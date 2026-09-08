from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIAssistanceRequest:
    """Immutable input envelope for future auxiliary AI/NLP providers."""

    paper_id: str
    title: str
    abstract: str
    model: str
    prompt_version: str
    input_hash: str

    def __post_init__(self) -> None:
        for name, value in (
            ("paper_id", self.paper_id),
            ("model", self.model),
            ("prompt_version", self.prompt_version),
            ("input_hash", self.input_hash),
        ):
            if not value.strip():
                raise ValueError(f"{name} cannot be empty")


@dataclass(frozen=True)
class AIAssistanceSuggestion:
    """Auditable AI output that is deliberately not a screening decision."""

    paper_id: str
    model: str
    prompt_version: str
    input_hash: str
    output: str
    confidence: float | None = None

    @property
    def authority(self) -> str:
        """Fixed authority label preventing accidental scientific authority."""
        return "assistant-only"

    def __post_init__(self) -> None:
        for name, value in (
            ("paper_id", self.paper_id),
            ("model", self.model),
            ("prompt_version", self.prompt_version),
            ("input_hash", self.input_hash),
            ("output", self.output),
        ):
            if not value.strip():
                raise ValueError(f"{name} cannot be empty")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("AI suggestion confidence must be between 0 and 1")

    def as_scientific_decision(self) -> None:
        """Explicitly reject attempts to promote an assistant output to a decision."""
        raise RuntimeError(
            "AI/NLP suggestions are auxiliary evidence and cannot become scientific screening decisions"
        )
