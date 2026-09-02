from dataclasses import dataclass
from uuid import UUID

from psi_jarvis.domain.screening.audit_repository import ScreeningAuditRepository
from psi_jarvis.domain.screening.execution import ScreeningExecution
from psi_jarvis.domain.screening.result_repository import ScreeningResultRepository
from psi_jarvis.domain.screening.run_repository import ScreeningRunRepository

@dataclass(frozen=True)
class ScreeningExecutionLoader:
    run_repository: ScreeningRunRepository
    result_repository: ScreeningResultRepository
    audit_repository: ScreeningAuditRepository

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
