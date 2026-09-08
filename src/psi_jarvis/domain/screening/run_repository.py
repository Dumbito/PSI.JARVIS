from typing import Protocol
from uuid import UUID

from psi_jarvis.domain.screening.run import ScreeningRun


class ScreeningRunRepository(Protocol):
    """Define el contrato para persistir y consultar ejecuciones de cribado."""

    def save(self, run: ScreeningRun) -> None: ...

    def get(self, run_id: UUID) -> ScreeningRun | None: ...

    def list_all(self) -> tuple[ScreeningRun, ...]: ...
