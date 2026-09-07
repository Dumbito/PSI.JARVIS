from pathlib import Path

from psi_jarvis.infrastructure.acquisition.scopus_transport import ScopusTransportConfig
from psi_jarvis.infrastructure.auth.scopus_connection import (
    ScopusConnectionManager,
    ScopusConnectionStatus,
)
from psi_jarvis.infrastructure.auth.scopus_oauth import JsonTokenStore
from psi_jarvis.infrastructure.connections.source_connections import SourceConnectionStatus
from psi_jarvis.infrastructure.connections.default_sources import build_default_source_connection_registry


def test_api_key_only_connection_is_configured(tmp_path: Path):
    transport = ScopusTransportConfig(api_key="api-key")
    manager = ScopusConnectionManager(
        None,
        JsonTokenStore(tmp_path / "scopus.json"),
        transport_config=transport,
    )

    connection = manager.inspect()

    assert connection.status is ScopusConnectionStatus.CONFIGURED
    assert connection.transport_config == transport
    assert manager.apply_token().api_key == "api-key"


def test_default_source_registry_reports_configured_scopus(tmp_path: Path):
    transport = ScopusTransportConfig(api_key="api-key", insttoken="inst-token")
    manager = ScopusConnectionManager(
        None,
        JsonTokenStore(tmp_path / "scopus.json"),
        transport_config=transport,
    )

    state = build_default_source_connection_registry(manager).inspect("scopus")

    assert state.status is SourceConnectionStatus.CONFIGURED
    assert state.credential_method.value == "institutional_token"
