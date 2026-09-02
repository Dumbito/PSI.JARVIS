from uuid import UUID

from psi_jarvis.domain.screening.audit import ScreeningAudit


class InMemoryScreeningAuditRepository:
    """Repositorio temporal en memoria para auditorías de cribado."""

    def __init__(self) -> None:
        self._audits: dict[tuple[UUID | None, UUID], ScreeningAudit] = {}

    def save(self, audit: ScreeningAudit) -> None:
        self._audits[(audit.run_id, audit.paper_id)] = audit

    def get(
        self,
        paper_id: UUID,
        run_id: UUID | None = None,
    ) -> ScreeningAudit | None:
        return self._audits.get((run_id, paper_id))

    def list_all(self) -> tuple[ScreeningAudit, ...]:
        return tuple(self._audits.values())
