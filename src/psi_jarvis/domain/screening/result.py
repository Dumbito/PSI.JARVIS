from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ScreeningResult:
    """Resultado detallado de la evaluación de un paper."""

    paper_id: UUID
    included: bool
    reason: str
    matched_rules: tuple[str, ...] = ()
    failed_rules: tuple[str, ...] = ()

    @property
    def status(self) -> str:
        """Devuelve el estado textual del resultado."""
        return "include" if self.included else "exclude"
