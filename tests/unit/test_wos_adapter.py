import json
from datetime import datetime, timezone
from uuid import UUID

from psi_jarvis.application.acquisition import BibliographicQuery
from psi_jarvis.domain.bibliography.provenance import AcquisitionReceipt
from psi_jarvis.infrastructure.acquisition.remote_base import RemoteAcquisitionResponse
from psi_jarvis.infrastructure.acquisition.wos import WebOfScienceAdapter, WebOfScienceJsonMapper

PAYLOAD = json.dumps({
    "hits": [{
        "uid": "WOS:000123456789",
        "title": "Working Memory Study",
        "source": {"sourceTitle": "Journal of Cognition", "publishYear": 2025},
        "names": {"authors": [{"displayName": "Smith, Jane"}, {"displayName": "Doe, John"}]},
        "identifiers": {"doi": "10.1000/example"},
    }]
})


def receipt() -> AcquisitionReceipt:
    return AcquisitionReceipt.create(
        source_key="web_of_science",
        adapter_key="wos-starter",
        adapter_version="1",
        acquired_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        request_payload=BibliographicQuery(text="TS=memory").payload(),
        input_content=PAYLOAD,
    )


def test_wos_mapper_maps_core_fields_and_provenance():
    result = WebOfScienceJsonMapper().map(RemoteAcquisitionResponse(PAYLOAD), receipt())
    assert len(result.papers) == 1
    paper = result.papers[0]
    assert paper.title == "Working Memory Study"
    assert paper.authors == ("Smith, Jane", "Doe, John")
    assert paper.doi == "10.1000/example"
    assert paper.publication_year == 2025
    assert paper.journal == "Journal of Cognition"
    assert paper.provenances[0].source_record_id == "WOS:000123456789"
    assert isinstance(paper.id, UUID)
    assert not result.issues


def test_wos_mapper_rejects_non_list_hits():
    payload = json.dumps({"hits": {}})
    result = WebOfScienceJsonMapper().map(RemoteAcquisitionResponse(payload), receipt())
    assert result.papers == ()
    assert result.issues[0].code == "invalid_format"


def test_wos_adapter_delegates_fetch_and_mapping():
    adapter = WebOfScienceAdapter(fetcher=lambda query: RemoteAcquisitionResponse(PAYLOAD))
    result = adapter.acquire(BibliographicQuery(text="memory"))
    assert len(result.papers) == 1
    assert result.papers[0].provenances[0].source_record_id == "WOS:000123456789"
