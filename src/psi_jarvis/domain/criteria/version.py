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
        if (
            criteria.inclusion_expression is None
            and criteria.exclusion_expression is None
        ):
            payload = "|".join(
                (
                    criteria.topic.strip(),
                    *[rule.strip() for rule in criteria.inclusion],
                    "--EXCLUSION--",
                    *[rule.strip() for rule in criteria.exclusion],
                )
            )
        else:
            payload = "|".join(
                (
                    criteria.topic.strip(),
                    "--INCLUSION-EXPRESSION--",
                    criteria.inclusion_rule.id,
                    "--EXCLUSION-EXPRESSION--",
                    criteria.exclusion_rule.id,
                )
            )
        digest = sha256(payload.encode("utf-8")).hexdigest()[:16]
        return cls(digest)
