from dataclasses import dataclass

from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.screening.decision import ScreeningDecision


@dataclass(frozen=True)
class ScreeningEngine:
    criteria: ScreeningCriteria

    def evaluate(self, paper: Paper) -> ScreeningDecision:
        text = (paper.title + " " + (paper.abstract or "")).lower()

        if self.criteria.topic.lower() not in text:
            return ScreeningDecision.exclude(
                reason=f"Topic not found: {self.criteria.topic}",
            )

        for rule in self.criteria.exclusion:
            if rule.lower() in text:
                return ScreeningDecision.exclude(
                    reason=f"Exclusion rule matched: {rule}",
                )

        for rule in self.criteria.inclusion:
            if rule.lower() not in text:
                return ScreeningDecision.exclude(
                    reason=f"Inclusion rule not matched: {rule}",
                )

        return ScreeningDecision.include(
            reason="Paper matches screening criteria",
        )
