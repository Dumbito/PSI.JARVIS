from dataclasses import dataclass

from psi_jarvis.domain.screening.rules.logical import (
    AllOfRule,
    AnyOfRule,
    NotRule,
    ScreeningRule,
)
from psi_jarvis.domain.screening.rules.trace import RuleTrace


@dataclass(frozen=True)
class RuleEvaluation:
    matched: bool
    matched_rule_ids: tuple[str, ...] = ()
    failed_rule_ids: tuple[str, ...] = ()
    trace: RuleTrace | None = None


def evaluate_rule(rule: ScreeningRule, text: str) -> RuleEvaluation:
    if isinstance(rule, AllOfRule):
        evaluations = tuple(evaluate_rule(child, text) for child in rule.rules)
        matched = all(evaluation.matched for evaluation in evaluations)
        matched_ids = tuple(
            child.id
            for child, evaluation in zip(rule.rules, evaluations)
            if evaluation.matched
        )
        failed_ids = tuple(
            child.id
            for child, evaluation in zip(rule.rules, evaluations)
            if not evaluation.matched
        )
        return RuleEvaluation(
            matched=matched,
            matched_rule_ids=matched_ids,
            failed_rule_ids=failed_ids,
            trace=RuleTrace(
                rule_id=rule.id,
                kind=rule.kind,
                matched=matched,
                children=tuple(
                    evaluation.trace
                    for evaluation in evaluations
                    if evaluation.trace is not None
                ),
            ),
        )

    if isinstance(rule, AnyOfRule):
        evaluations = tuple(evaluate_rule(child, text) for child in rule.rules)
        matched = any(evaluation.matched for evaluation in evaluations)
        matched_ids = tuple(
            child.id
            for child, evaluation in zip(rule.rules, evaluations)
            if evaluation.matched
        )
        failed_ids = tuple(
            child.id
            for child, evaluation in zip(rule.rules, evaluations)
            if not evaluation.matched
        )
        return RuleEvaluation(
            matched=matched,
            matched_rule_ids=matched_ids,
            failed_rule_ids=failed_ids,
            trace=RuleTrace(
                rule_id=rule.id,
                kind=rule.kind,
                matched=matched,
                children=tuple(
                    evaluation.trace
                    for evaluation in evaluations
                    if evaluation.trace is not None
                ),
            ),
        )

    if isinstance(rule, NotRule):
        evaluation = evaluate_rule(rule.rule, text)
        matched = not evaluation.matched
        return RuleEvaluation(
            matched=matched,
            matched_rule_ids=(rule.id,) if matched else (),
            failed_rule_ids=(rule.id,) if not matched else (),
            trace=RuleTrace(
                rule_id=rule.id,
                kind=rule.kind,
                matched=matched,
                children=((evaluation.trace,) if evaluation.trace is not None else ()),
            ),
        )

    matched = rule.matches(text)
    return RuleEvaluation(
        matched=matched,
        matched_rule_ids=(rule.id,) if matched else (),
        failed_rule_ids=(rule.id,) if not matched else (),
        trace=RuleTrace(
            rule_id=rule.id,
            kind=rule.kind,
            matched=matched,
        ),
    )
