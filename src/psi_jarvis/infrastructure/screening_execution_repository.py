from uuid import UUID

from psi_jarvis.domain.screening.execution import ScreeningExecution


class InMemoryScreeningExecutionRepository:
    def __init__(self) -> None:
        self._executions: dict[UUID, ScreeningExecution] = {}

    def save(self, execution: ScreeningExecution) -> None:
        self._executions[execution.run.run_id] = execution

    def get(self, run_id: UUID) -> ScreeningExecution | None:
        return self._executions.get(run_id)

    def list_all(self) -> tuple[ScreeningExecution, ...]:
        return tuple(self._executions.values())
