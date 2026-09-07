from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from psi_jarvis.infrastructure.auth.scopus_oauth import (
    JsonTokenStore,
    ScopusOAuthClient,
    ScopusOAuthConfig,
    ScopusOAuthToken,
)


CONFIG = ScopusOAuthConfig(
    client_id="client-123",
    authorization_endpoint="https://auth.example.test/authorize",
    token_endpoint="https://auth.example.test/token",
    scopes=("scopus.read",),
)


def test_authorization_request_contains_state_and_pkce():
    request = ScopusOAuthClient(CONFIG).prepare_authorization()
    params = parse_qs(urlparse(request.authorization_url).query)

    assert params["response_type"] == ["code"]
    assert params["client_id"] == ["client-123"]
    assert params["scope"] == ["scopus.read"]
    assert params["state"] == [request.state]
    assert params["code_challenge_method"] == ["S256"]
    assert params["code_challenge"][0]
    assert len(request.code_verifier) >= 43


def test_exchange_code_posts_form_data_and_builds_token():
    calls = []

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return (
                b'{"access_token":"access-123","token_type":"Bearer",'
                b'"expires_in":3600,"refresh_token":"refresh-123","scope":"scopus.read"}'
            )

    def opener(request, timeout):
        calls.append((request, timeout))
        return FakeResponse()

    client = ScopusOAuthClient(CONFIG, opener=opener)
    authorization = client.prepare_authorization()
    token = client.exchange_code("code-456", authorization)

    assert token.access_token == "access-123"
    assert token.refresh_token == "refresh-123"
    assert token.scope == "scopus.read"
    assert token.expires_at is not None
    assert len(calls) == 1
    request, timeout = calls[0]
    assert request.method == "POST"
    assert timeout == 20.0
    body = parse_qs(request.data.decode("utf-8"))
    assert body["grant_type"] == ["authorization_code"]
    assert body["code"] == ["code-456"]
    assert body["client_id"] == ["client-123"]
    assert body["code_verifier"] == [authorization.code_verifier]
    assert body["redirect_uri"] == [authorization.redirect_uri]


def test_exchange_code_includes_client_secret_when_configured():
    captured = []

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"access_token":"access-123"}'

    def opener(request, timeout):
        captured.append(parse_qs(request.data.decode("utf-8")))
        return FakeResponse()

    config = ScopusOAuthConfig(
        client_id="client-123",
        client_secret="secret-456",
        authorization_endpoint="https://auth.example.test/authorize",
        token_endpoint="https://auth.example.test/token",
    )
    client = ScopusOAuthClient(config, opener=opener)
    authorization = client.prepare_authorization()

    client.exchange_code("code-456", authorization)

    assert captured[0]["client_secret"] == ["secret-456"]


def test_invalid_token_response_is_rejected():
    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"token_type":"Bearer"}'

    client = ScopusOAuthClient(CONFIG, opener=lambda request, timeout: FakeResponse())
    authorization = client.prepare_authorization()

    with pytest.raises(RuntimeError, match="no access_token"):
        client.exchange_code("code-456", authorization)


def test_token_store_round_trip_and_permissions(tmp_path: Path):
    path = tmp_path / "connections" / "scopus.json"
    store = JsonTokenStore(path)
    token = ScopusOAuthToken(
        access_token="access-123",
        expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
        refresh_token="refresh-123",
        scope="scopus.read",
    )

    store.save(token)
    loaded = store.load()

    assert loaded == token
    assert path.stat().st_mode & 0o777 == 0o600


def test_token_store_delete(tmp_path: Path):
    store = JsonTokenStore(tmp_path / "scopus.json")
    store.save(ScopusOAuthToken(access_token="access-123"))

    store.delete()

    assert store.load() is None


def test_expired_token_is_detected():
    token = ScopusOAuthToken(
        access_token="access-123",
        expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )

    assert token.is_expired is True


def test_oauth_config_validates_required_fields():
    with pytest.raises(ValueError, match="client_id"):
        ScopusOAuthConfig(
            client_id="",
            authorization_endpoint="https://auth.example.test/authorize",
            token_endpoint="https://auth.example.test/token",
        )

    with pytest.raises(ValueError, match="redirect port"):
        ScopusOAuthConfig(
            client_id="client-123",
            authorization_endpoint="https://auth.example.test/authorize",
            token_endpoint="https://auth.example.test/token",
            redirect_port=70000,
        )
