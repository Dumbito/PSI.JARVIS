from __future__ import annotations

from PySide6.QtWidgets import QWidget

from psi_jarvis.gui import app as app_module
from psi_jarvis.gui.prisma_panel import PrismaReportPanel


class ReportsPage(app_module.ReportsPage):
    """Existing reports page with the read-only persisted PRISMA panel."""

    def __init__(self, data, workflow, parent: QWidget | None = None) -> None:
        super().__init__(data, workflow)
        panel = PrismaReportPanel(data, self)
        layout = self.layout()
        if layout is not None:
            layout.insertWidget(max(layout.count() - 1, 0), panel, 1)
