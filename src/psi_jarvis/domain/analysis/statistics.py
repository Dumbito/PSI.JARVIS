from dataclasses import dataclass


@dataclass(frozen=True)
class StatisticalSummary:
    total_input: int
    unique_papers: int
    duplicates_removed: int
    screened_papers: int
    included_papers: int
    excluded_papers: int

    def __post_init__(self):
        values = (
            self.total_input,
            self.unique_papers,
            self.duplicates_removed,
            self.screened_papers,
            self.included_papers,
            self.excluded_papers,
        )
        if any(value < 0 for value in values):
            raise ValueError("Statistical counts cannot be negative")
        if self.included_papers + self.excluded_papers != self.screened_papers:
            raise ValueError("Included and excluded papers must equal screened papers")
        if self.unique_papers + self.duplicates_removed != self.total_input:
            raise ValueError("Unique papers and duplicates must equal total input")

    @property
    def inclusion_rate(self) -> float:
        return (
            0.0
            if self.screened_papers == 0
            else self.included_papers / self.screened_papers
        )

    @property
    def exclusion_rate(self) -> float:
        return (
            0.0
            if self.screened_papers == 0
            else self.excluded_papers / self.screened_papers
        )

    @property
    def deduplication_rate(self) -> float:
        return (
            0.0 if self.total_input == 0 else self.duplicates_removed / self.total_input
        )
