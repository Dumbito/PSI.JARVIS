from psi_jarvis.application.acquisition import (
    AcquisitionResult,
    AcquisitionService,
    BibliographicQuery,
    BibliographicRemoteAcquisitionPort,
    BibliographicSourceResolver,
)


class FakeRemoteAdapter:
    source_key = "fake"
    adapter_key = "fake-remote"
    adapter_version = "1"

    def acquire(self, query: BibliographicQuery) -> AcquisitionResult:
        assert query.text == "memory"
        return AcquisitionResult(receipt=None)


def test_acquisition_service_can_execute_remote_query_through_port():
    result = AcquisitionService(FakeRemoteAdapter()).execute_query(
        BibliographicQuery(text="memory")
    )

    assert isinstance(result, AcquisitionResult)
    assert result.success is True


def test_acquisition_service_remote_query_uses_remote_acquisition_port():
    adapter = FakeRemoteAdapter()
    assert isinstance(adapter, BibliographicRemoteAcquisitionPort)
    result = AcquisitionService(adapter).execute_query(BibliographicQuery(text="memory"))
    assert result.success is True


def test_acquisition_service_resolves_remote_adapter_by_source_key():
    class FakeResolver:
        def __init__(self, adapter):
            self.adapter = adapter
            self.requested_source = None

        def resolve(self, source_key: str):
            self.requested_source = source_key
            return self.adapter

    adapter = FakeRemoteAdapter()
    resolver = FakeResolver(adapter)
    assert isinstance(resolver, BibliographicSourceResolver)

    result = AcquisitionService(adapter).execute_remote_query(
        "fake",
        BibliographicQuery(text="memory"),
        resolver,
    )

    assert resolver.requested_source == "fake"
    assert result.success is True
