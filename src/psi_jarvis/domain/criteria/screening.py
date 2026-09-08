from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psi_jarvis.domain.screening.rules.logical import ScreeningRule


@dataclass(frozen=True)
class ScreeningCriteria:
    """Define los criterios de inclusión y exclusión de una revisión."""

    topic: str
    inclusion: tuple[str, ...] = ()
    exclusion: tuple[str, ...] = ()
    inclusion_expression: "ScreeningRule | None" = None
    exclusion_expression: "ScreeningRule | None" = None

    def __post_init__(self) -> None:
        if not self.topic.strip():
            raise ValueError("Screening topic cannot be empty")

        if any(not rule.strip() for rule in self.inclusion):
            raise ValueError("Screening inclusion rules cannot be empty")

        if any(not rule.strip() for rule in self.exclusion):
            raise ValueError("Screening exclusion rules cannot be empty")

    @property
    def topic_rule(self):
        from psi_jarvis.domain.screening.rules.text_rule import TextRule

        return TextRule(self.topic)

    @property
    def inclusion_rules(self):
        from psi_jarvis.domain.screening.rules.text_rule import TextRule

        return tuple(TextRule(rule) for rule in self.inclusion)

    @property
    def exclusion_rules(self):
        from psi_jarvis.domain.screening.rules.text_rule import TextRule

        return tuple(TextRule(rule) for rule in self.exclusion)

    @property
    def inclusion_rule(self):
        if self.inclusion_expression is not None:
            return self.inclusion_expression
        from psi_jarvis.domain.screening.rules.logical import AllOfRule

        return AllOfRule(self.inclusion_rules)

    @property
    def has_custom_logic(self) -> bool:
        return (
            self.inclusion_expression is not None
            or self.exclusion_expression is not None
        )

    @property
    def exclusion_rule(self):
        if self.exclusion_expression is not None:
            return self.exclusion_expression
        from psi_jarvis.domain.screening.rules.logical import AnyOfRule

        return AnyOfRule(self.exclusion_rules)
