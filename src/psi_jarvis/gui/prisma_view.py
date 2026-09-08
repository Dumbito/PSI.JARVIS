from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from psi_jarvis.gui.data import GuiDataService
from psi_jarvis.gui.prisma import GuiPrismaService


class PrismaFlowView(QWidget):
    """Read-only visual summary of the persisted PRISMA-supported stages."""

    def __init__(self, data: GuiDataService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data
        self.service = GuiPrismaService(data)
        root = QVBoxLayout(self)
        root.setSpacing(10)
        self.title = QLabel("PRISMA flow")
        self.title.setObjectName("sectionTitle")
        root.addWidget(self.title)
        self.run = QLabel()
        self.run.setObjectName("pageSubtitle")
        root.addWidget(self.run)
        self.stages = QLabel()
        self.stages.setWordWrap(True)
        root.addWidget(self.stages)
        self.boundary = QLabel()
        self.boundary.setWordWrap(True)
        self.boundary.setObjectName("pageSubtitle")
        root.addWidget(self.boundary)
        root.addStretch()
        self.refresh()

    def refresh(self, run_id: str | None = None) -> None:
        snapshot = self.service.snapshot(run_id)
        if snapshot.run is None:
            self.run.setText("No persisted screening run selected.")
            self.stages.setText("No PRISMA counts are available yet.")
            self.boundary.setText(
                "Later stages are not inferred. Full-text retrieval and study-level assessment require persisted data before they can appear here."
            )
            return

        flow = snapshot.flow
        self.run.setText(
            f"Run {snapshot.run.run_id} · {snapshot.run.criteria_version} · {snapshot.run.started_at}"
        )
        self.stages.setText(
            "\n".join(
                (
                    f"Records identified: {flow.records_identified:,}",
                    f"Duplicates removed: {flow.duplicates_removed:,}",
                    f"Records screened: {flow.records_screened:,}",
                    f"Records excluded: {flow.records_excluded:,}",
                    f"Records retained for next stage: {flow.records_included_for_next_stage:,}",
                )
            )
        )
        self.boundary.setText(
            "Supported persisted stages only. Reports sought, reports assessed, reports excluded and studies included are not populated until PSI.JARVIS persists those stages."
        )
