from dataclasses import dataclass


@dataclass(frozen=True)
class DeduplicationAnalysis:
    total_input: int
    unique_papers: int
    duplicate_papers: int

    def __post_init__(self) -> None:
        values = (
            self.total_input,
            self.unique_papers,
            self.duplicate_papers,
        )

        if any(value < 0 for value in values):
            raise ValueError("Deduplication counts cannot be negative")

        if self.unique_papers + self.duplicate_papers != self.total_input:
            raise ValueError("Unique and duplicate papers must equal total input")

    @property
    def duplicate_rate(self) -> float:
        if self.total_input == 0:
            return 0.0
        return self.duplicate_papers / self.total_input
