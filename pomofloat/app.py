"""Pomofloat Qt application."""
import math
import os
import sys
import time
import argparse

# Set this before importing Qt. Explicit user configuration always wins.
if os.environ.get("XDG_SESSION_TYPE") == "wayland" and "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QMenu,
    QProgressBar, QPushButton, QMessageBox, QSystemTrayIcon,
    QVBoxLayout, QWidget,
)
from .notifications import notify, play_sound, sound_duration_ms
from .resources import logo_path
from .setup import SetupDialog
from .settings import Preferences
from .timer import TimerEngine
from . import __version__


class DragHandle(QWidget):
    def __init__(self, close_callback, mini_callback):
        super().__init__()
        self.mini_callback = mini_callback
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 0, 0)
        title = QLabel("POMOFLOAT")
        title.setObjectName("appTitle")
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(28, 28)
        self.close_button.clicked.connect(close_callback)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.close_button)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.window().windowHandle():
            self.window().windowHandle().startSystemMove()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mini_callback()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class Pomofloat(QWidget):
    def __init__(self):
        super().__init__()
        icon = QIcon(str(logo_path())) if logo_path() else QIcon()
        self.setWindowIcon(icon)
        self.setWindowTitle("Pomofloat")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.preferences = Preferences()
        values = self.preferences.load()
        timer_values = values["timer"]
        self.engine = TimerEngine(
            values["durations"], timer_values["mode"], timer_values["remaining"],
            timer_values["completed_sessions"], cycle_length=values["cycle_length"],
        )
        self.engine.running = False  # A monotonic deadline cannot span restarts.
        self.is_mini = values["mini"]
        self.notify_enabled = values["notifications"]
        self.sound_enabled = values["sound"]
        self.sound_style = values["sound_style"]
        self.auto_start = values["auto_start"]
        self.auto_start_break = values["auto_start_break"]
        self.mini_opacity = values["mini_opacity"]
        self._build_ui()
        self.clock = QTimer(self)
        self.clock.setInterval(200)
        self.clock.timeout.connect(self._tick)
        self._build_tray()
        self._build_shortcuts()
        self._refresh()
        self.resize(310, 245)
        if values["geometry"]:
            self.restoreGeometry(values["geometry"])
        if self.is_mini:
            self._set_mini(True)
        if self.auto_start and timer_values["running"]:
            self._start_pause()

    def _build_ui(self):
        self.panel = QWidget(self)
        self.panel.setObjectName("panel")
        self.effect = QGraphicsOpacityEffect(self.panel)
        self.panel.setGraphicsEffect(self.effect)
        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(17, 12, 17, 15)
        layout.setSpacing(9)
        self.header = DragHandle(self.close, self._toggle_mini)
        layout.addWidget(self.header)
        self.mode_label = QLabel()
        self.mode_label.setObjectName("modeLabel")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.mode_label)
        self.time_label = QLabel()
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        layout.addWidget(self.progress)
        self.status_label = QLabel("Ready to focus.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        self.sessions_label = QLabel()
        self.sessions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sessions_label)
        controls = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.reset_button = QPushButton("Reset")
        self.skip_button = QPushButton("Skip")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self._start_pause)
        self.reset_button.clicked.connect(self._reset)
        self.skip_button.clicked.connect(self._skip)
        for button in (self.start_button, self.reset_button, self.skip_button):
            button.setMinimumHeight(34)
            controls.addWidget(button)
        layout.addLayout(controls)
        self.optional_widgets = (
            self.mode_label, self.progress, self.status_label,
            self.sessions_label, self.start_button, self.reset_button,
            self.skip_button,
        )
        self.setStyleSheet("""
            QWidget { font-family: "Sans Serif"; color: #F4F5F8; }
            QWidget#panel { background: rgba(29,33,46,232); border: 1px solid rgba(255,255,255,35); border-radius: 17px; }
            QLabel#appTitle { color: #D7D9E3; font-size: 11px; font-weight: bold; letter-spacing: 2px; }
            QLabel#modeLabel { font-size: 11px; font-weight: bold; }
            QLabel#timeLabel { color: #FFF; font-size: 43px; font-weight: bold; }
            QPushButton { background: rgba(255,255,255,18); border: 1px solid rgba(255,255,255,24); border-radius: 8px; padding: 5px; }
            QPushButton#primaryButton { background: #FB7185; color: #23151C; font-weight: bold; border: none; }
            QPushButton#closeButton { background: transparent; border: none; color: #BFC4D4; font-size: 19px; }
            QProgressBar { background: rgba(255,255,255,20); border: none; border-radius: 3px; }
            QProgressBar::chunk { background: #FB7185; border-radius: 3px; }
        """)

    def _build_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.windowIcon())
        self.tray.setToolTip("Pomofloat")
        menu = QMenu()
        menu.addAction("Show / hide", self._toggle_visible)
        menu.addAction("Start / pause", self._start_pause)
        menu.addAction("Reset", self._reset)
        menu.addAction("Reset all sessions", self._reset_all)
        menu.addAction("Skip", self._skip)
        menu.addSeparator()
        menu.addAction("Setup…", self._setup)
        menu.addAction("Quit", self.close)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _build_shortcuts(self):
        for sequence, callback in (
            ("Ctrl+Space", self._start_pause),
            ("Ctrl+R", self._reset),
            ("Ctrl+M", self._toggle_mini),
            ("Ctrl+Q", self.close),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(callback)

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_visible()

    def _start_pause(self):
        if self.engine.running:
            self.engine.pause(time.monotonic())
            self.clock.stop()
            self.status_label.setText("Timer paused.")
        else:
            self.engine.start(time.monotonic())
            self.clock.start()
            self.status_label.setText("Time to focus." if self.engine.mode == "work" else "Enjoy your break.")
        self._refresh()

    def _tick(self):
        was_work = self.engine.mode == "work"
        if self.engine.update(time.monotonic()):
            self.clock.stop()
            message = "Focus complete! Time for a break." if self.engine.mode != "work" else "Break complete! Ready to focus?"
            self.status_label.setText(message)
            if self.notify_enabled:
                notify(
                    "Pomofloat",
                    message,
                    self.sound_enabled,
                    self.sound_style,
                    self.tray,
                )
            elif self.sound_enabled:
                play_sound(self.sound_style)
            if was_work and self.auto_start_break:
                QTimer.singleShot(
                    sound_duration_ms(self.sound_style)
                    if self.sound_enabled
                    else 0,
                    self._start_break,
                )
        self._refresh()

    def _start_break(self):
        if self.engine.mode != "work" and not self.engine.running:
            self.engine.start(time.monotonic())
            self.clock.start()
            self._refresh()

    def _reset(self):
        self.engine.reset()
        self.clock.stop()
        self.status_label.setText("Timer reset.")
        self._refresh()

    def _reset_all(self):
        self.engine.completed_sessions = 0
        self.engine.reset()
        self.clock.stop()
        self.status_label.setText("All session data reset.")
        self._save_state()
        self._refresh()

    def _skip(self):
        self.engine.skip()
        self.clock.stop()
        self.status_label.setText("Phase skipped.")
        self._refresh()

    def _refresh(self):
        seconds = max(0, math.ceil(self.engine.remaining))
        minutes, seconds = divmod(seconds, 60)
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")
        names = {"work": "FOCUS", "short": "SHORT BREAK", "long": "LONG BREAK"}
        colors = {"work": "#FB7185", "short": "#34D399", "long": "#60A5FA"}
        self.mode_label.setText(names[self.engine.mode])
        self.mode_label.setStyleSheet(f"color:{colors[self.engine.mode]}")
        self.progress.setRange(0, self.engine.duration)
        self.progress.setValue(max(0, int(self.engine.duration - self.engine.remaining)))
        self.sessions_label.setText(f"{self.engine.completed_sessions} sessions completed")
        self.start_button.setText("Pause" if self.engine.running else ("Resume" if self.engine.remaining < self.engine.duration else "Start"))

    def _set_mini(self, enabled):
        self.is_mini = enabled
        background_alpha = self.mini_opacity if enabled else 232
        self.panel.setStyleSheet(
            "QWidget#panel {"
            f"background: rgba(29,33,46,{background_alpha});"
            "border: 1px solid rgba(255,255,255,35);"
            "border-radius: 17px;"
            "}"
        )
        for widget in self.optional_widgets:
            widget.setVisible(not enabled)
        self.header.close_button.setVisible(not enabled)
        self.resize(175, 90) if enabled else self.resize(310, 245)

    def _toggle_mini(self):
        self._set_mini(not self.is_mini)
        self._refresh()

    def _toggle_visible(self):
        self.setVisible(not self.isVisible())

    def _setup(self):
        values = self.preferences.load()
        values.update({
            "durations": self.engine.durations,
            "notifications": self.notify_enabled,
            "sound": self.sound_enabled,
            "sound_style": self.sound_style,
            "cycle_length": self.engine.cycle_length,
            "auto_start": self.auto_start,
            "auto_start_break": self.auto_start_break,
            "mini_opacity": self.mini_opacity,
        })
        dialog = SetupDialog(values, self)
        if dialog.exec():
            changed = dialog.values()
            if dialog.reset_all:
                answer = QMessageBox.question(
                    self,
                    "Reset all session data",
                    "Clear the completed-session count and reset the current phase?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer == QMessageBox.StandardButton.Yes:
                    self._reset_all()
                return
            self.engine.durations = changed["durations"]
            self.engine.cycle_length = changed["cycle_length"]
            self.notify_enabled = changed["notifications"]
            self.sound_enabled = changed["sound"]
            self.sound_style = changed["sound_style"]
            self.auto_start = changed["auto_start"]
            self.auto_start_break = changed["auto_start_break"]
            self.mini_opacity = changed["mini_opacity"]
            self.engine.reset()
            self.preferences.save({
                **changed,
                "mini": self.is_mini,
                "timer": {
                    "mode": self.engine.mode,
                    "remaining": self.engine.remaining,
                    "completed_sessions": self.engine.completed_sessions,
                    "running": False,
                },
            })
            self._set_mini(self.is_mini)
            self._refresh()

    def _save_state(self):
        self.preferences.save({
            "durations": self.engine.durations,
            "notifications": self.notify_enabled,
            "sound": self.sound_enabled,
            "sound_style": self.sound_style,
            "mini": self.is_mini,
            "mini_opacity": self.mini_opacity,
            "cycle_length": self.engine.cycle_length,
            "auto_start": self.auto_start,
            "auto_start_break": self.auto_start_break,
            "timer": {
                "mode": self.engine.mode,
                "remaining": self.engine.remaining,
                "completed_sessions": self.engine.completed_sessions,
                "running": False,
            },
        })

    def resizeEvent(self, event):
        self.panel.setGeometry(self.rect())
        super().resizeEvent(event)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and (self.isFullScreen() or self.isMaximized()):
            QTimer.singleShot(0, self.showNormal)

    def closeEvent(self, event):
        self.preferences.save({
            "durations": self.engine.durations, "notifications": self.notify_enabled,
            "sound": self.sound_enabled, "mini": self.is_mini,
            "sound_style": self.sound_style,
            "mini_opacity": self.mini_opacity,
            "cycle_length": self.engine.cycle_length, "auto_start": self.auto_start,
            "auto_start_break": self.auto_start_break,
            "timer": {"mode": self.engine.mode, "remaining": self.engine.remaining,
                      "completed_sessions": self.engine.completed_sessions,
                      "running": self.engine.running},
            "geometry": self.saveGeometry(),
        })
        self.tray.hide()
        super().closeEvent(event)


def main():
    parser = argparse.ArgumentParser(
        prog="pomofloat",
        description="A lightweight, always-on-top Pomodoro timer.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    _, qt_args = parser.parse_known_args()
    # QApplication must not be constructed for informational CLI commands.
    # Keep Qt's arguments available for normal GUI startup.
    sys.argv = [sys.argv[0], *qt_args]
    app = QApplication(sys.argv)
    app.setApplicationName("Pomofloat")
    icon_path = logo_path()
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))
    window = Pomofloat()
    window.show()
    window.raise_()
    sys.exit(app.exec())
