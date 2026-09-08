from __future__ import annotations

from psi_jarvis.gui.prisma_diagram import PrismaDiagram


class FakeData:
    def screening_runs(self, limit=100000):
        return []

    def screening_rows(self):
        return []


def test_diagram_renders_supported_stages(qtbot):
    widget = PrismaDiagram(FakeData())
    qtbot.addWidget(widget)
    widget.refresh()
    assert widget.stage_row.count() == 5
    assert widget.stage_row.itemAt(0).widget().findChildren(type(widget.note))
