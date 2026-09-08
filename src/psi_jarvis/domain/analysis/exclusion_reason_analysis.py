from collections import Counter
from dataclasses import dataclass
from collections.abc import Iterable

from psi_jarvis.domain.screening.audit import ScreeningAudit


@dataclass(frozen=True)
class ExclusionReasonStatistics:
    reason: str
    count: int
    total_excluded: int

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("Exclusion reason cannot be empty")
        if self.count < 0 or self.total_excluded < 0:
            raise ValueError("Exclusion statistics cannot be negative")
        if self.count > self.total_excluded:
            raise ValueError("Exclusion reason count cannot exceed total exclusions")

    @property
    def rate(self) -> float:
        return 0.0 if self.total_excluded == 0 else self.count / self.total_excluded


@dataclass(frozen=True)
class ExclusionReasonAnalysis:
    reasons: tuple[ExclusionReasonStatistics, ...]

    @classmethod
    def from_audits(cls, audits: Iterable[ScreeningAudit]) -> "ExclusionReasonAnalysis":
        excluded_reasons = Counter(
            audit.reason for audit in audits if not audit.included
        )
        total_excluded = sum(excluded_reasons.values())
        return cls(
            reasons=tuple(
                ExclusionReasonStatistics(
                    reason=reason,
                    count=count,
                    total_excluded=total_excluded,
                )
                for reason, count in sorted(excluded_reasons.items())
            )
        )

    @property
    def total_reasons(self) -> int:
        return len(self.reasons)

    @property
    def total_excluded(self) -> int:
        return sum(reason.count for reason in self.reasons)

    def by_reason(self, reason: str) -> ExclusionReasonStatistics | None:
        return next(
            (item for item in self.reasons if item.reason == reason),
            None,
        )
