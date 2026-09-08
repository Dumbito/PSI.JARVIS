from __future__ import annotations

from psi_jarvis.gui.prisma import GuiPrismaService


class FakeData:
    def __init__(self, runs, rows):
        self._runs = tuple(runs)
        self._rows = tuple(rows)

    def screening_runs(self, limit=100000):
        return self._runs

    def screening_rows(self):
        return self._rows


def test_snapshot_uses_latest_run_and_derives_supported_flow():
    from psi_jarvis.gui.data import ScreeningRow, ScreeningRunSnapshot

    run = ScreeningRunSnapshot("run-2", None, "v2", "2026-09-08", 10, 8, 2, 8)
    rows = [
        ScreeningRow("a", "A", 2026, "Included", "", "run-2", "v2"),
        ScreeningRow("b", "B", 2026, "Excluded", "reason", "run-2", "v2"),
        ScreeningRow("c", "C", 2026, "Included", "", "run-2", "v2"),
        ScreeningRow("d", "D", 2026, "Excluded", "reason", "run-2", "v2"),
        ScreeningRow("e", "E", 2026, "Included", "", "run-2", "v2"),
        ScreeningRow("f", "F", 2026, "Excluded", "reason", "run-2", "v2"),
        ScreeningRow("g", "G", 2026, "Included", "", "run-2", "v2"),
        ScreeningRow("h", "H", 2026, "Excluded", "reason", "run-2", "v2"),
    ]

    snapshot = GuiPrismaService(FakeData([run], rows)).snapshot()

    assert snapshot.run == run
    assert snapshot.flow.records_identified == 10
    assert snapshot.flow.duplicates_removed == 2
    assert snapshot.flow.records_screened == 8
    assert snapshot.flow.records_excluded == 4
    assert snapshot.flow.records_included_for_next_stage == 4
    assert not snapshot.later_stages_persisted


def test_snapshot_without_runs_is_empty_and_does_not_invent_later_stages():
    snapshot = GuiPrismaService(FakeData([], [])).snapshot()

    assert snapshot.run is None
    assert snapshot.flow.records_identified == 0
    assert snapshot.flow.records_screened == 0
    assert snapshot.flow.reports_sought == 0
    assert snapshot.flow.reports_assessed == 0
    assert snapshot.flow.studies_included == 0
