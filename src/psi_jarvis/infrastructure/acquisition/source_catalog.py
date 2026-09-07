from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BibliographicSourceDefinition:
    """Identidad estable de una fuente bibliográfica remota."""

    key: str
    display_name: str

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Bibliographic source key cannot be empty")
        if not self.display_name.strip():
            raise ValueError("Bibliographic source display name cannot be empty")


PUBMED = BibliographicSourceDefinition("pubmed", "PubMed")
SCOPUS = BibliographicSourceDefinition("scopus", "Scopus")
WEB_OF_SCIENCE = BibliographicSourceDefinition("web_of_science", "Web of Science")
ZOTERO = BibliographicSourceDefinition("zotero", "Zotero")

PLANNED_REMOTE_SOURCES: tuple[BibliographicSourceDefinition, ...] = (
    PUBMED,
    SCOPUS,
    WEB_OF_SCIENCE,
    ZOTERO,
)


def source_definition(source_key: str) -> BibliographicSourceDefinition:
    """Resuelve la definición de una fuente por su clave estable."""

    for source in PLANNED_REMOTE_SOURCES:
        if source.key == source_key:
            return source
    raise KeyError(f"Unknown planned bibliographic source: {source_key}")
