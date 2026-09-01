from dataclasses import dataclass


@dataclass(frozen=True)
class TextRule:
    """Regla de cribado basada en la presencia de un texto."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("TextRule value cannot be empty")

    @property
    def kind(self) -> str:
        return "text"

    @property
    def id(self) -> str:
        return f"text:{self.value.strip().lower()}"

    def matches(self, text: str) -> bool:
        return self.value.lower() in text.lower()
