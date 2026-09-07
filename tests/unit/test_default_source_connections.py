from pathlib import Path

from psi_jarvis.infrastructure.auth.scopus_connection import ScopusConnectionManager
from psi_jarvis.infrastructure.auth.scopus_oauth import JsonTokenStore
from psi_jarvis.infrastructure.connections.default_sources import (
    build_default_source_connection_registry,
)
from psi_jarvis.infrastructure.connections.source_connections import (
    CredentialMethod,
    SourceConnectionStatus,
)


def test_default_registry_marks_public_and_unconfigured_sources_correctly(tmp_path: Path):
    manager = ScopusConnectionManager(None, JsonTokenStore(tmp_path / "scopus.json"))
    registry = build_default_source_connection_registry(manager)

    assert registry.sources() == ("pubmed", "scopus", "web_of_science", "zotero")
    assert registry.inspect("pubmed").status is SourceConnectionStatus.AVAILABLE
    assert registry.inspect("pubmed").credential_method is CredentialMethod.NONE
    assert registry.inspect("scopus").status is SourceConnectionStatus.UNAVAILABLE
    assert registry.inspect("web_of_science").status is SourceConnectionStatus.UNAVAILABLE
    assert registry.inspect("zotero").status is SourceConnectionStatus.UNAVAILABLE


def test_default_registry_exposes_scopus_auth_required_when_oauth_is_configured(tmp_path: Path):
    from psi_jarvis.infrastructure.auth.scopus_oauth import ScopusOAuthConfig

    manager = ScopusConnectionManager(
        ScopusOAuthConfig(
            client_id="client",
            authorization_endpoint="https://example.test/authorize",
            token_endpoint="https://example.test/token",
        ),
        JsonTokenStore(tmp_path / "scopus.json"),
    )

    state = build_default_source_connection_registry(manager).inspect("scopus")

    assert state.status is SourceConnectionStatus.AUTH_REQUIRED
    assert state.source.key == "scopus"
