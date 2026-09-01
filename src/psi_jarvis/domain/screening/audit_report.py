from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from psi_jarvis.domain.screening.audit import ScreeningAudit


@dataclass(frozen=True)
class ScreeningAuditReport:
    "Resumen estadístico inmutable de una ejecución de cribado."

    total_evaluated: int
    included: int
    excluded: int
    criteria_version: str = ""
    audits: tuple[ScreeningAudit, ...] = ()

    @property
    def inclusion_rate(self) -> float:
        if self.total_evaluated == 0:
            return 0.0
        return self.included / self.total_evaluated

    @property
    def exclusion_rate(self) -> float:
        if self.total_evaluated == 0:
            return 0.0
        return self.excluded / self.total_evaluated

    @property
    def exclusion_reasons(self) -> tuple[str, ...]:
        return tuple(
            audit.reason
            for audit in self.audits
            if not audit.included
        )

    @property
    def exclusion_reason_counts(self) -> dict[str, int]:
        return dict(Counter(self.exclusion_reasons))

    @property
    def failed_rule_id_counts(self) -> dict[str, int]:
        return dict(
            Counter(
                rule_id
                for audit in self.audits
                if not audit.included
                for rule_id in audit.failed_rule_ids
            )
        )

    @property
    def matched_rule_id_counts(self) -> dict[str, int]:
        return dict(
            Counter(
                rule_id
                for audit in self.audits
                for rule_id in audit.matched_rule_ids
            )
        )

    @classmethod
    def from_audits(cls, audits: Iterable[ScreeningAudit]) -> "ScreeningAuditReport":
        audits = tuple(audits)
        versions = {audit.criteria_version for audit in audits if audit.criteria_version}
        if len(versions) > 1:
            raise ValueError("All audits must use the same screening criteria version")
        criteria_version = next(iter(versions), "")
        return cls(
            total_evaluated=len(audits),
            included=sum(1 for audit in audits if audit.included),
            excluded=sum(1 for audit in audits if not audit.included),
            criteria_version=criteria_version,
            audits=audits,
        )

    @property
    def failed_rule_counts(self) -> dict[str, int]:
        return dict(
            Counter(
                rule
                for audit in self.audits
                if not audit.included
                for rule in audit.failed_rules
            )
        )
