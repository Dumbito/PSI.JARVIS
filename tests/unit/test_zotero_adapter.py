import json
from datetime import datetime, timezone

from psi_jarvis.application.acquisition import BibliographicQuery
from psi_jarvis.domain.bibliography.provenance import AcquisitionReceipt
from psi_jarvis.infrastructure.acquisition.remote_base import RemoteAcquisitionResponse
from psi_jarvis.infrastructure.acquisition.zotero import ZoteroAdapter, ZoteroJsonMapper

PAYLOAD = json.dumps([{
    "key": "ABCD1234",
    "version": 1,
    "data": {
        "title": "Memory and Intelligence",
        "abstractNote": "Abstract text",
        "DOI": "10.1000/zotero",
        "publicationTitle": "Cognitive Science Journal",
        "date": "2024-05-01",
        "creators": [
            {"creatorType": "author", "firstName": "Jane", "lastName": "Smith"},
            {"creatorType": "author", "name": "Research Group"},
        ],
    },
}])


def receipt() -> AcquisitionReceipt:
    return AcquisitionReceipt.create(
        source_key="zotero",
        adapter_key="zotero-web-api",
        adapter_version="1",
        acquired_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        request_payload=BibliographicQuery(text="memory").payload(),
        input_content=PAYLOAD,
    )


def test_zotero_mapper_maps_core_fields_and_provenance():
    result = ZoteroJsonMapper().map(RemoteAcquisitionResponse(PAYLOAD), receipt())
    assert len(result.papers) == 1
    paper = result.papers[0]
    assert paper.title == "Memory and Intelligence"
    assert paper.authors == ("Smith, Jane", "Research Group")
    assert paper.abstract == "Abstract text"
    assert paper.doi == "10.1000/zotero"
    assert paper.publication_year == 2024
    assert paper.journal == "Cognitive Science Journal"
    assert paper.provenances[0].source_record_id == "ABCD1234"
    assert not result.issues


def test_zotero_mapper_rejects_non_list_response():
    result = ZoteroJsonMapper().map(RemoteAcquisitionResponse("{}"), receipt())
    assert result.papers == ()
    assert result.issues[0].code == "invalid_format"


def test_zotero_adapter_delegates_fetch_and_mapping():
    adapter = ZoteroAdapter(fetcher=lambda query: RemoteAcquisitionResponse(PAYLOAD))
    result = adapter.acquire(BibliographicQuery(text="memory"))
    assert len(result.papers) == 1
    assert result.papers[0].provenances[0].source_record_id == "ABCD1234"
