from __future__ import annotations

from PySide6.QtWidgets import QComboBox

from psi_jarvis.gui.prisma_panel import PrismaReportPanel


class FakeRun:
    def __init__(self, run_id: str, started_at: str, criteria_version: str, screened_papers: int):
        self.run_id = run_id
        self.started_at = started_at
        self.criteria_version = criteria_version
        self.screened_papers = screened_papers


class FakeData:
    def screening_runs(self, limit=100000):
        return [
            FakeRun("run-2", "2026-09-08T12:00:00", "v2", 20),
            FakeRun("run-1", "2026-09-07T12:00:00", "v1", 10),
        ]

    def screening_rows(self):
        return []


def test_panel_exposes_run_selector_and_diagram(qtbot):
    panel = PrismaReportPanel(FakeData())
    qtbot.addWidget(panel)

    assert isinstance(panel.run_box, QComboBox)
    assert panel.run_box.count() == 2
    assert panel.run_box.itemData(0) == "run-2"
    assert panel.run_box.itemData(1) == "run-1"
    assert panel.flow_view.stage_row.count() == 5


def test_panel_refresh_repopulates_run_selector(qtbot):
    panel = PrismaReportPanel(FakeData())
    qtbot.addWidget(panel)

    panel.refresh()

    assert panel.run_box.count() == 2
    assert panel.flow_view._flow.records_identified == 0
