from dataclasses import dataclass
from typing import Iterable

from psi_jarvis.domain.screening.audit import ScreeningAudit


@dataclass(frozen=True)
class ScreeningMetrics:
    total_input: int
    screened_papers: int
    included_papers: int
    excluded_papers: int
    duplicates_removed: int
    total_matched_rules: int
    total_failed_rules: int

    def __post_init__(self) -> None:
        values = (
            self.total_input,
            self.screened_papers,
            self.included_papers,
            self.excluded_papers,
            self.duplicates_removed,
            self.total_matched_rules,
            self.total_failed_rules,
        )
        if any(value < 0 for value in values):
            raise ValueError("Screening metrics cannot be negative")

        if self.included_papers + self.excluded_papers != self.screened_papers:
            raise ValueError("Included and excluded papers must equal screened papers")

        if self.screened_papers + self.duplicates_removed != self.total_input:
            raise ValueError("Screened papers and duplicates must equal total input")

    @classmethod
    def from_audits(
        cls,
        total_input: int,
        screened_papers: int,
        included_papers: int,
        excluded_papers: int,
        duplicates_removed: int,
        audits: Iterable[ScreeningAudit],
    ) -> "ScreeningMetrics":
        audits = tuple(audits)

        return cls(
            total_input=total_input,
            screened_papers=screened_papers,
            included_papers=included_papers,
            excluded_papers=excluded_papers,
            duplicates_removed=duplicates_removed,
            total_matched_rules=sum(len(audit.matched_rule_ids) for audit in audits),
            total_failed_rules=sum(len(audit.failed_rule_ids) for audit in audits),
        )

    @property
    def screening_completion_rate(self) -> float:
        return (
            0.0
            if self.total_input == 0
            else self.screened_papers / self.total_input
        )

    @property
    def screening_yield(self) -> float:
        return (
            0.0
            if self.total_input == 0
            else self.included_papers / self.total_input
        )

    @property
    def exclusion_yield(self) -> float:
        return (
            0.0
            if self.total_input == 0
            else self.excluded_papers / self.total_input
        )

    @property
    def average_matched_rules(self) -> float:
        return (
            0.0
            if self.screened_papers == 0
            else self.total_matched_rules / self.screened_papers
        )

    @property
    def average_failed_rules(self) -> float:
        return (
            0.0
            if self.screened_papers == 0
            else self.total_failed_rules / self.screened_papers
        )
