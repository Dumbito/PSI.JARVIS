from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from psi_jarvis.gui.data import GuiDataService
from psi_jarvis.gui.prisma import GuiPrismaService


class PrismaStageCard(QFrame):
    """Compact read-only PRISMA stage card."""

    def __init__(self, title: str, value: int, detail: str, enabled: bool = True) -> None:
        super().__init__()
        self.setObjectName("prismaStage")
        self.setProperty("enabledStage", enabled)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(3)
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        heading.setWordWrap(True)
        layout.addWidget(heading)
        count = QLabel(f"{value:,}")
        count.setObjectName("metricValue")
        layout.addWidget(count)
        label = QLabel(detail)
        label.setObjectName("pageSubtitle")
        label.setWordWrap(True)
        layout.addWidget(label)


class PrismaDiagram(QWidget):
    """PRISMA-style flow diagram for stages actually persisted by PSI.JARVIS."""

    def __init__(self, data: GuiDataService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data
        self.service = GuiPrismaService(data)
        self._flow = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 4)
        root.setSpacing(8)
        self.stage_row = QHBoxLayout()
        self.stage_row.setSpacing(8)
        root.addLayout(self.stage_row)
        self.note = QLabel()
        self.note.setObjectName("pageSubtitle")
        self.note.setWordWrap(True)
        root.addWidget(self.note)
        self.refresh()

    def _clear(self) -> None:
        while self.stage_row.count():
            item = self.stage_row.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def refresh(self, run_id: str | None = None) -> None:
        snapshot = self.service.snapshot(run_id)
        self._flow = snapshot.flow
        self._clear()
        flow = snapshot.flow
        stages = (
            ("Identified", flow.records_identified, "records", True),
            ("Deduplicated", flow.unique_records, "unique records", True),
            ("Screened", flow.records_screened, "title/abstract stage", True),
            ("Excluded", flow.records_excluded, "screening exclusions", True),
            ("Retained", flow.records_included_for_next_stage, "next-stage candidates", True),
        )
        for title, value, detail, enabled in stages:
            self.stage_row.addWidget(PrismaStageCard(title, value, detail, enabled))
        if snapshot.run is None:
            self.note.setText("No persisted run is selected. The diagram is intentionally empty of inferred later-stage data.")
        else:
            self.note.setText(
                "Only persisted identification, deduplication and title/abstract screening are represented. Full-text retrieval and study-level assessment remain unavailable until those stages are persisted."
            )

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.stage_row.count() < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.palette().mid().color())
        cards = [self.stage_row.itemAt(i).widget() for i in range(self.stage_row.count())]
        for left, right in zip(cards, cards[1:]):
            if left is None or right is None:
                continue
            y = (left.geometry().center().y() + right.geometry().center().y()) // 2
            painter.drawLine(left.geometry().right(), y, right.geometry().left(), y)
