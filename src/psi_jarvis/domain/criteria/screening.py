from dataclasses import dataclass

@dataclass(frozen=True)
class ScreeningCriteria:
    """Define los criterios de inclusión y exclusión de una revisión."""

    topic: str
    inclusion: tuple[str, ...] = ()
    exclusion: tuple[str, ...] = ()

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
