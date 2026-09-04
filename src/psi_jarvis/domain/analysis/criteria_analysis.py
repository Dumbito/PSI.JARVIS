from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from psi_jarvis.domain.screening.audit import ScreeningAudit


@dataclass(frozen=True)
class CriterionStatistics:
    criterion_id: str
    matched: int
    failed: int

    def __post_init__(self) -> None:
        if not self.criterion_id.strip():
            raise ValueError("Criterion ID cannot be empty")

        if self.matched < 0 or self.failed < 0:
            raise ValueError("Criterion statistics cannot be negative")

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
class CriteriaAnalysis:
    criteria: tuple[CriterionStatistics, ...]

    @classmethod
    def from_audits(
        cls,
        audits: Iterable[ScreeningAudit],
    ) -> "CriteriaAnalysis":
        audits = tuple(audits)

        matched = Counter(
            criterion_id
            for audit in audits
            for criterion_id in audit.matched_rule_ids
        )

        failed = Counter(
            criterion_id
            for audit in audits
            for criterion_id in audit.failed_rule_ids
        )

        criterion_ids = sorted(set(matched) | set(failed))

        return cls(
            criteria=tuple(
                CriterionStatistics(
                    criterion_id=criterion_id,
                    matched=matched[criterion_id],
                    failed=failed[criterion_id],
                )
                for criterion_id in criterion_ids
            )
        )

    @property
    def total_criteria(self) -> int:
        return len(self.criteria)

    def by_criterion_id(
        self,
        criterion_id: str,
    ) -> CriterionStatistics | None:
        return next(
            (
                criterion
                for criterion in self.criteria
                if criterion.criterion_id == criterion_id
            ),
            None,
        )