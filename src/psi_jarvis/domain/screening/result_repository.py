from typing import Protocol
from uuid import UUID

from psi_jarvis.domain.screening.result import ScreeningResult


class ScreeningResultRepository(Protocol):
    """Define el contrato para persistir resultados individuales de cribado."""

    def save(self, result: ScreeningResult) -> None:
        ...

    def get(self, paper_id: UUID, run_id: UUID | None = None) -> ScreeningResult | None:
        ...

    def list_all(self) -> tuple[ScreeningResult, ...]:
        ...
