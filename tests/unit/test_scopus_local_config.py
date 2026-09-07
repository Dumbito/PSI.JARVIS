from pathlib import Path

from psi_jarvis.infrastructure.auth.scopus_local_config import (
    ScopusLocalConfig,
    ScopusLocalConfigStore,
)


def test_local_config_round_trip_and_permissions(tmp_path: Path):
    path = tmp_path / "connections" / "scopus_config.json"
    store = ScopusLocalConfigStore(path)
    config = ScopusLocalConfig(
        api_key="secret-api-key",
        insttoken="institution-token",
        client_id="client-123",
        client_secret="client-secret",
        authorization_endpoint="https://auth.example.test/authorize",
        token_endpoint="https://auth.example.test/token",
        scopes=("scopus.read",),
    )

    store.save(config)
    loaded = store.load()

    assert loaded == config
    assert path.stat().st_mode & 0o777 == 0o600


def test_local_config_delete(tmp_path: Path):
    path = tmp_path / "scopus_config.json"
    store = ScopusLocalConfigStore(path)
    store.save(ScopusLocalConfig(api_key="secret-api-key"))

    store.delete()

    assert store.load() is None
