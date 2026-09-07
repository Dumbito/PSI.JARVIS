from datetime import datetime, timezone
from pathlib import Path

from psi_jarvis.infrastructure.acquisition.scopus_transport import ScopusTransportConfig
from psi_jarvis.infrastructure.auth.scopus_connection import (
    ScopusConnectionManager,
    ScopusConnectionStatus,
)
from psi_jarvis.infrastructure.auth.scopus_oauth import (
    JsonTokenStore,
    ScopusOAuthConfig,
    ScopusOAuthToken,
)


def config() -> ScopusOAuthConfig:
    return ScopusOAuthConfig(
        client_id="client-123",
        authorization_endpoint="https://auth.example.test/authorize",
        token_endpoint="https://auth.example.test/token",
    )


def test_unconfigured_connection_is_reported():
    manager = ScopusConnectionManager(None, JsonTokenStore(Path("/tmp/psi-jarvis-test-scopus.json")))

    connection = manager.inspect()

    assert connection.status is ScopusConnectionStatus.UNCONFIGURED


def test_missing_token_is_disconnected(tmp_path: Path):
    manager = ScopusConnectionManager(config(), JsonTokenStore(tmp_path / "scopus.json"))

    assert manager.inspect().status is ScopusConnectionStatus.DISCONNECTED


def test_valid_token_is_connected(tmp_path: Path):
    store = JsonTokenStore(tmp_path / "scopus.json")
    store.save(ScopusOAuthToken(access_token="access-123"))
    manager = ScopusConnectionManager(config(), store)

    connection = manager.inspect()

    assert connection.status is ScopusConnectionStatus.CONNECTED
    assert connection.token is not None
    assert connection.token.access_token == "access-123"


def test_expired_token_is_reported(tmp_path: Path):
    store = JsonTokenStore(tmp_path / "scopus.json")
    store.save(
        ScopusOAuthToken(
            access_token="access-123",
            expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
    )
    manager = ScopusConnectionManager(config(), store)

    assert manager.inspect().status is ScopusConnectionStatus.EXPIRED


def test_apply_token_returns_transport_config_with_oauth_access_token(tmp_path: Path):
    store = JsonTokenStore(tmp_path / "scopus.json")
    store.save(ScopusOAuthToken(access_token="access-123"))
    manager = ScopusConnectionManager(config(), store)
    transport_config = ScopusTransportConfig(api_key="api-key", count=10)

    configured = manager.apply_token(transport_config)

    assert configured.api_key == "api-key"
    assert configured.auth_token == "access-123"
    assert configured.count == 10


def test_apply_token_rejects_missing_connection(tmp_path: Path):
    manager = ScopusConnectionManager(config(), JsonTokenStore(tmp_path / "scopus.json"))

    try:
        manager.apply_token(ScopusTransportConfig(api_key="api-key"))
    except RuntimeError as exc:
        assert str(exc) == "Scopus is not connected"
    else:
        raise AssertionError("Expected RuntimeError")


def test_logout_removes_persisted_token(tmp_path: Path):
    store = JsonTokenStore(tmp_path / "scopus.json")
    store.save(ScopusOAuthToken(access_token="access-123"))
    manager = ScopusConnectionManager(config(), store)

    manager.logout()

    assert manager.inspect().status is ScopusConnectionStatus.DISCONNECTED
