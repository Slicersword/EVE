"""M13 - voice. Speaking: espeak-ng (English, Hindi, Marathi). Hearing: arecord -> simple loudness-based
speech detection -> whisper.cpp on the Pi. Audio stays in RAM: the short clip handed to whisper lives in
/dev/shm and is deleted straight after. While EVE speaks the microphone input is thrown away, so she does
not hear herself."""
from __future__ import annotations
import array, os, queue, subprocess, tempfile, threading, wave

VOICES = {"en": "en", "hi": "hi", "mr": "mr"}


def clean_speech(text, limit=300) -> str:
    text = " ".join("".join(ch if ch.isprintable() else " " for ch in str(text)).split())
    return text[:limit]


class Speaker:
    def __init__(self, cfg, run=subprocess.run):
        v = cfg["voice"]
        self.enabled, self.command, self.speed = v["tts_enabled"] is True, v["tts_command"], int(v["tts_speed"])
        self._run = run
        self._queue: queue.Queue = queue.Queue(maxsize=5)
        self.speaking = False
        self.last_error = ""
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="eve3-speaker", daemon=True)
        self._thread.start()

    def say(self, text, lang="en") -> bool:
        text = clean_speech(text)
        if not self.enabled or not text:
            return False
        try:
            self._queue.put_nowait((text, VOICES.get(lang, "en")))
            return True
        except queue.Full:
            return False                                # drop rather than fall behind

    def speak_now(self, text, voice):
        self.speaking = True
        try:
            # list arguments + "--": the text can never be read as an option or a shell command
            self._run([self.command, "-v", voice, "-s", str(self.speed), "--", text],
                      timeout=30, check=False, capture_output=True)
            self.last_error = ""
        except Exception as exc:
            self.last_error = type(exc).__name__
        finally:
            self.speaking = False

    def _loop(self):
        while not self._stop.is_set():
            try:
                text, voice = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            self.speak_now(text, voice)

    def stop(self):
        self._stop.set()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break


def rms(pcm: bytes) -> float:
    samples = array.array("h")
    samples.frombytes(pcm[:len(pcm) // 2 * 2])
    if not samples:
        return 0.0
    return (sum(s * s for s in samples) / len(samples)) ** 0.5


class Segmenter:
    """Cuts a stream of 16-bit mono chunks into utterances: starts on a loud chunk, ends after a pause."""

    def __init__(self, threshold=500.0, chunk_s=0.1, silence_s=0.7, max_s=8.0, min_s=0.3, pre_chunks=2):
        self.threshold = float(threshold)
        self.silence_chunks = max(1, round(silence_s / chunk_s))
        self.max_chunks, self.min_chunks, self.pre_chunks = round(max_s / chunk_s), round(min_s / chunk_s), pre_chunks
        self.reset()

    def reset(self):
        self._pre, self._buf, self._quiet, self._loud = [], [], 0, 0

    def feed(self, chunk: bytes) -> bytes | None:
        loud = rms(chunk) >= self.threshold
        if not self._buf:
            if not loud:
                self._pre = (self._pre + [chunk])[-self.pre_chunks:]
                return None
            self._buf, self._pre, self._quiet, self._loud = self._pre + [chunk], [], 0, 1
            return None
        self._buf.append(chunk)
        self._loud += loud
        self._quiet = 0 if loud else self._quiet + 1
        if self._quiet >= self.silence_chunks or len(self._buf) >= self.max_chunks:
            out, loud_count = b"".join(self._buf), self._loud
            self.reset()
            return out if loud_count >= self.min_chunks else None    # a click or bump is not speech
        return None


def transcribe(cfg, pcm: bytes, run=subprocess.run, shm="/dev/shm") -> str:
    """whisper.cpp on a clip that exists only in RAM-backed /dev/shm and is removed afterwards."""
    v = cfg["voice"]
    root = cfg["_root"]
    if not os.path.isdir(shm):
        raise RuntimeError("RAM audio directory unavailable; refusing to write microphone audio to disk")
    fd, path = tempfile.mkstemp(suffix=".wav", prefix="eve-", dir=shm)
    try:
        with os.fdopen(fd, "wb") as handle, wave.open(handle, "wb") as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(int(v["sample_rate"])); wav.writeframes(pcm)
        result = run([os.path.join(root, v["stt_command"]), "-m", os.path.join(root, v["stt_model"]), "-f", path,
                      "-l", str(v["stt_language"]), "-nt", "-np", "-t", "3"],
                     capture_output=True, text=True, timeout=v["stt_timeout_s"], check=False)
        text = " ".join(result.stdout.split())
        return "" if text.startswith(("[", "(")) else text[:400]         # "[BLANK_AUDIO]", "(music)" etc.
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


class Listener:
    """Microphone thread. Calls on_text(text) for each understood utterance."""

    def __init__(self, cfg, on_text, is_speaking, popen=subprocess.Popen, transcriber=transcribe):
        self.cfg, self.on_text, self.is_speaking = cfg, on_text, is_speaking
        self._popen, self._transcribe = popen, transcriber
        v = cfg["voice"]
        self.rate = int(v["sample_rate"])
        self.chunk_bytes = self.rate // 10 * 2
        self.segmenter = Segmenter(v["vad_rms"], 0.1, v["silence_s"], v["max_utterance_s"])
        self.listening = False
        self.last_error = ""
        self.level = 0.0
        self._stop = threading.Event()
        self._thread = None
        self._proc = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="eve3-listener", daemon=True)
        self._thread.start()

    def _loop(self):
        v = self.cfg["voice"]
        while not self._stop.is_set():
            try:
                self._proc = self._popen(["arecord", "-q", "-D", str(v["capture_device"]), "-f", "S16_LE", "-r", str(self.rate),
                                          "-c", "1", "-t", "raw"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                self.listening, self.last_error = True, ""
                while not self._stop.is_set():
                    chunk = self._proc.stdout.read(self.chunk_bytes)
                    if not chunk:
                        raise IOError("microphone stream ended")
                    self.handle_chunk(chunk)
            except Exception as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"[:120]
            finally:
                self.listening = False
                self._kill()
            self._stop.wait(5)                           # retry later; never spin

    def handle_chunk(self, chunk: bytes):
        if self.is_speaking():
            self.segmenter.reset()                       # half-duplex: ignore the robot's own voice
            return
        self.level = rms(chunk)
        utterance = self.segmenter.feed(chunk)
        if utterance:
            text = self._transcribe(self.cfg, utterance)
            if text:
                self.on_text(text)

    def _kill(self):
        proc, self._proc = self._proc, None
        if proc is not None:
            try:
                proc.kill()
                proc.wait(timeout=2)
            except Exception:
                pass

    def stop(self):
        self._stop.set()
        self._kill()
