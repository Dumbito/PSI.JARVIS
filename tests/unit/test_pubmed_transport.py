from urllib.parse import parse_qs, urlsplit

import pytest

from psi_jarvis.application.acquisition import BibliographicQuery
from psi_jarvis.infrastructure.acquisition.pubmed_transport import (
    PubMedEUtilsTransport,
    PubMedTransportConfig,
)


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

FETCH_XML = """
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>Transport Integration Study</ArticleTitle>
        <Journal><Title>Journal of Integration</Title></Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
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


def test_pubmed_transport_runs_esearch_then_efetch_with_expected_parameters():
    calls = []

    def opener(request, timeout):
        calls.append((request, timeout))
        endpoint = urlsplit(request.full_url).path.rsplit("/", 1)[-1]
        return FakeResponse(SEARCH_XML if endpoint == "esearch.fcgi" else FETCH_XML)

    transport = PubMedEUtilsTransport(
        PubMedTransportConfig(
            tool="psi_jarvis",
            email="researcher@example.org",
            api_key="secret-key",
            retmax=2,
        ),
        opener=opener,
    )

    result = transport.fetch(BibliographicQuery(text="working memory", parameters=(("sort", "pub_date"),)))

    assert result.raw_content == FETCH_XML
    assert len(calls) == 2
    assert all(request.method == "POST" for request, _ in calls)
    assert all(timeout == 20.0 for _, timeout in calls)

    (search_request, _), (fetch_request, _) = calls
    search_params = parse_qs(search_request.data.decode("utf-8"))
    fetch_params = parse_qs(fetch_request.data.decode("utf-8"))

    assert search_params["db"] == ["pubmed"]
    assert search_params["term"] == ["working memory"]
    assert search_params["retmode"] == ["xml"]
    assert search_params["retmax"] == ["2"]
    assert search_params["sort"] == ["pub_date"]
    assert search_params["tool"] == ["psi_jarvis"]
    assert search_params["email"] == ["researcher@example.org"]
    assert search_params["api_key"] == ["secret-key"]
    assert fetch_params["db"] == ["pubmed"]
    assert fetch_params["id"] == ["12345678,87654321"]
    assert fetch_params["retmode"] == ["xml"]

    assert "api_key" not in result.source_locator
    assert "email" not in result.source_locator
    assert "tool" not in result.source_locator
    assert "12345678%2C87654321" in result.source_locator


def test_pubmed_transport_supports_an_explicit_second_search_page():
    calls = []
    search_page = """
    <eSearchResult>
      <Count>4</Count>
      <RetMax>2</RetMax>
      <RetStart>2</RetStart>
      <IdList>
        <Id>33333333</Id>
        <Id>44444444</Id>
      </IdList>
    </eSearchResult>
    """.strip()

    def opener(request, timeout):
        calls.append((request, timeout))
        endpoint = urlsplit(request.full_url).path.rsplit("/", 1)[-1]
        return FakeResponse(search_page if endpoint == "esearch.fcgi" else FETCH_XML)

    result = PubMedEUtilsTransport(
        PubMedTransportConfig(tool="psi_jarvis", email="researcher@example.org", retmax=2),
        opener=opener,
    ).fetch(BibliographicQuery(text="memory", parameters=(("retstart", "2"),)))

    (search_request, _), (fetch_request, _) = calls
    search_params = parse_qs(search_request.data.decode("utf-8"))
    fetch_params = parse_qs(fetch_request.data.decode("utf-8"))

    assert search_params["retstart"] == ["2"]
    assert fetch_params["id"] == ["33333333,44444444"]
    assert result.raw_content == FETCH_XML


def test_pubmed_transport_does_not_call_efetch_when_esearch_returns_no_pmids():
    calls = []

    def opener(request, timeout):
        calls.append(request)
        return FakeResponse(
            """
            <eSearchResult>
              <Count>0</Count>
              <RetMax>20</RetMax>
              <RetStart>0</RetStart>
              <IdList />
            </eSearchResult>
            """.strip()
        )

    result = PubMedEUtilsTransport(
        PubMedTransportConfig(tool="psi_jarvis", email="researcher@example.org"),
        opener=opener,
    ).fetch(BibliographicQuery(text="no matches"))

    assert len(calls) == 1
    assert result.raw_content == "<PubmedArticleSet />"
    assert "esearch.fcgi" in result.source_locator


def test_pubmed_transport_rejects_unsupported_query_parameter():
    transport = PubMedEUtilsTransport(
        PubMedTransportConfig(tool="psi_jarvis", email="researcher@example.org"),
        opener=lambda request, timeout: pytest.fail("transport must not be called"),
    )

    with pytest.raises(ValueError, match="Unsupported PubMed E-utilities parameter"):
        transport.fetch(BibliographicQuery(text="memory", parameters=(("api_key", "oops"),)))


def test_pubmed_transport_rejects_invalid_esearch_xml():
    transport = PubMedEUtilsTransport(
        PubMedTransportConfig(tool="psi_jarvis", email="researcher@example.org"),
        opener=lambda request, timeout: FakeResponse("<broken"),
    )

    with pytest.raises(RuntimeError, match="Invalid NCBI ESearch XML"):
        transport.fetch(BibliographicQuery(text="memory"))


def test_pubmed_transport_rejects_incoherent_esearch_metadata():
    transport = PubMedEUtilsTransport(
        PubMedTransportConfig(tool="psi_jarvis", email="researcher@example.org", retmax=2),
        opener=lambda request, timeout: FakeResponse(
            """
            <eSearchResult>
              <Count>4</Count>
              <RetMax>2</RetMax>
              <RetStart>1</RetStart>
              <IdList><Id>12345678</Id></IdList>
            </eSearchResult>
            """.strip()
        ),
    )

    with pytest.raises(RuntimeError, match="retstart does not match"):
        transport.fetch(BibliographicQuery(text="memory"))


def test_pubmed_transport_rejects_retstart_window_over_10000():
    transport = PubMedEUtilsTransport(
        PubMedTransportConfig(tool="psi_jarvis", email="researcher@example.org", retmax=20),
        opener=lambda request, timeout: pytest.fail("transport must not be called"),
    )

    with pytest.raises(ValueError, match="retstart plus retmax cannot exceed 10000"):
        transport.fetch(BibliographicQuery(text="memory", parameters=(("retstart", "9999"),)))


def test_pubmed_transport_rejects_invalid_retstart_values():
    transport = PubMedEUtilsTransport(
        PubMedTransportConfig(tool="psi_jarvis", email="researcher@example.org"),
        opener=lambda request, timeout: pytest.fail("transport must not be called"),
    )

    with pytest.raises(ValueError, match="non-negative integer"):
        transport.fetch(BibliographicQuery(text="memory", parameters=(("retstart", "invalid"),)))

    with pytest.raises(ValueError, match="non-negative integer"):
        transport.fetch(BibliographicQuery(text="memory", parameters=(("retstart", "-1"),)))



def test_pubmed_transport_config_validates_ncbi_identification_and_limits():
    with pytest.raises(ValueError, match="tool"):
        PubMedTransportConfig(tool="psi jarvis", email="researcher@example.org")

    with pytest.raises(ValueError, match="email"):
        PubMedTransportConfig(tool="psi_jarvis", email="invalid")

    with pytest.raises(ValueError, match="retmax"):
        PubMedTransportConfig(tool="psi_jarvis", email="researcher@example.org", retmax=10001)

    with pytest.raises(ValueError, match="timeout"):
        PubMedTransportConfig(tool="psi_jarvis", email="researcher@example.org", timeout_seconds=0)
