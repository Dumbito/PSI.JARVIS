"""Hand-drawn vector icons for the sidebar navigation.

Each icon is a small set of QPainterPath primitives (no external icon
font, no bundled image assets, nothing fetched at build time) so the
app's visual identity stays fully self-contained and reproducible,
matching the project's determinism principles. Icons are rendered at
paint time with the caller's color, so the same path data serves the
active and inactive nav states without needing separate pixmaps.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPainterPath, QPen, QPixmap


def _stroke(painter: QPainter, color: str, width: float = 1.6) -> None:
    pen = QPen(color)
    pen.setWidthF(width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)


def _home(p: QPainter, r: QRectF) -> None:
    path = QPainterPath()
    path.moveTo(r.left(), r.center().y())
    path.lineTo(r.center().x(), r.top())
    path.lineTo(r.right(), r.center().y())
    p.drawPath(path)
    p.drawLine(
        QPointF(r.left() + r.width() * 0.15, r.center().y() - 1),
        QPointF(r.left() + r.width() * 0.15, r.bottom()),
    )
    p.drawLine(
        QPointF(r.right() - r.width() * 0.15, r.center().y() - 1),
        QPointF(r.right() - r.width() * 0.15, r.bottom()),
    )
    p.drawLine(
        QPointF(r.left() + r.width() * 0.15, r.bottom()),
        QPointF(r.right() - r.width() * 0.15, r.bottom()),
    )
    p.drawLine(
        QPointF(r.center().x() - r.width() * 0.12, r.bottom()),
        QPointF(r.center().x() - r.width() * 0.12, r.bottom() - r.height() * 0.32),
    )
    p.drawLine(
        QPointF(r.center().x() + r.width() * 0.12, r.bottom()),
        QPointF(r.center().x() + r.width() * 0.12, r.bottom() - r.height() * 0.32),
    )
    p.drawLine(
        QPointF(r.center().x() - r.width() * 0.12, r.bottom() - r.height() * 0.32),
        QPointF(r.center().x() + r.width() * 0.12, r.bottom() - r.height() * 0.32),
    )


def _folder(p: QPainter, r: QRectF) -> None:
    top = r.top() + r.height() * 0.18
    path = QPainterPath()
    path.moveTo(r.left(), r.bottom())
    path.lineTo(r.left(), top + r.height() * 0.08)
    path.lineTo(r.left() + r.width() * 0.32, top + r.height() * 0.08)
    path.lineTo(r.left() + r.width() * 0.42, top)
    path.lineTo(r.right(), top)
    path.lineTo(r.right(), r.bottom())
    path.lineTo(r.left(), r.bottom())
    p.drawPath(path)


def _document(p: QPainter, r: QRectF) -> None:
    inset = r.adjusted(r.width() * 0.14, 0, -r.width() * 0.14, 0)
    path = QPainterPath()
    path.moveTo(inset.left(), inset.top())
    path.lineTo(inset.right() - inset.width() * 0.28, inset.top())
    path.lineTo(inset.right(), inset.top() + inset.height() * 0.22)
    path.lineTo(inset.right(), inset.bottom())
    path.lineTo(inset.left(), inset.bottom())
    path.closeSubpath()
    p.drawPath(path)
    for frac in (0.42, 0.6, 0.78):
        y = inset.top() + inset.height() * frac
        p.drawLine(
            QPointF(inset.left() + inset.width() * 0.16, y),
            QPointF(inset.right() - inset.width() * 0.16, y),
        )


def _shuffle(p: QPainter, r: QRectF) -> None:
    top_y = r.top() + r.height() * 0.3
    bot_y = r.bottom() - r.height() * 0.3
    p.drawLine(QPointF(r.left(), top_y), QPointF(r.right() - r.width() * 0.18, top_y))
    p.drawLine(QPointF(r.left(), bot_y), QPointF(r.right() - r.width() * 0.18, bot_y))
    for y in (top_y, bot_y):
        arrow = QPainterPath()
        arrow.moveTo(r.right() - r.width() * 0.3, y - r.height() * 0.14)
        arrow.lineTo(r.right(), y)
        arrow.lineTo(r.right() - r.width() * 0.3, y + r.height() * 0.14)
        p.drawPath(arrow)


def _check(p: QPainter, r: QRectF) -> None:
    box = r.adjusted(
        r.width() * 0.05, r.height() * 0.05, -r.width() * 0.05, -r.height() * 0.05
    )
    p.drawRoundedRect(box, 3, 3)
    path = QPainterPath()
    path.moveTo(box.left() + box.width() * 0.24, box.center().y())
    path.lineTo(box.left() + box.width() * 0.44, box.bottom() - box.height() * 0.28)
    path.lineTo(box.right() - box.width() * 0.2, box.top() + box.height() * 0.26)
    p.drawPath(path)


def _grid(p: QPainter, r: QRectF) -> None:
    gap = r.width() * 0.12
    half_w = (r.width() - gap) / 2
    half_h = (r.height() - gap) / 2
    for dx in (0, half_w + gap):
        for dy in (0, half_h + gap):
            p.drawRoundedRect(QRectF(r.left() + dx, r.top() + dy, half_w, half_h), 2, 2)


def _bars(p: QPainter, r: QRectF) -> None:
    base = r.bottom()
    widths = r.width() * 0.18
    heights = (0.4, 0.75, 0.55, 0.95)
    gap = (r.width() - widths * len(heights)) / (len(heights) - 1)
    x = r.left()
    for h in heights:
        rect = QRectF(x, base - r.height() * h, widths, r.height() * h)
        p.drawRoundedRect(rect, 1.5, 1.5)
        x += widths + gap


def _audit(p: QPainter, r: QRectF) -> None:
    c = QPointF(r.center().x() - r.width() * 0.08, r.center().y() - r.height() * 0.08)
    radius = r.width() * 0.32
    p.drawEllipse(c, radius, radius)
    handle_start = QPointF(c.x() + radius * 0.7, c.y() + radius * 0.7)
    p.drawLine(handle_start, QPointF(r.right(), r.bottom()))


def _gear(p: QPainter, r: QRectF) -> None:
    c = r.center()
    outer = r.width() * 0.42
    inner = r.width() * 0.18
    p.drawEllipse(c, inner, inner)
    for i in range(8):
        import math

        angle = math.pi * 2 * i / 8
        x1 = c.x() + math.cos(angle) * outer * 0.72
        y1 = c.y() + math.sin(angle) * outer * 0.72
        x2 = c.x() + math.cos(angle) * outer
        y2 = c.y() + math.sin(angle) * outer
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    p.drawEllipse(c, outer * 0.72, outer * 0.72)


ICON_PAINTERS: dict[str, Callable[[QPainter, QRectF], None]] = {
    "Dashboard": _home,
    "Projects": _folder,
    "Papers": _document,
    "Sources": _shuffle,
    "Screening": _check,
    "Analysis": _grid,
    "Reports": _bars,
    "Audit": _audit,
    "Settings": _gear,
}


def nav_icon(label: str, color: str, size: int = 18) -> QIcon:
    """Render a small line-icon for ``label`` tinted with ``color``."""
    painter_fn = ICON_PAINTERS.get(label)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    if painter_fn is None:
        return QIcon(pixmap)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    _stroke(painter, color)
    margin = size * 0.08
    rect = QRectF(margin, margin, size - margin * 2, size - margin * 2)
    painter_fn(painter, rect)
    painter.end()
    return QIcon(pixmap)
