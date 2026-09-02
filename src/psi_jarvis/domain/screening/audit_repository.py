from typing import Protocol
from uuid import UUID

from psi_jarvis.domain.screening.audit import ScreeningAudit


class ScreeningAuditRepository(Protocol):
    """Define el contrato para persistir auditorías de cribado."""

    def save(self, audit: ScreeningAudit) -> None:
        ...

    def get(
        self,
        paper_id: UUID,
        run_id: UUID | None = None,
    ) -> ScreeningAudit | None:
        ...

    def list_all(self) -> tuple[ScreeningAudit, ...]:
        ...
