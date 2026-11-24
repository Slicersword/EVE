"""M09 - two TTP223 touch pads on the Pi: head (BCM27) and back (BCM22), momentary, active high.
Head pat = happy. Back tap = wake / listen. Back hold = STOP."""
from __future__ import annotations


class TouchPads:
    def __init__(self, cfg, on_head, on_back_tap, on_back_hold, button_factory=None):
        t = cfg["touch"]
        self.enabled = t["enabled"] is True
        self.pins = (int(t["head_gpio"]), int(t["back_gpio"]))
        self.hold_s = float(t["hold_stop_s"])
        self.on_head, self.on_back_tap, self.on_back_hold = on_head, on_back_tap, on_back_hold
        self._factory = button_factory
        self._buttons = []
        self._held = False
        self.error = "not started"

    def start(self):
        if not self.enabled:
            self.error = "switched off in config"
            return
        try:
            factory = self._factory
            if factory is None:
                from gpiozero import Button
                factory = lambda pin, hold: Button(pin, pull_up=None, active_state=True, bounce_time=0.05, hold_time=hold)
            head, back = factory(self.pins[0], self.hold_s), factory(self.pins[1], self.hold_s)
            head.when_pressed = self.on_head
            back.when_held = self._back_held
            back.when_released = self._back_released
            self._buttons, self.error = [head, back], ""
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"[:120]

    def _back_held(self):
        self._held = True
        self.on_back_hold()

    def _back_released(self):
        if not self._held:
            self.on_back_tap()
        self._held = False

    def close(self):
        for button in self._buttons:
            try:
                button.close()
            except Exception:
                pass
        self._buttons = []
