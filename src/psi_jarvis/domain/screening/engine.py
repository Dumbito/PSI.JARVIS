from dataclasses import dataclass

from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.domain.screening.rules.evaluation import evaluate_rule


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

        if self.criteria.has_custom_logic:
            return self._evaluate_custom_logic(
                paper=paper,
                text=text,
                criteria_version=criteria_version,
            )

        matched_exclusions = tuple(
            rule.value
            for rule in self.criteria.exclusion_rules
            if rule.matches(text)
        )

        matched_exclusion_ids = tuple(
            rule.id
            for rule in self.criteria.exclusion_rules
            if rule.matches(text)
        )

        if matched_exclusions:
            return ScreeningResult(
                paper_id=paper.id,
                included=False,
                reason=f"Exclusion rule matched: {matched_exclusions[0]}",
                failed_rules=matched_exclusions,
                failed_rule_ids=matched_exclusion_ids,
                criteria_version=criteria_version,
            )

        matched_inclusions = tuple(
            rule.value
            for rule in self.criteria.inclusion_rules
            if rule.matches(text)
        )

        failed_inclusions = tuple(
            rule.value
            for rule in self.criteria.inclusion_rules
            if not rule.matches(text)
        )

        matched_inclusion_ids = tuple(
            rule.id
            for rule in self.criteria.inclusion_rules
            if rule.matches(text)
        )

        failed_inclusion_ids = tuple(
            rule.id
            for rule in self.criteria.inclusion_rules
            if not rule.matches(text)
        )

        if failed_inclusions:
            return ScreeningResult(
                paper_id=paper.id,
                included=False,
                reason=f"Inclusion rule not matched: {failed_inclusions[0]}",
                matched_rules=matched_inclusions,
                failed_rules=failed_inclusions,
                matched_rule_ids=matched_inclusion_ids,
                failed_rule_ids=failed_inclusion_ids,
                criteria_version=criteria_version,
            )

        return ScreeningResult(
            paper_id=paper.id,
            included=True,
            reason="Paper matches screening criteria",
            matched_rules=matched_inclusions,
            matched_rule_ids=matched_inclusion_ids,
            criteria_version=criteria_version,
        )

    def _evaluate_custom_logic(
        self,
        paper: Paper,
        text: str,
        criteria_version: str,
    ) -> ScreeningResult:
        exclusion = evaluate_rule(self.criteria.exclusion_rule, text)

        if exclusion.matched:
            return ScreeningResult(
                paper_id=paper.id,
                included=False,
                reason=f"Exclusion expression matched: {self.criteria.exclusion_rule.id}",
                failed_rules=(self.criteria.exclusion_rule.id,),
                failed_rule_ids=exclusion.matched_rule_ids
                or (self.criteria.exclusion_rule.id,),
                matched_rule_ids=exclusion.matched_rule_ids,
                criteria_version=criteria_version,
            )

        inclusion = evaluate_rule(self.criteria.inclusion_rule, text)

        if not inclusion.matched:
            return ScreeningResult(
                paper_id=paper.id,
                included=False,
                reason=f"Inclusion expression not matched: {self.criteria.inclusion_rule.id}",
                failed_rules=(self.criteria.inclusion_rule.id,),
                failed_rule_ids=inclusion.failed_rule_ids
                or (self.criteria.inclusion_rule.id,),
                matched_rule_ids=inclusion.matched_rule_ids,
                criteria_version=criteria_version,
                rule_traces=(
                    inclusion.trace,
                ) if inclusion.trace is not None else (),
            )

        return ScreeningResult(
            paper_id=paper.id,
            included=True,
            reason="Paper matches screening criteria",
            matched_rules=(self.criteria.inclusion_rule.id,),
            matched_rule_ids=inclusion.matched_rule_ids
            or (self.criteria.inclusion_rule.id,),
            criteria_version=criteria_version,
            rule_traces=(inclusion.trace,) if inclusion.trace is not None else (),
        )
