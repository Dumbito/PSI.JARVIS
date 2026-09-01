from dataclasses import dataclass

from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.screening.result import ScreeningResult


@dataclass(frozen=True)
class ScreeningEngine:
    criteria: ScreeningCriteria

    @property
    def criteria_version(self) -> str:
        return ScreeningCriteriaVersion.from_criteria(self.criteria).value

    def evaluate(self, paper: Paper) -> ScreeningResult:
        text = (paper.title + " " + (paper.abstract or "")).lower()
        criteria_version = self.criteria_version

        topic_rule = self.criteria.topic_rule

        if not topic_rule.matches(text):
            return ScreeningResult(
                paper_id=paper.id,
                included=False,
                reason=f"Topic not found: {self.criteria.topic}",
                failed_rules=(self.criteria.topic,),
                failed_rule_ids=(topic_rule.id,),
                criteria_version=criteria_version,
            )

        matched_rules = []
        failed_rules = []
        matched_rule_ids = []
        failed_rule_ids = []

        for rule in self.criteria.exclusion_rules:
            if rule.matches(text):
                failed_rules.append(rule.value)
                failed_rule_ids.append(rule.id)

        if failed_rules:
            return ScreeningResult(
                paper_id=paper.id,
                included=False,
                reason=f"Exclusion rule matched: {failed_rules[0]}",
                failed_rules=tuple(failed_rules),
                failed_rule_ids=tuple(failed_rule_ids),
                criteria_version=criteria_version,
            )

        for rule in self.criteria.inclusion_rules:
            if rule.matches(text):
                matched_rules.append(rule.value)
                matched_rule_ids.append(rule.id)
            else:
                failed_rules.append(rule.value)
                failed_rule_ids.append(rule.id)

        if failed_rules:
            return ScreeningResult(
                paper_id=paper.id,
                included=False,
                reason=f"Inclusion rule not matched: {failed_rules[0]}",
                matched_rules=tuple(matched_rules),
                failed_rules=tuple(failed_rules),
                matched_rule_ids=tuple(matched_rule_ids),
                failed_rule_ids=tuple(failed_rule_ids),
                criteria_version=criteria_version,
            )

        return ScreeningResult(
            paper_id=paper.id,
            included=True,
            reason="Paper matches screening criteria",
            matched_rules=tuple(matched_rules),
            matched_rule_ids=tuple(matched_rule_ids),
            criteria_version=criteria_version,
        )
