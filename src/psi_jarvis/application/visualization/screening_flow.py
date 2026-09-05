from dataclasses import dataclass

from psi_jarvis.application.pipeline.pipeline import PipelineResult


@dataclass(frozen=True)
class ScreeningFlow:
    identified: int
    duplicates_removed: int
    screened: int
    excluded: int
    included: int


@dataclass(frozen=True)
class ScreeningFlowBuilder:
    def execute(self, result: PipelineResult) -> ScreeningFlow:
        return ScreeningFlow(
            identified=result.total_input,
            duplicates_removed=result.duplicates_removed,
            screened=result.screened_papers,
            excluded=result.statistics.excluded_papers,
            included=result.statistics.included_papers,
        )
