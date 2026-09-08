from dataclasses import dataclass

from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion
from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.domain.screening.rules.trace import RuleTrace


@dataclass(frozen=True)
class RuleStatistics:
    rule_id: str
    matched: int
    failed: int

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("Rule ID cannot be empty")

        if self.matched < 0 or self.failed < 0:
            raise ValueError("Rule statistics cannot be negative")

    @property
    def evaluated(self) -> int:
        return self.matched + self.failed


@dataclass(frozen=True)
class RuleConsistency:
    criteria_version: str
    total_results: int
    included_results: int
    excluded_results: int
    rules: tuple[RuleStatistics, ...]
    untracked_rule_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.criteria_version:
            raise ValueError("Criteria version cannot be empty")

        counts = (
            self.total_results,
            self.included_results,
            self.excluded_results,
        )

        if any(value < 0 for value in counts):
            raise ValueError("Rule consistency counts cannot be negative")

        if self.included_results + self.excluded_results != self.total_results:
            raise ValueError("Included and excluded results must equal total results")

        if any(not rule_id.strip() for rule_id in self.untracked_rule_ids):
            raise ValueError("Untracked rule IDs cannot be empty")

        rule_ids = [rule.rule_id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("Rule statistics must contain unique rule IDs")

    @property
    def rule_count(self) -> int:
        return len(self.rules)

    @property
    def consistent(self) -> bool:
        return not self.untracked_rule_ids

    @classmethod
    def from_results(
        cls,
        criteria: ScreeningCriteria,
        results: tuple[ScreeningResult, ...],
    ) -> "RuleConsistency":
        if len({result.paper_id for result in results}) != len(results):
            raise ValueError("Results must not contain duplicate papers")

        expected_version = ScreeningCriteriaVersion.from_criteria(criteria).value
        result_versions = {result.criteria_version for result in results}

        if result_versions != {expected_version}:
            raise ValueError("Results do not match criteria version")

        declared_rule_ids = {
            criteria.topic_rule.id,
            *(rule.id for rule in criteria.inclusion_rules),
            *(rule.id for rule in criteria.exclusion_rules),
        }

        if criteria.has_custom_logic:
            declared_rule_ids.add(criteria.inclusion_rule.id)
            declared_rule_ids.add(criteria.exclusion_rule.id)

        statistics: dict[str, list[int]] = {}

        for result in results:
            referenced_rule_ids = set(result.matched_rule_ids) | set(
                result.failed_rule_ids
            )

            for trace in result.rule_traces:
                cls._collect_trace_ids(trace, referenced_rule_ids)

            for rule_id in referenced_rule_ids:
                statistics.setdefault(rule_id, [0, 0])

            counted_rule_ids = set()

            for rule_id in result.matched_rule_ids:
                statistics.setdefault(rule_id, [0, 0])[0] += 1
                counted_rule_ids.add(rule_id)

            for rule_id in result.failed_rule_ids:
                statistics.setdefault(rule_id, [0, 0])[1] += 1
                counted_rule_ids.add(rule_id)

            for trace in result.rule_traces:
                cls._collect_trace_counts(
                    trace,
                    statistics,
                    counted_rule_ids,
                )

        untracked_rule_ids = tuple(
            sorted(
                rule_id for rule_id in statistics if rule_id not in declared_rule_ids
            )
        )

        rule_statistics = tuple(
            RuleStatistics(
                rule_id=rule_id,
                matched=counts[0],
                failed=counts[1],
            )
            for rule_id, counts in sorted(statistics.items())
        )

        included_results = sum(result.included for result in results)
        excluded_results = len(results) - included_results

        return cls(
            criteria_version=expected_version,
            total_results=len(results),
            included_results=included_results,
            excluded_results=excluded_results,
            rules=rule_statistics,
            untracked_rule_ids=untracked_rule_ids,
        )

    @staticmethod
    def _collect_trace_ids(
        trace: RuleTrace,
        rule_ids: set[str],
    ) -> None:
        rule_ids.add(trace.rule_id)
        for child in trace.children:
            RuleConsistency._collect_trace_ids(child, rule_ids)

    @staticmethod
    def _collect_trace_counts(
        trace: RuleTrace,
        statistics: dict[str, list[int]],
        counted_rule_ids: set[str],
    ) -> None:
        if trace.rule_id not in counted_rule_ids:
            counts = statistics.setdefault(trace.rule_id, [0, 0])

            if trace.matched:
                counts[0] += 1
            else:
                counts[1] += 1

            counted_rule_ids.add(trace.rule_id)

        for child in trace.children:
            RuleConsistency._collect_trace_counts(
                child,
                statistics,
                counted_rule_ids,
            )
