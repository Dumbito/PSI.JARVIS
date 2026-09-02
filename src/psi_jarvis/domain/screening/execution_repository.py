from typing import Protocol
from uuid import UUID

from psi_jarvis.domain.screening.execution import ScreeningExecution


class ScreeningExecutionRepository(Protocol):
    def save(self, execution: ScreeningExecution) -> None: ...

    def get(self, run_id: UUID) -> ScreeningExecution | None: ...

    def list_all(self) -> tuple[ScreeningExecution, ...]: ...
