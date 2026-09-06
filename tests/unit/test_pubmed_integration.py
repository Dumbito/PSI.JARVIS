from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from psi_jarvis.application.acquisition import BibliographicQuery
from psi_jarvis.infrastructure.acquisition import (
    PubMedTransportConfig,
    build_pubmed_adapter,
)


FIXED_TIME = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)
FIXTURE = Path(__file__).parents[1] / "fixtures" / "pubmed_records.xml"

SEARCH_XML = """
<eSearchResult>
  <Count>2</Count>
  <RetMax>2</RetMax>
  <RetStart>0</RetStart>
  <IdList>
    <Id>12345678</Id>
    <Id>87654321</Id>
  </IdList>
</eSearchResult>
""".strip()


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


def test_build_pubmed_adapter_composes_transport_and_mapper_without_network():
    calls = []

    def opener(request, timeout):
        calls.append((request, timeout))
        endpoint = urlsplit(request.full_url).path.rsplit("/", 1)[-1]
        content = SEARCH_XML if endpoint == "esearch.fcgi" else FIXTURE.read_text(encoding="utf-8")
        return FakeResponse(content)

    adapter = build_pubmed_adapter(
        PubMedTransportConfig(
            tool="psi_jarvis",
            email="researcher@example.org",
            api_key="secret-key",
            retmax=2,
        ),
        clock=lambda: FIXED_TIME,
        opener=opener,
    )

    result = adapter.acquire(BibliographicQuery(text="working memory"))

    assert result.success is True
    assert result.receipt is not None
    assert result.receipt.source_key == "pubmed"
    assert result.receipt.adapter_key == "pubmed-efetch"
    assert result.receipt.adapter_version == "1"
    assert result.receipt.acquired_at == FIXED_TIME
    assert result.receipt.request_json == '{"parameters":{},"text":"working memory"}'
    assert result.receipt.source_locator is not None
    assert "efetch.fcgi" in result.receipt.source_locator
    assert "api_key" not in result.receipt.source_locator
    assert "email" not in result.receipt.source_locator
    assert "tool" not in result.receipt.source_locator
    assert len(result.papers) == 2
    assert [paper.pmid for paper in result.papers] == ["12345678", "87654321"]
    assert [provenance.source_record_id for paper in result.papers for provenance in paper.provenances] == [
        "12345678",
        "87654321",
    ]
    assert len(calls) == 2
