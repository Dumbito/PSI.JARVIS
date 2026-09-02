from dataclasses import dataclass

from psi_jarvis.domain.screening.audit import ScreeningAudit
from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.domain.screening.run import ScreeningRun


@dataclass(frozen=True)
class ScreeningExecution:
    run: ScreeningRun
    results: tuple[ScreeningResult, ...]
    audits: tuple[ScreeningAudit, ...]

    def __post_init__(self) -> None:
        run_id = self.run.run_id
        for result in self.results:
            if result.run_id != run_id:
                raise ValueError("Screening result belongs to a different run")
        for audit in self.audits:
            if audit.run_id != run_id:
                raise ValueError("Screening audit belongs to a different run")

    @property
    def included(self) -> int:
        return sum(1 for result in self.results if result.included)

    @property
    def excluded(self) -> int:
        return sum(1 for result in self.results if not result.included)

    @property
    def screened_papers(self) -> int:
        return len(self.results)
