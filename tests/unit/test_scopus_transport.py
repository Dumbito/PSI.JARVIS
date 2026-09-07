from urllib.parse import parse_qs, urlsplit

import pytest

from psi_jarvis.application.acquisition import BibliographicQuery
from psi_jarvis.infrastructure.acquisition.scopus_transport import (
    MAX_SCOPUS_COUNT,
    ScopusSearchTransport,
    ScopusTransportConfig,
)


SEARCH_JSON = '{"search-results":{"opensearch:totalResults":"1","opensearch:startIndex":"0","opensearch:itemsPerPage":"1","entry":[{"dc:identifier":"SCOPUS_ID:123"}]}}'


class FakeResponse:
    def __init__(self, content: str, status: int = 200):
        self.status = status
        self._content = content.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._content


def test_scopus_transport_builds_get_request_with_api_key_in_header():
    calls = []

    def opener(request, timeout):
        calls.append((request, timeout))
        return FakeResponse(SEARCH_JSON)

    transport = ScopusSearchTransport(
        ScopusTransportConfig(api_key="secret-key", insttoken="institution-token", count=10),
        opener=opener,
    )

    result = transport.fetch(
        BibliographicQuery(
            text="TITLE-ABS-KEY(working memory)",
            parameters=(("view", "STANDARD"), ("start", "10"), ("sort", "-coverDate")),
        )
    )

    assert result.raw_content == SEARCH_JSON
    assert len(calls) == 1

    request, timeout = calls[0]
    params = parse_qs(urlsplit(request.full_url).query)

    assert request.method == "GET"
    assert timeout == 20.0
    assert request.get_header("Accept") == "application/json"
    assert request.get_header("X-els-apikey") == "secret-key"
    assert request.get_header("X-els-insttoken") == "institution-token"
    assert params["query"] == ["TITLE-ABS-KEY(working memory)"]
    assert params["count"] == ["10"]
    assert params["start"] == ["10"]
    assert params["view"] == ["STANDARD"]
    assert params["sort"] == ["-coverDate"]
    assert params["httpAccept"] == ["application/json"]
    assert "secret-key" not in result.source_locator
    assert "institution-token" not in result.source_locator


def test_scopus_transport_supports_oauth_bearer_token():
    calls = []

    def opener(request, timeout):
        calls.append(request)
        return FakeResponse(SEARCH_JSON)

    ScopusSearchTransport(
        ScopusTransportConfig(api_key="secret-key", auth_token="oauth-token"),
        opener=opener,
    ).fetch(BibliographicQuery(text="memory"))

    request = calls[0]
    assert request.get_header("Authorization") == "Bearer oauth-token"
    assert request.get_header("X-els-apikey") == "secret-key"


def test_scopus_transport_defaults_to_json_and_configured_count():
    calls = []

    def opener(request, timeout):
        calls.append(request)
        return FakeResponse(SEARCH_JSON)

    ScopusSearchTransport(
        ScopusTransportConfig(api_key="secret-key", count=25),
        opener=opener,
    ).fetch(BibliographicQuery(text="memory"))

    params = parse_qs(urlsplit(calls[0].full_url).query)
    assert params["httpAccept"] == ["application/json"]
    assert params["count"] == ["25"]
    assert params["query"] == ["memory"]


def test_scopus_transport_rejects_transport_owned_count_parameter():
    transport = ScopusSearchTransport(
        ScopusTransportConfig(api_key="secret-key"),
        opener=lambda request, timeout: pytest.fail("transport must not be called"),
    )

    with pytest.raises(ValueError, match="count is controlled by transport configuration"):
        transport.fetch(BibliographicQuery(text="memory", parameters=(("count", "50"),)))


def test_scopus_transport_rejects_unsupported_query_parameter():
    transport = ScopusSearchTransport(
        ScopusTransportConfig(api_key="secret-key"),
        opener=lambda request, timeout: pytest.fail("transport must not be called"),
    )

    with pytest.raises(ValueError, match="Unsupported Scopus Search parameter"):
        transport.fetch(BibliographicQuery(text="memory", parameters=(("apiKey", "oops"),)))


def test_scopus_transport_validates_start_as_non_negative_integer():
    transport = ScopusSearchTransport(
        ScopusTransportConfig(api_key="secret-key"),
        opener=lambda request, timeout: pytest.fail("transport must not be called"),
    )

    with pytest.raises(ValueError, match="non-negative integer"):
        transport.fetch(BibliographicQuery(text="memory", parameters=(("start", "invalid"),)))

    with pytest.raises(ValueError, match="non-negative integer"):
        transport.fetch(BibliographicQuery(text="memory", parameters=(("start", "-1"),)))


def test_scopus_transport_validates_configuration():
    with pytest.raises(ValueError, match="API key"):
        ScopusTransportConfig(api_key="")

    with pytest.raises(ValueError, match="institution token"):
        ScopusTransportConfig(api_key="secret-key", insttoken="")

    with pytest.raises(ValueError, match="authentication token"):
        ScopusTransportConfig(api_key="secret-key", auth_token="")

    with pytest.raises(ValueError, match="timeout"):
        ScopusTransportConfig(api_key="secret-key", timeout_seconds=0)

    with pytest.raises(ValueError, match="count"):
        ScopusTransportConfig(api_key="secret-key", count=0)

    with pytest.raises(ValueError, match="count"):
        ScopusTransportConfig(api_key="secret-key", count=MAX_SCOPUS_COUNT + 1)


def test_scopus_transport_rejects_non_json_success_payload():
    transport = ScopusSearchTransport(
        ScopusTransportConfig(api_key="secret-key"),
        opener=lambda request, timeout: FakeResponse("<not-json />"),
    )

    with pytest.raises(RuntimeError, match="Invalid Scopus Search JSON"):
        transport.fetch(BibliographicQuery(text="memory"))


def test_scopus_transport_propagates_non_200_status():
    transport = ScopusSearchTransport(
        ScopusTransportConfig(api_key="secret-key"),
        opener=lambda request, timeout: FakeResponse("quota", status=429),
    )

    with pytest.raises(RuntimeError, match="HTTP 429"):
        transport.fetch(BibliographicQuery(text="memory"))
