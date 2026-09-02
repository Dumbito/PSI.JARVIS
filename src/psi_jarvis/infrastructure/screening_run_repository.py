from uuid import UUID

from psi_jarvis.domain.screening.run import ScreeningRun


class InMemoryScreeningRunRepository:
    """Repositorio temporal en memoria para ejecuciones de cribado."""

    def __init__(self) -> None:
        self._runs: dict[UUID, ScreeningRun] = {}

    def save(self, run: ScreeningRun) -> None:
        self._runs[run.run_id] = run

    def get(self, run_id: UUID) -> ScreeningRun | None:
        return self._runs.get(run_id)

    def list_all(self) -> tuple[ScreeningRun, ...]:
        return tuple(self._runs.values())
