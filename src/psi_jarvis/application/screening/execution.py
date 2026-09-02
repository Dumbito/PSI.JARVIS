from dataclasses import dataclass
from uuid import UUID

from psi_jarvis.domain.screening.audit import ScreeningAudit
from psi_jarvis.domain.screening.audit_repository import ScreeningAuditRepository
from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.domain.screening.result_repository import ScreeningResultRepository
from psi_jarvis.domain.screening.run import ScreeningRun
from psi_jarvis.domain.screening.run_repository import ScreeningRunRepository


@dataclass(frozen=True)
class ScreeningExecution:
    run: ScreeningRun
    results: tuple[ScreeningResult, ...]
    audits: tuple[ScreeningAudit, ...]

    def __post_init__(self) -> None:
        if any(result.run_id != self.run.run_id for result in self.results):
            raise ValueError("All screening results must belong to the execution run")
        if any(audit.run_id != self.run.run_id for audit in self.audits):
            raise ValueError("All screening audits must belong to the execution run")

    @property
    def included(self) -> int:
        return sum(1 for result in self.results if result.included)

    @property
    def excluded(self) -> int:
        return sum(1 for result in self.results if not result.included)

    @property
    def screened_papers(self) -> int:
        return len(self.results)


class ScreeningExecutionLoader:
    def __init__(
        self,
        run_repository: ScreeningRunRepository,
        result_repository: ScreeningResultRepository,
        audit_repository: ScreeningAuditRepository,
    ) -> None:
        self.run_repository = run_repository
        self.result_repository = result_repository
        self.audit_repository = audit_repository

    def load(self, run_id: UUID) -> ScreeningExecution | None:
        run = self.run_repository.get(run_id)
        if run is None:
            return None

        results = tuple(
            result
            for result in self.result_repository.list_all()
            if result.run_id == run_id
        )

        audits = tuple(
            audit
            for audit in self.audit_repository.list_all()
            if audit.run_id == run_id
        )

        return ScreeningExecution(
            run=run,
            results=results,
            audits=audits,
        )
