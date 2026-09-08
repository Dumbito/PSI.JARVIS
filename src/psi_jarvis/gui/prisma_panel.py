from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from psi_jarvis.gui.data import GuiDataService
from psi_jarvis.gui.prisma_diagram import PrismaDiagram


class PrismaReportPanel(QWidget):
    """Reusable PRISMA panel intended for the Reports workspace."""

    def __init__(self, data: GuiDataService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data
        root = QVBoxLayout(self)
        root.setSpacing(10)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("PRISMA run"))
        self.run_box = QComboBox()
        self._populate_runs()
        self.run_box.currentIndexChanged.connect(self._refresh_view)
        controls.addWidget(self.run_box, 1)
        refresh = QPushButton("Refresh PRISMA")
        refresh.setObjectName("secondary")
        refresh.clicked.connect(self.refresh)
        controls.addWidget(refresh)
        root.addLayout(controls)
        self.flow_view = PrismaDiagram(data)
        root.addWidget(self.flow_view, 1)

    def _populate_runs(self, selected_run_id: str | None = None) -> None:
        self.run_box.blockSignals(True)
        try:
            self.run_box.clear()
            for run in self.data.screening_runs():
                self.run_box.addItem(
                    f"{run.started_at} · {run.criteria_version} · {run.screened_papers:,} screened",
                    run.run_id,
                )
            if selected_run_id is not None:
                index = self.run_box.findData(selected_run_id)
                if index >= 0:
                    self.run_box.setCurrentIndex(index)
        finally:
            self.run_box.blockSignals(False)

    def _refresh_view(self) -> None:
        self.flow_view.refresh(self.run_box.currentData())

    def refresh(self) -> None:
        selected_run_id = self.run_box.currentData()
        self._populate_runs(selected_run_id)
        self._refresh_view()
