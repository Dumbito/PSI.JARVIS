from dataclasses import dataclass
from uuid import UUID

from psi_jarvis.domain.screening.rules.trace import RuleTrace


@dataclass(frozen=True)
class ScreeningResult:
    """Resultado detallado de la evaluación de un paper."""

    paper_id: UUID
    included: bool
    reason: str
    run_id: UUID | None = None
    matched_rules: tuple[str, ...] = ()
    failed_rules: tuple[str, ...] = ()
    matched_rule_ids: tuple[str, ...] = ()
    failed_rule_ids: tuple[str, ...] = ()
    criteria_version: str = ""
    rule_traces: tuple[RuleTrace, ...] = ()

    def with_run_id(self, run_id: UUID) -> "ScreeningResult":
        """Devuelve una copia del resultado asociada a una ejecución."""
        return ScreeningResult(
            paper_id=self.paper_id,
            included=self.included,
            reason=self.reason,
            run_id=run_id,
            matched_rules=self.matched_rules,
            failed_rules=self.failed_rules,
            matched_rule_ids=self.matched_rule_ids,
            failed_rule_ids=self.failed_rule_ids,
            criteria_version=self.criteria_version,
            rule_traces=self.rule_traces,
        )

    @property
    def status(self) -> str:
        """Devuelve el estado textual del resultado."""
        return "include" if self.included else "exclude"
