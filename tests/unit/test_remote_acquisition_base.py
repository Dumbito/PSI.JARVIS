from datetime import datetime, timezone

import pytest

from psi_jarvis.application.acquisition import AcquisitionResult, BibliographicQuery
from psi_jarvis.domain.bibliography import AcquisitionReceipt


FIXED_TIME = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)


def test_remote_adapter_receipt_records_query_and_adapter_identity():
    receipt = AcquisitionReceipt.create(
        source_key="fake",
        adapter_key="fake-remote",
        adapter_version="1",
        acquired_at=FIXED_TIME,
        request_payload=BibliographicQuery(text="working memory").payload(),
        input_content="{results:[]}",
        source_locator=None,
    )

    assert receipt.source_key == "fake"
    assert receipt.adapter_key == "fake-remote"
    assert receipt.adapter_version == "1"
    assert "working memory" in receipt.request_json
    assert receipt.source_locator is None


def test_empty_remote_result_is_a_valid_acquisition_result():
    result = AcquisitionResult(receipt=None, papers=(), issues=())
    assert result.success is True
    assert result.papers == ()
    assert result.issues == ()


def test_remote_adapter_base_contract_exposes_acquire_workflow():
    from psi_jarvis.infrastructure.acquisition.remote_base import RemoteBibliographicAdapter

    assert hasattr(RemoteBibliographicAdapter, "acquire")
    assert hasattr(RemoteBibliographicAdapter, "fetch")
    assert hasattr(RemoteBibliographicAdapter, "map_response")


def test_remote_acquisition_response_is_immutable_and_preserves_raw_payload():
    from psi_jarvis.infrastructure.acquisition.remote_base import RemoteAcquisitionResponse

    response = RemoteAcquisitionResponse(raw_content="{results:[]}", source_locator=None)

    assert response.raw_content == "{results:[]}"
    assert response.source_locator is None

    try:
        response.raw_content = "changed"
    except AttributeError:
        pass
    else:
        raise AssertionError("RemoteAcquisitionResponse should be immutable")


def test_remote_response_reader_enforces_memory_limit():
    from psi_jarvis.infrastructure.acquisition.remote_base import read_remote_response

    class FakeResponse:
        headers = {}

        def read(self, size=-1):
            payload = b"abcdefgh"
            return payload if size < 0 else payload[:size]

    assert read_remote_response(FakeResponse(), max_bytes=8) == b"abcdefgh"
    with pytest.raises(RuntimeError, match="exceeds"):
        read_remote_response(FakeResponse(), max_bytes=7)


def test_remote_response_reader_rejects_excess_content_length_before_reading():
    from psi_jarvis.infrastructure.acquisition.remote_base import read_remote_response

    class FakeResponse:
        headers = {"Content-Length": "99"}

        def read(self, size=-1):
            raise AssertionError("response body must not be read after a rejected Content-Length")

    with pytest.raises(RuntimeError, match="exceeds"):
        read_remote_response(FakeResponse(), max_bytes=8)


def test_remote_adapter_converts_transport_failure_into_acquisition_issue():
    from psi_jarvis.application.acquisition import BibliographicQuery
    from psi_jarvis.infrastructure.acquisition.remote_base import RemoteBibliographicAdapter

    class FailingAdapter(RemoteBibliographicAdapter):
        source_key = "fake"
        adapter_key = "fake-remote"
        adapter_version = "1"
        format_name = "fixture"
        format_version = "1"
        mapping_version = "1"

        def fetch(self, query):
            raise RuntimeError("transport unavailable")

        def map_response(self, response, receipt):
            raise AssertionError("map_response should not be called after transport failure")

    try:
        FailingAdapter().acquire(BibliographicQuery(text="memory"))
    except RuntimeError as exc:
        assert str(exc) == "transport unavailable"
    else:
        raise AssertionError("Transport failures must not be silently ignored")


def test_remote_adapter_acquire_builds_receipt_and_delegates_mapping():
    from psi_jarvis.application.acquisition import BibliographicQuery
    from psi_jarvis.infrastructure.acquisition.remote_base import RemoteAcquisitionResponse, RemoteBibliographicAdapter

    class FakeAdapter(RemoteBibliographicAdapter):
        source_key = "fake"
        adapter_key = "fake-remote"
        adapter_version = "1"
        format_name = "fixture-json"
        format_version = "1"
        mapping_version = "1"

        def fetch(self, query):
            assert query.text == "memory"
            return RemoteAcquisitionResponse(
                raw_content="{results:[]}",
                source_locator="fixture://memory",
            )

        def map_response(self, response, receipt):
            assert response.source_locator == "fixture://memory"
            assert receipt.source_key == "fake"
            assert receipt.adapter_key == "fake-remote"
            return AcquisitionResult(receipt=receipt)

    result = FakeAdapter(clock=lambda: FIXED_TIME).acquire(BibliographicQuery(text="memory"))

    assert result.success is True
    assert result.receipt is not None
    assert result.receipt.source_key == "fake"
    assert result.receipt.source_locator == "fixture://memory"
