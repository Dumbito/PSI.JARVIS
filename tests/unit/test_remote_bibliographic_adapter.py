from psi_jarvis.application.acquisition import AcquisitionResult, BibliographicQuery, BibliographicRemoteAcquisitionPort


def test_remote_bibliographic_acquisition_port_accepts_query_adapter():
    class FakeRemoteAdapter:
        source_key = "fake"
        adapter_key = "fake-remote"
        adapter_version = "1"

        def acquire(self, query: BibliographicQuery) -> AcquisitionResult:
            raise NotImplementedError

    assert isinstance(FakeRemoteAdapter(), BibliographicRemoteAcquisitionPort)
    assert FakeRemoteAdapter.source_key == "fake"
    assert FakeRemoteAdapter.adapter_key == "fake-remote"
    assert FakeRemoteAdapter.adapter_version == "1"


def test_remote_bibliographic_acquisition_port_rejects_non_adapter():
    class InvalidAdapter:
        source_key = "fake"

    assert not isinstance(InvalidAdapter(), BibliographicRemoteAcquisitionPort)



def test_remote_bibliographic_acquisition_port_declares_acquisition_result_contract():
    class FakeRemoteAdapter:
        source_key = "fake"

        def acquire(self, query: BibliographicQuery) -> AcquisitionResult:
            return AcquisitionResult(receipt=None)

    result = FakeRemoteAdapter().acquire(BibliographicQuery(text="memory"))
    assert isinstance(result, AcquisitionResult)
