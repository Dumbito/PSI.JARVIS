"""A small animated ring/donut progress indicator.

Used on the dashboard in place of a flat progress bar for a more
distinctive, premium look. The ring animates smoothly to its target
value using a Qt property animation, and falls back to a plain empty
ring (no misleading full circle) when there is no data yet.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class ProgressRing(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fraction = 0.0
        self._target = 0.0
        self._track_color = QColor("#1c2c40")
        self._fill_color = QColor("#3a96f4")
        self._text_color = QColor("#eef6ff")
        self.setMinimumSize(96, 96)
        self._animation = QPropertyAnimation(self, b"fraction", self)
        self._animation.setDuration(700)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

    def set_value(self, numerator: int, denominator: int) -> None:
        self._target = 0.0 if denominator <= 0 else min(1.0, numerator / denominator)
        self._animation.stop()
        self._animation.setStartValue(self._fraction)
        self._animation.setEndValue(self._target)
        self._animation.start()

    def get_fraction(self) -> float:
        return self._fraction

    def set_fraction(self, value: float) -> None:
        self._fraction = value
        self.update()

    fraction = Property(float, get_fraction, set_fraction)

    def paintEvent(self, event) -> None:
        del event
        side = min(self.width(), self.height())
        margin = side * 0.08
        rect = QRectF(margin, margin, side - margin * 2, side - margin * 2)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        track_pen = QPen(self._track_color)
        track_pen.setWidthF(side * 0.1)
        track_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)

        if self._fraction > 0:
            fill_pen = QPen(self._fill_color)
            fill_pen.setWidthF(side * 0.1)
            fill_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(fill_pen)
            span = int(360 * 16 * self._fraction)
            painter.drawArc(rect, 90 * 16, -span)

        painter.setPen(self._text_color)
        font = painter.font()
        font.setBold(True)
        font.setPointSizeF(side * 0.16)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, f"{round(self._fraction * 100)}%")
        painter.end()
