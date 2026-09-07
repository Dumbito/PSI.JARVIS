from urllib.parse import parse_qs, urlsplit

import pytest

from psi_jarvis.application.acquisition import BibliographicQuery
from psi_jarvis.infrastructure.acquisition.zotero_transport import ZoteroTransportConfig, ZoteroWebApiTransport


class FakeResponse:
    status = 200
    def __init__(self, content): self._content = content.encode()
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def read(self): return self._content


def test_zotero_transport_builds_v3_authenticated_request():
    calls = []
    payload = "[]"
    def opener(request, timeout):
        calls.append((request, timeout))
        return FakeResponse(payload)
    transport = ZoteroWebApiTransport(ZoteroTransportConfig(user_id="12345", api_key="key", limit=25), opener=opener)
    result = transport.fetch(BibliographicQuery(text="memory", parameters=(("sort", "dateAdded"), ("direction", "desc"), ("start", "25"))))
    assert result.raw_content == payload
    request, timeout = calls[0]
    params = parse_qs(urlsplit(request.full_url).query)
    assert request.method == "GET"
    assert request.headers["Zotero-api-version"] == "3"
    assert request.headers["Zotero-api-key"] == "key"
    assert "/users/12345/items" in request.full_url
    assert params["q"] == ["memory"]
    assert params["limit"] == ["25"]
    assert params["start"] == ["25"]
    assert timeout == 20.0
    assert "key" not in result.source_locator


def test_zotero_transport_rejects_unsupported_parameter():
    transport = ZoteroWebApiTransport(ZoteroTransportConfig(user_id="12345", api_key="key"), opener=lambda request, timeout: pytest.fail("must not call"))
    with pytest.raises(ValueError, match="Unsupported Zotero parameter"):
        transport.fetch(BibliographicQuery(text="memory", parameters=(("unknown", "x"),)))


def test_zotero_transport_rejects_invalid_json():
    transport = ZoteroWebApiTransport(ZoteroTransportConfig(user_id="12345", api_key="key"), opener=lambda request, timeout: FakeResponse("broken"))
    with pytest.raises(RuntimeError, match="Invalid Zotero JSON"):
        transport.fetch(BibliographicQuery(text="memory"))
