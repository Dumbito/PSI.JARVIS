from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Paper:
    """Representa un artículo científico dentro de PSI.JARVIS."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    authors: tuple[str, ...] = ()
    abstract: str | None = None
    doi: str | None = None
    pmid: str | None = None
    publication_year: int | None = None
    journal: str | None = None
