from dataclasses import dataclass


@dataclass(frozen=True)
class ScreeningDecision:
    """Representa la decisión de inclusión o exclusión de un paper."""

    included: bool
    reason: str

    @classmethod
    def include(cls, reason: str) -> "ScreeningDecision":
        """Crea una decisión de inclusión."""
        return cls(
            included=True,
            reason=reason,
        )

    @classmethod
    def exclude(cls, reason: str) -> "ScreeningDecision":
        """Crea una decisión de exclusión."""
        return cls(
            included=False,
            reason=reason,
        )
