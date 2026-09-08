from __future__ import annotations

from dataclasses import dataclass

from psi_jarvis.domain.analysis.prisma_flow import PrismaFlow
from psi_jarvis.gui.data import GuiDataService, ScreeningRunSnapshot


@dataclass(frozen=True)
class PrismaReportSnapshot:
    """Read-only PRISMA report data derived from persisted screening runs."""

    flow: PrismaFlow
    run: ScreeningRunSnapshot | None

    @property
    def later_stages_persisted(self) -> bool:
        return self.flow.reports_sought > 0 or self.flow.reports_assessed > 0


class GuiPrismaService:
    """Build PRISMA presentation data without changing scientific state."""

    def __init__(self, data: GuiDataService) -> None:
        self.data = data

    def snapshot(self, run_id: str | None = None) -> PrismaReportSnapshot:
        runs = self.data.screening_runs(limit=100000)
        run = (
            next((item for item in runs if item.run_id == run_id), None)
            if run_id
            else (runs[0] if runs else None)
        )
        if run is None:
            return PrismaReportSnapshot(
                flow=PrismaFlow(
                    records_identified=0,
                    duplicates_removed=0,
                    records_screened=0,
                    records_excluded=0,
                    records_included_for_next_stage=0,
                ),
                run=None,
            )

        included, excluded = self._screening_counts(run.run_id)
        flow = PrismaFlow.from_run(
            total_input=run.total_input,
            unique_papers=run.unique_papers,
            duplicates_removed=run.duplicates_removed,
            screened_papers=run.screened_papers,
            included=included,
            excluded=excluded,
        )
        return PrismaReportSnapshot(flow=flow, run=run)

    def _screening_counts(self, run_id: str) -> tuple[int, int]:
        rows = self.data.screening_rows()
        included = sum(
            row.decision == "Included" and row.run_id == run_id for row in rows
        )
        excluded = sum(
            row.decision == "Excluded" and row.run_id == run_id for row in rows
        )
        return included, excluded
