from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SetupDialog(QDialog):
    def __init__(self, values, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pomofloat Setup")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(430, 560)
        self.reset_all = False
        self._drag_position = None

        panel = QWidget(self)
        panel.setObjectName("setupPanel")
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(panel)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 15, 20, 18)
        panel_layout.setSpacing(14)

        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 0, 0)
        title = QLabel("POMOFLOAT  /  SETUP")
        title.setObjectName("setupTitle")
        header.addWidget(title)
        header.addStretch()

        close_button = QPushButton("×")
        close_button.setObjectName("setupCloseButton")
        close_button.setFixedSize(28, 28)
        close_button.setToolTip("Save and close setup")
        close_button.clicked.connect(self.accept)
        header.addWidget(close_button)
        panel_layout.addLayout(header)

        subtitle = QLabel("Shape your focus rhythm and desktop experience.")
        subtitle.setObjectName("setupSubtitle")
        panel_layout.addWidget(subtitle)

        content = QWidget()
        form = QFormLayout(content)
        form.setContentsMargins(0, 3, 0, 0)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(13)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.spins = {}
        for key, label in (
            ("work", "Focus duration"),
            ("short", "Short break"),
            ("long", "Long break"),
        ):
            spin = QSpinBox()
            spin.setRange(1, 180)
            spin.setSuffix(" min")
            spin.setValue(max(1, int(values["durations"][key] // 60)))
            self.spins[key] = spin
            form.addRow(label, spin)

        self.cycle = QSpinBox()
        self.cycle.setRange(1, 12)
        self.cycle.setSuffix(" sessions")
        self.cycle.setValue(values.get("cycle_length", 4))
        form.addRow("Long break after", self.cycle)

        self.opacity = QSpinBox()
        self.opacity.setRange(20, 255)
        self.opacity.setSuffix(" / 255")
        self.opacity.setValue(values.get("mini_opacity", 110))
        form.addRow("Mini mode opacity", self.opacity)

        self.notifications = QCheckBox("Show completion notifications")
        self.notifications.setChecked(values.get("notifications", True))
        form.addRow(self.notifications)

        self.sound = QCheckBox("Play a completion sound")
        self.sound.setChecked(values.get("sound", True))
        form.addRow(self.sound)

        self.sound_style = QComboBox()
        for key, label in (
            ("system", "System beep"),
            ("double", "Double beep"),
            ("triple", "Triple beep"),
        ):
            self.sound_style.addItem(label, key)
        index = self.sound_style.findData(values.get("sound_style", "double"))
        self.sound_style.setCurrentIndex(max(0, index))
        form.addRow("Sound pattern", self.sound_style)

        self.auto_start = QCheckBox("Automatically resume a saved timer")
        self.auto_start.setChecked(values.get("auto_start", False))
        form.addRow(self.auto_start)

        self.auto_start_break = QCheckBox(
            "Start the break automatically after focus completes"
        )
        self.auto_start_break.setChecked(values.get("auto_start_break", False))
        form.addRow(self.auto_start_break)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(content)
        panel_layout.addWidget(scroll, 1)

        reset_row = QHBoxLayout()
        reset_row.addStretch()
        self.reset_all_button = QPushButton("Reset all session data")
        self.reset_all_button.setObjectName("resetButton")
        self.reset_all_button.clicked.connect(self._request_reset_all)
        reset_row.addWidget(self.reset_all_button)
        panel_layout.addLayout(reset_row)

        self.setStyleSheet("""
            QWidget {
                color: #F4F5F8;
                font-family: "Sans Serif";
                font-size: 11px;
            }

            QWidget#setupPanel {
                background-color: rgba(29, 33, 46, 248);
                border: 1px solid rgba(255, 255, 255, 35);
                border-radius: 17px;
            }

            QLabel#setupTitle {
                color: #D7D9E3;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 2px;
            }

            QLabel#setupSubtitle {
                color: #A9AFC2;
                font-size: 11px;
                padding-bottom: 2px;
            }

            QFormLayout QLabel {
                color: #D7D9E3;
            }

            QSpinBox, QComboBox {
                min-height: 28px;
                padding: 2px 8px;
                background-color: rgba(255, 255, 255, 18);
                border: 1px solid rgba(255, 255, 255, 24);
                border-radius: 7px;
            }

            QComboBox QAbstractItemView {
                background-color: #252A3A;
                color: #F4F5F8;
                selection-background-color: #FB7185;
            }

            QCheckBox {
                spacing: 8px;
                color: #D7D9E3;
            }

            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }

            QPushButton#setupCloseButton {
                background-color: transparent;
                border: none;
                color: #BFC4D4;
                font-size: 19px;
                padding: 0;
            }

            QPushButton#setupCloseButton:hover {
                background-color: rgba(239, 68, 68, 100);
                color: white;
                border-radius: 7px;
            }

            QPushButton#resetButton {
                color: #FDA4AF;
                background-color: transparent;
                border: 1px solid rgba(251, 113, 133, 100);
                border-radius: 7px;
                padding: 6px 10px;
            }

            QPushButton#resetButton:hover {
                background-color: rgba(251, 113, 133, 35);
            }
        """)

    def _request_reset_all(self):
        self.reset_all = True
        self.accept()

    def values(self):
        return {
            "durations": {
                key: spin.value() * 60
                for key, spin in self.spins.items()
            },
            "notifications": self.notifications.isChecked(),
            "sound": self.sound.isChecked(),
            "sound_style": self.sound_style.currentData(),
            "cycle_length": self.cycle.value(),
            "auto_start": self.auto_start.isChecked(),
            "auto_start_break": self.auto_start_break.isChecked(),
            "mini_opacity": self.opacity.value(),
        }

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_position is not None:
            offset = event.globalPosition().toPoint() - self._drag_position
            self.move(self.pos() + offset)
            self._drag_position = event.globalPosition().toPoint()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_position = None
        super().mouseReleaseEvent(event)

    def closeEvent(self, event):
        self.accept()
        event.accept()
