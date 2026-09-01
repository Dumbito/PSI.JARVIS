from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class ScreeningCriteriaVersion:
    """Identidad estable de un conjunto de criterios de cribado."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Screening criteria version cannot be empty")

    @classmethod
    def from_criteria(cls, criteria) -> "ScreeningCriteriaVersion":
        payload = "|".join(
            (
                criteria.topic.strip(),
                *[rule.strip() for rule in criteria.inclusion],
                "--EXCLUSION--",
                *[rule.strip() for rule in criteria.exclusion],
            )
        )
        digest = sha256(payload.encode("utf-8")).hexdigest()[:16]
        return cls(digest)
