from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class Toast(QFrame):
    """Small non-modal notification that never uses a graphics effect."""

    def __init__(self, parent: QWidget, message: str, duration_ms: int = 2400) -> None:
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setStyleSheet(
            "QFrame#toast { background: #13253a; border: 1px solid #3a5d7d; border-radius: 8px; }"
            "QFrame#toast QLabel { background: transparent; color: #eaf2fb; padding: 1px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.adjustSize()
        self._position(parent)
        QTimer.singleShot(max(500, duration_ms), self.close)

    def _position(self, parent: QWidget) -> None:
        margin = 24
        x = max(margin, parent.width() - self.width() - margin)
        y = max(margin, parent.height() - self.height() - margin)
        self.move(x, y)

    @classmethod
    def show_message(cls, parent: QWidget, message: str, duration_ms: int = 2400) -> "Toast":
        window = parent.window()
        toast = cls(window, message, duration_ms)
        toast.show()
        toast.raise_()
        return toast
