from PySide6.QtCore import QSettings
from pomofloat.settings import Preferences
from pomofloat.resources import logo_path


def test_preferences_round_trip():
    settings = QSettings()
    settings.clear()
    preferences = Preferences(settings)
    preferences.save({
        "durations": {"work": 120, "short": 60, "long": 180},
        "cycle_length": 3,
        "auto_start": True,
        "auto_start_break": True,
        "sound_style": "triple",
        "timer": {
            "mode": "short", "remaining": 42.5,
            "completed_sessions": 2, "running": False,
        },
    })
    loaded = preferences.load()
    assert loaded["durations"]["work"] == 120
    assert loaded["cycle_length"] == 3
    assert loaded["auto_start"] is True
    assert loaded["auto_start_break"] is True
    assert loaded["sound_style"] == "triple"
    assert loaded["timer"]["mode"] == "short"
    assert loaded["timer"]["remaining"] == 42.5
    settings.clear()


def test_logo_path_points_to_project_asset():
    assert logo_path() is not None
    assert logo_path().name == "pomofloat.png"
