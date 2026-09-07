import pytest

from psi_jarvis.infrastructure.acquisition.source_catalog import (
    PLANNED_REMOTE_SOURCES,
    PUBMED,
    SCOPUS,
    WEB_OF_SCIENCE,
    ZOTERO,
    BibliographicSourceDefinition,
    source_definition,
)


def test_planned_remote_sources_have_unique_stable_keys():
    keys = tuple(source.key for source in PLANNED_REMOTE_SOURCES)

    assert keys == ("pubmed", "scopus", "web_of_science", "zotero")
    assert len(keys) == len(set(keys))


def test_planned_remote_sources_have_expected_display_names():
    assert PUBMED.display_name == "PubMed"
    assert SCOPUS.display_name == "Scopus"
    assert WEB_OF_SCIENCE.display_name == "Web of Science"
    assert ZOTERO.display_name == "Zotero"


def test_source_definition_resolves_planned_source_by_key():
    assert source_definition("pubmed") is PUBMED
    assert source_definition("scopus") is SCOPUS
    assert source_definition("web_of_science") is WEB_OF_SCIENCE
    assert source_definition("zotero") is ZOTERO


def test_source_definition_rejects_unknown_key():
    with pytest.raises(KeyError, match="Unknown planned bibliographic source"):
        source_definition("unknown")


def test_source_definition_validates_identity():
    with pytest.raises(ValueError, match="key cannot be empty"):
        BibliographicSourceDefinition("", "PubMed")

    with pytest.raises(ValueError, match="display name cannot be empty"):
        BibliographicSourceDefinition("pubmed", "")
