from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from psi_jarvis.domain.screening.audit import ScreeningAudit


@dataclass(frozen=True)
class RuleStatistics:
    rule_id: str
    matched: int
    failed: int

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("Rule ID cannot be empty")
        if self.matched < 0 or self.failed < 0:
            raise ValueError("Rule statistics cannot be negative")

    @property
    def evaluated(self) -> int:
        return self.matched + self.failed

    @property
    def match_rate(self) -> float:
        return 0.0 if self.evaluated == 0 else self.matched / self.evaluated

    @property
    def failure_rate(self) -> float:
        return 0.0 if self.evaluated == 0 else self.failed / self.evaluated


@dataclass(frozen=True)
class RuleAnalysis:
    rules: tuple[RuleStatistics, ...]

    @classmethod
    def from_audits(cls, audits: Iterable[ScreeningAudit]) -> "RuleAnalysis":
        matched = Counter(
            rule_id
            for audit in audits
            for rule_id in audit.matched_rule_ids
        )
        failed = Counter(
            rule_id
            for audit in audits
            for rule_id in audit.failed_rule_ids
        )
        rule_ids = sorted(set(matched) | set(failed))
        return cls(
            rules=tuple(
                RuleStatistics(
                    rule_id=rule_id,
                    matched=matched[rule_id],
                    failed=failed[rule_id],
                )
                for rule_id in rule_ids
            )
        )

    @property
    def total_rules(self) -> int:
        return len(self.rules)

    def by_rule_id(self, rule_id: str) -> RuleStatistics | None:
        return next(
            (rule for rule in self.rules if rule.rule_id == rule_id),
            None,
        )
