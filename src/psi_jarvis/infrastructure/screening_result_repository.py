from uuid import UUID

from psi_jarvis.domain.screening.result import ScreeningResult


class InMemoryScreeningResultRepository:
    """Repositorio temporal en memoria para resultados de cribado."""

    def __init__(self) -> None:
        self._results: dict[tuple[UUID | None, UUID], ScreeningResult] = {}

    def save(self, result: ScreeningResult) -> None:
        self._results[(result.run_id, result.paper_id)] = result

    def get(
        self,
        paper_id: UUID,
        run_id: UUID | None = None,
    ) -> ScreeningResult | None:
        return self._results.get((run_id, paper_id))

    def list_all(self) -> tuple[ScreeningResult, ...]:
        return tuple(self._results.values())
