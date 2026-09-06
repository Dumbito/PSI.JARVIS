from datetime import datetime, timezone

from psi_jarvis.application.acquisition import AcquisitionResult, BibliographicQuery
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.acquisition import RemoteAcquisitionResponse, RemoteBibliographicAdapter
from psi_jarvis.domain.bibliography import BibliographicProvenance
from psi_jarvis.domain.bibliography.provenance import sha256_text


FIXED_TIME = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)


class FixtureRemoteAdapter(RemoteBibliographicAdapter):
    source_key = "fixture"
    adapter_key = "fixture-remote"
    adapter_version = "1"
    format_name = "fixture-json"
    format_version = "1"
    mapping_version = "1"

    def fetch(self, query: BibliographicQuery):
        return RemoteAcquisitionResponse(
            raw_content="fixture-record-1|Working Memory Study|fixture-1",
            source_locator="fixture://bibliography",
        )

    def map_response(self, response, receipt):
        raw_record = response.raw_content
        fields = raw_record.split("|")
        provenance = BibliographicProvenance(
            receipt=receipt,
            record_ordinal=1,
            format_name=self.format_name,
            format_version=self.format_version,
            mapping_version=self.mapping_version,
            raw_record_sha256=sha256_text(raw_record),
            source_record_id=fields[2],
        )
        paper = Paper(title=fields[1], provenances=(provenance,))
        return AcquisitionResult(receipt=receipt, papers=(paper,))


def test_fixture_remote_adapter_produces_paper_with_provenance():
    result = FixtureRemoteAdapter(clock=lambda: FIXED_TIME).acquire(
        BibliographicQuery(text="working memory")
    )

    assert result.success is True
    assert result.receipt is not None
    assert result.receipt.source_key == "fixture"
    assert result.receipt.source_locator == "fixture://bibliography"
    assert len(result.papers) == 1
    assert isinstance(result.papers[0], Paper)
    assert result.papers[0].title == "Working Memory Study"
    assert len(result.papers[0].provenances) == 1
    assert isinstance(result.papers[0].provenances[0], BibliographicProvenance)
    assert result.papers[0].provenances[0].source_record_id == "fixture-1"
