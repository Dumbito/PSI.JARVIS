from datetime import datetime, timezone

from psi_jarvis.application.acquisition import BibliographicQuery
from psi_jarvis.infrastructure.acquisition.remote_base import RemoteAcquisitionResponse
from psi_jarvis.infrastructure.acquisition.scopus import ScopusAdapter, ScopusJsonMapper


SCOPUS_JSON = """
{
  "search-results": {
    "entry": [
      {
        "dc:identifier": "SCOPUS_ID:85123456789",
        "dc:title": "Working Memory and Cognitive Integration",
        "dc:creator": "Smith, John",
        "dc:description": "Study of working memory.",
        "prism:publicationName": "Journal of Cognitive Science",
        "prism:doi": "10.1000/example.123",
        "prism:coverDate": "2026-04-17"
      }
    ]
  }
}
""".strip()


def adapter():
    return ScopusAdapter(
        fetcher=lambda query: RemoteAcquisitionResponse(SCOPUS_JSON, "https://example.test/scopus"),
        clock=lambda: datetime(2026, 9, 6, tzinfo=timezone.utc),
    )


def test_scopus_adapter_maps_paper_and_provenance():
    result = adapter().acquire(BibliographicQuery(text="working memory"))
    paper = result.papers[0]
    provenance = paper.provenances[0]

    assert paper.title == "Working Memory and Cognitive Integration"
    assert paper.authors == ("Smith", "John")
    assert paper.abstract == "Study of working memory."
    assert paper.doi == "10.1000/example.123"
    assert paper.publication_year == 2026
    assert paper.journal == "Journal of Cognitive Science"
    assert provenance.source_record_id == "SCOPUS_ID:85123456789"
    assert provenance.format_name == "Scopus Search JSON"
    assert provenance.mapping_version == "1"


def test_scopus_mapper_is_deterministic_for_same_receipt():
    mapper = ScopusJsonMapper()
    first = adapter().acquire(BibliographicQuery(text="memory"))

    mapped_a = mapper.map(RemoteAcquisitionResponse(SCOPUS_JSON, None), first.receipt)
    mapped_b = mapper.map(RemoteAcquisitionResponse(SCOPUS_JSON, None), first.receipt)

    assert mapped_a.papers[0].id == mapped_b.papers[0].id
    assert mapped_a.papers[0].provenances[0].raw_record_sha256 == mapped_b.papers[0].provenances[0].raw_record_sha256


def test_scopus_adapter_reports_invalid_json():
    broken = ScopusAdapter(
        fetcher=lambda query: RemoteAcquisitionResponse("{broken", None),
        clock=lambda: datetime(2026, 9, 6, tzinfo=timezone.utc),
    )
    result = broken.acquire(BibliographicQuery(text="memory"))

    assert result.papers == ()
    assert result.issues[0].code == "invalid_format"


def test_scopus_adapter_reports_missing_core_fields_as_warnings():
    payload = '{"search-results":{"entry":[{"dc:identifier":"SCOPUS_ID:1"}]}}'
    broken = ScopusAdapter(
        fetcher=lambda query: RemoteAcquisitionResponse(payload, None),
        clock=lambda: datetime(2026, 9, 6, tzinfo=timezone.utc),
    )
    result = broken.acquire(BibliographicQuery(text="memory"))

    assert len(result.papers) == 1
    assert {issue.code for issue in result.issues} == {"missing_title", "missing_journal"}


def test_scopus_adapter_reports_missing_identifier():
    payload = '{"search-results":{"entry":[{"dc:title":"Record","prism:publicationName":"Journal"}]}}'
    broken = ScopusAdapter(
        fetcher=lambda query: RemoteAcquisitionResponse(payload, None),
        clock=lambda: datetime(2026, 9, 6, tzinfo=timezone.utc),
    )
    result = broken.acquire(BibliographicQuery(text="memory"))

    assert len(result.papers) == 1
    assert result.papers[0].provenances[0].source_record_id is None
    assert result.issues[0].code == "missing_scopus_id"


def test_scopus_adapter_exposes_expected_metadata():
    value = adapter()

    assert value.source_key == "scopus"
    assert value.adapter_key == "scopus-search"
    assert value.adapter_version == "1"
    assert value.format_name == "Scopus Search JSON"
    assert value.format_version == "1"
    assert value.mapping_version == "1"


def test_scopus_adapter_delegates_query_to_fetcher():
    calls = []

    def fetcher(query):
        calls.append(query)
        return RemoteAcquisitionResponse(SCOPUS_JSON, None)

    value = ScopusAdapter(fetcher=fetcher)
    query = BibliographicQuery(text="cognitive flexibility")
    value.acquire(query)

    assert calls == [query]
