from __future__ import annotations

from psi_jarvis.gui.prisma_view import PrismaFlowView


class FakeData:
    def screening_runs(self, limit=100000):
        return []

    def screening_rows(self):
        return []


def test_view_can_refresh_without_persisted_runs(qtbot):
    view = PrismaFlowView(FakeData())
    qtbot.addWidget(view)
    view.refresh()
    assert "No persisted screening run" in view.run.text()
    assert "No PRISMA counts" in view.stages.text()
