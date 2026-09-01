from dataclasses import dataclass

from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.domain.screening.rules.text_rule import TextRule


@dataclass(frozen=True)
class ScreeningEngine:
    criteria: ScreeningCriteria

    def evaluate(self, paper: Paper) -> ScreeningResult:
        text = (paper.title + " " + (paper.abstract or "")).lower()

        topic_rule = TextRule(self.criteria.topic)

        if not topic_rule.matches(text):
            return ScreeningResult(
                paper_id=paper.id,
                included=False,
                reason=f"Topic not found: {self.criteria.topic}",
                failed_rules=(self.criteria.topic,),
            )

        matched_rules = []
        failed_rules = []

        for rule in self.criteria.exclusion:
            if TextRule(rule).matches(text):
                failed_rules.append(rule)

        if failed_rules:
            return ScreeningResult(
                paper_id=paper.id,
                included=False,
                reason=f"Exclusion rule matched: {failed_rules[0]}",
                failed_rules=tuple(failed_rules),
            )

        for rule in self.criteria.inclusion:
            if TextRule(rule).matches(text):
                matched_rules.append(rule)
            else:
                failed_rules.append(rule)

        if failed_rules:
            return ScreeningResult(
                paper_id=paper.id,
                included=False,
                reason=f"Inclusion rule not matched: {failed_rules[0]}",
                matched_rules=tuple(matched_rules),
                failed_rules=tuple(failed_rules),
            )

        return ScreeningResult(
            paper_id=paper.id,
            included=True,
            reason="Paper matches screening criteria",
            matched_rules=tuple(matched_rules),
        )
