import pytest

from psi_jarvis.infrastructure.connections.source_connections import (
    CredentialMethod,
    SourceConnectionDefinition,
    SourceConnectionRegistry,
    SourceConnectionState,
    SourceConnectionStatus,
)


def test_registry_inspects_and_sorts_sources():
    registry = SourceConnectionRegistry()
    scopus = SourceConnectionDefinition(
        key="scopus",
        display_name="Scopus",
        requires_auth=True,
        credential_methods=(CredentialMethod.API_KEY, CredentialMethod.OAUTH),
    )
    pubmed = SourceConnectionDefinition(
        key="pubmed",
        display_name="PubMed",
        requires_auth=False,
    )

    registry.register(
        scopus,
        lambda: SourceConnectionState(scopus, SourceConnectionStatus.AUTH_REQUIRED),
    )
    registry.register(
        pubmed,
        lambda: SourceConnectionState(pubmed, SourceConnectionStatus.AVAILABLE),
    )

    assert registry.sources() == ("pubmed", "scopus")
    assert registry.inspect("scopus").status is SourceConnectionStatus.AUTH_REQUIRED
    assert tuple(state.source.key for state in registry.inspect_all()) == ("pubmed", "scopus")


def test_registry_rejects_duplicate_source():
    registry = SourceConnectionRegistry()
    definition = SourceConnectionDefinition("pubmed", "PubMed", False)
    inspector = lambda: SourceConnectionState(definition, SourceConnectionStatus.AVAILABLE)
    registry.register(definition, inspector)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(definition, inspector)


def test_registry_rejects_unknown_source():
    registry = SourceConnectionRegistry()

    with pytest.raises(KeyError, match="Unknown source connection"):
        registry.inspect("scopus")
