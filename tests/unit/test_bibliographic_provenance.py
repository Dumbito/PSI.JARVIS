from datetime import datetime, timezone

from psi_jarvis.domain.bibliography import AcquisitionReceipt, BibliographicProvenance
from psi_jarvis.domain.bibliography.provenance import sha256_text
from psi_jarvis.domain.paper import Paper


FIXED_TIME = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def receipt():
    return AcquisitionReceipt.create(
        source_key="ris",
        adapter_key="local-ris",
        adapter_version="1",
        acquired_at=FIXED_TIME,
        request_payload={"location": "records.ris", "context": "fixture"},
        input_content="fixture-content",
        source_locator="records.ris",
    )


def provenance():
    return BibliographicProvenance(
        receipt=receipt(),
        record_ordinal=1,
        format_name="RIS",
        format_version="1",
        mapping_version="1",
        raw_record_sha256=sha256_text("record"),
        source_record_id="record-1",
    )


def test_acquisition_receipt_is_immutable_and_uses_utc_timestamp():
    item = receipt()

    assert item.acquired_at == FIXED_TIME
    try:
        item.source_key = "changed"
    except AttributeError:
        pass
    else:
        raise AssertionError("Acquisition receipt should be immutable")


def test_acquisition_receipt_serialization_and_hashes_are_deterministic():
    first = receipt()
    second = receipt()

    assert first == second
    assert first.to_json() == second.to_json()
    assert first.request_sha256 == sha256_text(first.request_json)
    assert len(first.input_sha256) == 64


def test_bibliographic_provenance_is_immutable_and_has_stable_key():
    item = provenance()

    assert item.source_key == "ris"
    assert len(item.key) == 64
    try:
        item.record_ordinal = 2
    except AttributeError:
        pass
    else:
        raise AssertionError("Bibliographic provenance should be immutable")


def test_paper_defaults_to_empty_provenance_for_backward_compatibility():
    assert Paper(title="Historical paper").provenances == ()
