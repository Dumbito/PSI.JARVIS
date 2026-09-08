from __future__ import annotations

from PySide6.QtWidgets import QWidget

from psi_jarvis.gui.prisma_panel import PrismaReportPanel
from psi_jarvis.gui.reports import ReportsPage


class FakeData:
    def screening_runs(self, limit=100000):
        return []

    def screening_rows(self):
        return []


class FakeWorkflow:
    pass


def test_reports_page_contains_prisma_panel(qtbot):
    page = ReportsPage(FakeData(), FakeWorkflow())
    qtbot.addWidget(page)

    panels = page.findChildren(PrismaReportPanel)
    assert len(panels) == 1
    assert isinstance(panels[0], QWidget)
