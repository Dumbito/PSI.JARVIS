from dataclasses import dataclass
from uuid import UUID

from psi_jarvis.domain.screening.result import ScreeningResult


@dataclass(frozen=True)
class ScreeningAudit:
    "Registra de forma inmutable la trazabilidad de una decisión de cribado."

    paper_id: UUID
    included: bool
    reason: str
    matched_rules: tuple[str, ...] = ()
    failed_rules: tuple[str, ...] = ()

    @classmethod
    def from_result(cls, result: ScreeningResult) -> "ScreeningAudit":
        "Crea una auditoría a partir de un resultado de cribado."
        return cls(
            paper_id=result.paper_id,
            included=result.included,
            reason=result.reason,
            matched_rules=result.matched_rules,
            failed_rules=result.failed_rules,
        )
