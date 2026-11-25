"""M10 - camera. Finds a face in the picture and reports only where it is (left/right, up/down).
Pictures stay in RAM, are never saved and never leave the Pi. The LED (BCM25) is on whenever the
camera is running; the physical shutter is the real privacy barrier."""
from __future__ import annotations
import threading, time


def face_offset(faces, width, height):
    """faces = [(x, y, w, h), ...] -> (dx, dy) of the biggest face, each -1..1 (0 = centre), or None."""
    faces = [f for f in faces if len(f) == 4 and f[2] > 0 and f[3] > 0]
    if not faces or width <= 0 or height <= 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    dx = ((x + w / 2) / width) * 2 - 1
    dy = ((y + h / 2) / height) * 2 - 1
    return max(-1.0, min(1.0, dx)), max(-1.0, min(1.0, dy))


def tracking_step(offset, deadband=0.12, step=8, pan_sign=1, tilt_sign=1):
    """Small head correction towards the face; (0, 0) inside the dead band or when no face."""
    if offset is None:
        return 0, 0
    dx, dy = offset
    dpan = 0 if abs(dx) < deadband else int(step * pan_sign * (1 if dx > 0 else -1))
    dtilt = 0 if abs(dy) < deadband else int(step * tilt_sign * (1 if dy > 0 else -1))
    return dpan, dtilt


class Camera:
    def __init__(self, cfg, on_face=None):
        self.c = cfg["camera"]
        self.on_face = on_face
        self.offset = None
        self.offset_at = 0.0
        self.running = False
        self.error = "off"
        self._stop = threading.Event()
        self._paused = threading.Event()
        self._thread = None

    def start(self):
        if self.c["enabled"] is not True or (self._thread and self._thread.is_alive()):
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="eve3-camera", daemon=True)
        self._thread.start()

    def _loop(self):
        while not self._stop.is_set():
            if self._paused.is_set():
                self._stop.wait(0.1)
                continue
            self._capture()
            if self.error:
                return

    def _capture(self):
        cam = led = None
        try:
            import cv2
            from picamera2 import Picamera2
            from gpiozero import LED
            cascade = cv2.CascadeClassifier(self.c["cascade_path"])
            if cascade.empty():
                raise RuntimeError("face model file not found")
            led = LED(int(self.c["led_gpio"]))
            led.on()                                                    # LED before the first frame
            width, height = int(self.c["width"]), int(self.c["height"])
            cam = Picamera2()
            cam.configure(cam.create_preview_configuration(main={"size": (width, height), "format": "RGB888"}))
            cam.start()
            self.running, self.error = True, ""
            period = 1.0 / max(1, int(self.c["process_fps"]))
            while not self._stop.wait(period) and not self._paused.is_set():
                gray = cv2.cvtColor(cam.capture_array(), cv2.COLOR_RGB2GRAY)
                faces = cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(48, 48))
                self.offset, self.offset_at = face_offset([tuple(int(v) for v in f) for f in faces], width, height), time.monotonic()
                if self.on_face:
                    self.on_face(self.offset)
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"[:120]
        finally:
            self.offset = None
            for closer in (lambda: cam and cam.stop(), lambda: cam and cam.close(), lambda: led and led.off(),
                           lambda: led and led.close()):
                try:
                    closer()
                except Exception:
                    pass
            self.running = False

    def face_present(self, max_age_s=1.5) -> bool:
        return (not self._paused.is_set() and self.running and self.offset is not None
                and time.monotonic() - self.offset_at < max_age_s)

    def set_paused(self, paused):
        if paused:
            self._paused.set()
        else:
            self._paused.clear()

    @property
    def state(self):
        if self.c["enabled"] and self._paused.is_set() and not self.running:
            return "paused for sleep"
        return "on" if self.running else self.error

    def stop(self):
        self._stop.set()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=3)
