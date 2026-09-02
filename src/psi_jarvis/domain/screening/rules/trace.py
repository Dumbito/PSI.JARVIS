from dataclasses import dataclass


@dataclass(frozen=True)
class RuleTrace:
    rule_id: str
    kind: str
    matched: bool
    children: tuple["RuleTrace", ...] = ()
