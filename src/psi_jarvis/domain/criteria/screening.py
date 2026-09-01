from dataclasses import dataclass


@dataclass(frozen=True)
class ScreeningCriteria:
    """Define los criterios de inclusión y exclusión de una revisión."""

    topic: str
    inclusion: tuple[str, ...] = ()
    exclusion: tuple[str, ...] = ()
