"""Best-effort desktop notifications and completion sound."""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication


def sound_duration_ms(style: str) -> int:
    return {"system": 0, "double": 140, "triple": 280}.get(style, 140)


def play_sound(style: str) -> None:
    """Play a small dependency-free sound pattern using the desktop beep."""
    intervals = {"system": (), "double": (140,), "triple": (140, 280)}
    QApplication.beep()
    for delay in intervals.get(style, intervals["double"]):
        QTimer.singleShot(delay, QApplication.beep)


def notify(
    title: str,
    message: str,
    sound: bool = True,
    sound_style: str = "double",
    tray=None,
):
    """Show a tray notification with an optional selectable beep pattern."""
    if sound:
        play_sound(sound_style)
    if tray is not None:
        try:
            tray.showMessage(title, message)
        except Exception:
            pass
