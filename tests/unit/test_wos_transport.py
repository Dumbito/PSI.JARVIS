from urllib.parse import parse_qs, urlsplit

import pytest

from psi_jarvis.application.acquisition import BibliographicQuery
from psi_jarvis.infrastructure.acquisition.wos_transport import WebOfScienceStarterTransport, WebOfScienceTransportConfig


class FakeResponse:
    status = 200
    def __init__(self, content): self._content = content.encode()
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def read(self): return self._content


def test_wos_transport_builds_authenticated_query():
    calls = []
    payload = '{"hits":[]}'
    def opener(request, timeout):
        calls.append((request, timeout))
        return FakeResponse(payload)
    transport = WebOfScienceStarterTransport(WebOfScienceTransportConfig(api_key="key", limit=10), opener=opener)
    result = transport.fetch(BibliographicQuery(text="TS=memory", parameters=(("page", "2"), ("sortField", "PY+D"))))
    assert result.raw_content == payload
    request, timeout = calls[0]
    params = parse_qs(urlsplit(request.full_url).query)
    assert request.method == "GET"
    assert request.headers["X-apikey"] == "key"
    assert params["db"] == ["WOS"]
    assert params["q"] == ["TS=memory"]
    assert params["limit"] == ["10"]
    assert params["page"] == ["2"]
    assert params["sortField"] == ["PY+D"]
    assert timeout == 20.0


def test_wos_transport_rejects_bad_parameters():
    transport = WebOfScienceStarterTransport(WebOfScienceTransportConfig(api_key="key"), opener=lambda request, timeout: pytest.fail("must not call"))
    with pytest.raises(ValueError, match="Unsupported Web of Science parameter"):
        transport.fetch(BibliographicQuery(text="memory", parameters=(("unknown", "x"),)))


def test_wos_transport_rejects_invalid_json():
    transport = WebOfScienceStarterTransport(WebOfScienceTransportConfig(api_key="key"), opener=lambda request, timeout: FakeResponse("broken"))
    with pytest.raises(RuntimeError, match="Invalid Web of Science JSON"):
        transport.fetch(BibliographicQuery(text="memory"))
