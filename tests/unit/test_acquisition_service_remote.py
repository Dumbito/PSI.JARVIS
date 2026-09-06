from psi_jarvis.application.acquisition import AcquisitionResult, AcquisitionService, BibliographicQuery


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
    from psi_jarvis.application.acquisition import BibliographicRemoteAcquisitionPort

    class FakeRemoteAdapter:
        source_key = "fake"
        adapter_key = "fake-remote"
        adapter_version = "1"

        def acquire(self, query: BibliographicQuery) -> AcquisitionResult:
            assert query.text == "memory"
            return AcquisitionResult(receipt=None)

    adapter = FakeRemoteAdapter()
    assert isinstance(adapter, BibliographicRemoteAcquisitionPort)
    result = AcquisitionService(adapter).execute_query(BibliographicQuery(text="memory"))
    assert result.success is True
