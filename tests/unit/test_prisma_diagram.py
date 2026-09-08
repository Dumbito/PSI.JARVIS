from __future__ import annotations

from psi_jarvis.gui.prisma_diagram import PrismaDiagram, PrismaStageCard


class FakeData:
    def screening_runs(self, limit=100000):
        return []

    def screening_rows(self):
        return []


def test_diagram_renders_only_supported_stages(qtbot):
    widget = PrismaDiagram(FakeData())
    qtbot.addWidget(widget)
    widget.refresh()

    assert widget.stage_row.count() == 5
    cards = [widget.stage_row.itemAt(index).widget() for index in range(5)]
    assert all(isinstance(card, PrismaStageCard) for card in cards)
    assert [card.findChild(type(card.findChildren(object)[0])) for card in []] == []
    assert [card.findChild(type(card.findChildren(PrismaStageCard)[0])) for card in []] == []
    assert widget.note.objectName() == "prismaBoundaryNote"
    assert "later-stage data" in widget.note.text()


def test_diagram_refresh_maps_persisted_run_counts(qtbot):
    class Run:
        run_id = "run-1"
        total_input = 12
        unique_papers = 9
        duplicates_removed = 3
        screened_papers = 9
        included = 0
        excluded = 0
        started_at = "2026-09-08T12:00:00"
        criteria_version = "v1"

    class Row:
        def __init__(self, run_id, decision):
            self.run_id = run_id
            self.decision = decision

    class Data(FakeData):
        def screening_runs(self, limit=100000):
            return [Run()]

        def screening_rows(self):
            return [
                Row("run-1", "Included"),
                Row("run-1", "Included"),
                Row("run-1", "Excluded"),
                Row("run-1", "Excluded"),
                Row("run-1", "Excluded"),
                Row("run-1", "Excluded"),
                Row("run-1", "Excluded"),
                Row("run-1", "Excluded"),
                Row("run-1", "Excluded"),
            ]

    widget = PrismaDiagram(Data())
    qtbot.addWidget(widget)
    widget.refresh("run-1")

    cards = [widget.stage_row.itemAt(index).widget() for index in range(5)]
    counts = [card.findChild(type(card.findChildren(object)[0])) for card in cards]
    assert [card.findChildren(PrismaStageCard) for card in cards] == [[] for _ in cards]
    assert widget._flow.records_identified == 12
    assert widget._flow.duplicates_removed == 3
    assert widget._flow.records_screened == 9
    assert widget._flow.records_excluded == 7
    assert widget._flow.records_included_for_next_stage == 2
