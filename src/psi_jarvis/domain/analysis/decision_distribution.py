from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionDistribution:
    total: int
    included: int
    excluded: int

    def __post_init__(self) -> None:
        values = (self.total, self.included, self.excluded)
        if any(value < 0 for value in values):
            raise ValueError("Decision counts cannot be negative")
        if self.included + self.excluded != self.total:
            raise ValueError("Included and excluded decisions must equal total")

    @property
    def inclusion_rate(self) -> float:
        return 0.0 if self.total == 0 else self.included / self.total

    @property
    def exclusion_rate(self) -> float:
        return 0.0 if self.total == 0 else self.excluded / self.total

    @property
    def counts(self) -> dict[str, int]:
        return {
            "included": self.included,
            "excluded": self.excluded,
        }
