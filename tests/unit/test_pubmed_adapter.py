from datetime import datetime, timezone
from pathlib import Path

from psi_jarvis.application.acquisition import BibliographicQuery
from psi_jarvis.domain.bibliography import BibliographicProvenance
from psi_jarvis.infrastructure.acquisition import RemoteAcquisitionResponse
from psi_jarvis.infrastructure.acquisition.pubmed import PubMedAdapter, PubMedXmlMapper


FIXED_TIME = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)
FIXTURE = Path(__file__).parents[1] / "fixtures" / "pubmed_records.xml"


def _fixture_response(query: BibliographicQuery) -> RemoteAcquisitionResponse:
    assert query.text == "working memory"
    return RemoteAcquisitionResponse(
        raw_content=FIXTURE.read_text(encoding="utf-8"),
        source_locator="fixture://pubmed_records.xml",
    )


def test_pubmed_mapper_maps_records_to_papers_and_provenance():
    raw_content = FIXTURE.read_text(encoding="utf-8")
    response = RemoteAcquisitionResponse(
        raw_content=raw_content,
        source_locator="fixture://pubmed_records.xml",
    )
    adapter = PubMedAdapter(fetcher=lambda query: response, clock=lambda: FIXED_TIME)

    result = adapter.acquire(BibliographicQuery(text="working memory"))

    assert result.success is True
    assert result.receipt is not None
    assert result.receipt.source_key == "pubmed"
    assert result.receipt.adapter_key == "pubmed-efetch"
    assert result.receipt.source_locator == "fixture://pubmed_records.xml"
    assert len(result.papers) == 2
    assert result.issues == ()

    first = result.papers[0]
    assert first.pmid == "12345678"
    assert first.doi == "10.1000/example.pubmed.1"
    assert first.title == "Working Memory and Intelligence"
    assert first.authors == ("Doe, J", "Smith, A", "Cognitive Research Group")
    assert first.publication_year == 2024
    assert first.journal == "Journal of Cognitive Research"
    assert first.abstract == (
        "BACKGROUND: Working memory is related to several cognitive functions.\n"
        "METHODS: Participants completed standardized cognitive tasks."
    )
    assert len(first.provenances) == 1
    assert isinstance(first.provenances[0], BibliographicProvenance)
    assert first.provenances[0].source_record_id == "12345678"

    second = result.papers[1]
    assert second.pmid == "87654321"
    assert second.publication_year == 2023
    assert second.doi is None
    assert second.abstract is None
    assert second.authors == ("Jones",)


def test_pubmed_mapper_reports_invalid_xml_without_papers():
    response = RemoteAcquisitionResponse(
        raw_content="<PubmedArticleSet><broken>",
        source_locator="fixture://invalid.xml",
    )
    adapter = PubMedAdapter(fetcher=lambda query: response, clock=lambda: FIXED_TIME)

    result = adapter.acquire(BibliographicQuery(text="memory"))

    assert result.success is False
    assert result.receipt is not None
    assert result.papers == ()
    assert len(result.issues) == 1
    assert result.issues[0].code == "invalid_format"
    assert result.issues[0].severity == "error"


def test_pubmed_mapper_preserves_transport_injection_boundary():
    calls: list[str] = []

    def fetcher(query: BibliographicQuery) -> RemoteAcquisitionResponse:
        calls.append(query.text)
        return RemoteAcquisitionResponse(
            raw_content="<PubmedArticleSet />",
            source_locator="fixture://empty.xml",
        )

    adapter = PubMedAdapter(fetcher=fetcher, clock=lambda: FIXED_TIME)
    result = adapter.acquire(BibliographicQuery(text="neuropsychology"))

    assert calls == ["neuropsychology"]
    assert result.success is True
    assert result.papers == ()
    assert result.issues == ()


def test_pubmed_xml_mapper_can_be_used_without_network_transport():
    mapper = PubMedXmlMapper()
    assert mapper.format_name == "PubMed XML"
    assert mapper.format_version == "1"
    assert mapper.mapping_version == "1"
