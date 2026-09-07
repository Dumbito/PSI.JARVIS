import pytest

from psi_jarvis.infrastructure.auth.scopus_config import load_scopus_environment


def test_load_scopus_environment_without_variables(monkeypatch):
    for name in tuple(key for key in __import__('os').environ if key.startswith('PSI_SCOPUS_')):
        monkeypatch.delenv(name, raising=False)

    config = load_scopus_environment()

    assert config.api_key is None
    assert config.transport is None
    assert config.oauth is None


def test_load_scopus_environment_builds_transport_and_oauth(monkeypatch):
    monkeypatch.setenv('PSI_SCOPUS_API_KEY', 'api-key')
    monkeypatch.setenv('PSI_SCOPUS_INSTTOKEN', 'inst-token')
    monkeypatch.setenv('PSI_SCOPUS_COUNT', '10')
    monkeypatch.setenv('PSI_SCOPUS_TIMEOUT', '15')
    monkeypatch.setenv('PSI_SCOPUS_CLIENT_ID', 'client-id')
    monkeypatch.setenv('PSI_SCOPUS_CLIENT_SECRET', 'client-secret')
    monkeypatch.setenv('PSI_SCOPUS_AUTHORIZATION_ENDPOINT', 'https://example.test/authorize')
    monkeypatch.setenv('PSI_SCOPUS_TOKEN_ENDPOINT', 'https://example.test/token')
    monkeypatch.setenv('PSI_SCOPUS_SCOPES', 'scope-a scope-b')
    monkeypatch.setenv('PSI_SCOPUS_REDIRECT_PORT', '8765')

    config = load_scopus_environment()

    assert config.api_key == 'api-key'
    assert config.transport is not None
    assert config.transport.api_key == 'api-key'
    assert config.transport.insttoken == 'inst-token'
    assert config.transport.count == 10
    assert config.transport.timeout_seconds == 15.0
    assert config.oauth is not None
    assert config.oauth.client_id == 'client-id'
    assert config.oauth.client_secret == 'client-secret'
    assert config.oauth.scopes == ('scope-a', 'scope-b')
    assert config.oauth.redirect_port == 8765


def test_load_scopus_environment_rejects_partial_oauth_configuration(monkeypatch):
    monkeypatch.setenv('PSI_SCOPUS_CLIENT_ID', 'client-id')
    monkeypatch.delenv('PSI_SCOPUS_AUTHORIZATION_ENDPOINT', raising=False)
    monkeypatch.delenv('PSI_SCOPUS_TOKEN_ENDPOINT', raising=False)

    with pytest.raises(ValueError, match='PSI_SCOPUS_AUTHORIZATION_ENDPOINT'):
        load_scopus_environment()
