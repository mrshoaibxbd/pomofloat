"""QSettings-backed application preferences and restorable timer state."""
from PySide6.QtCore import QSettings
from .timer import DEFAULT_DURATIONS


class Preferences:
    def __init__(self, settings=None):
        self.settings = settings or QSettings("Pomofloat", "Pomofloat")

    def load(self) -> dict:
        durations = {}
        for mode, seconds in DEFAULT_DURATIONS.items():
            default_minutes = seconds // 60
            minutes = self.settings.value(f"duration/{mode}", default_minutes, int)
            durations[mode] = max(1, int(minutes)) * 60
        return {
            "durations": durations,
            "sound": self.settings.value("notifications/sound", True, bool),
            "sound_style": self.settings.value(
                "notifications/sound_style", "double", str
            ),
            "notifications": self.settings.value("notifications/enabled", True, bool),
            "mini": self.settings.value("ui/mini", False, bool),
            "mini_opacity": self.settings.value("ui/mini_opacity", 110, int),
            "geometry": self.settings.value("ui/geometry", None),
            "cycle_length": max(1, self.settings.value("timer/cycle_length", 4, int)),
            "auto_start": self.settings.value("timer/auto_start", False, bool),
            "auto_start_break": self.settings.value(
                "timer/auto_start_break", False, bool
            ),
            "timer": self._load_timer(),
        }

    def _load_timer(self):
        return {
            "mode": self.settings.value("timer/mode", "work", str),
            "remaining": self.settings.value("timer/remaining", None, float),
            "completed_sessions": max(0, self.settings.value("timer/completed", 0, int)),
            "running": self.settings.value("timer/running", False, bool),
        }

    def save(self, values: dict):
        for mode, seconds in values.get("durations", {}).items():
            self.settings.setValue(f"duration/{mode}", max(1, int(seconds // 60)))
        self.settings.setValue("notifications/sound", bool(values.get("sound", True)))
        self.settings.setValue(
            "notifications/sound_style",
            values.get("sound_style", "double"),
        )
        self.settings.setValue("notifications/enabled", bool(values.get("notifications", True)))
        self.settings.setValue("ui/mini", bool(values.get("mini", False)))
        self.settings.setValue(
            "ui/mini_opacity",
            min(255, max(20, int(values.get("mini_opacity", 110)))),
        )
        self.settings.setValue("timer/cycle_length", max(1, int(values.get("cycle_length", 4))))
        self.settings.setValue("timer/auto_start", bool(values.get("auto_start", False)))
        self.settings.setValue(
            "timer/auto_start_break",
            bool(values.get("auto_start_break", False)),
        )
        timer = values.get("timer")
        if timer:
            self.settings.setValue("timer/mode", timer["mode"])
            self.settings.setValue("timer/remaining", float(timer["remaining"]))
            self.settings.setValue("timer/completed", int(timer["completed_sessions"]))
            self.settings.setValue("timer/running", bool(timer["running"]))
        if values.get("geometry") is not None:
            self.settings.setValue("ui/geometry", values["geometry"])
        self.settings.sync()
