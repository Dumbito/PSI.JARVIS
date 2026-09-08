from dataclasses import dataclass
from typing import Protocol


class ScreeningRule(Protocol):
    @property
    def id(self) -> str: ...

    def matches(self, text: str) -> bool: ...


@dataclass(frozen=True)
class AllOfRule:
    rules: tuple[ScreeningRule, ...]

    @property
    def kind(self) -> str:
        return "and"

    @property
    def id(self) -> str:
        return "and:(" + ",".join(rule.id for rule in self.rules) + ")"

    def matches(self, text: str) -> bool:
        return all(rule.matches(text) for rule in self.rules)


@dataclass(frozen=True)
class AnyOfRule:
    rules: tuple[ScreeningRule, ...]

    @property
    def kind(self) -> str:
        return "or"

    @property
    def id(self) -> str:
        return "or:(" + ",".join(rule.id for rule in self.rules) + ")"

    def matches(self, text: str) -> bool:
        return any(rule.matches(text) for rule in self.rules)


@dataclass(frozen=True)
class NotRule:
    rule: ScreeningRule

    @property
    def kind(self) -> str:
        return "not"

    @property
    def id(self) -> str:
        return f"not:({self.rule.id})"

    def matches(self, text: str) -> bool:
        return not self.rule.matches(text)
