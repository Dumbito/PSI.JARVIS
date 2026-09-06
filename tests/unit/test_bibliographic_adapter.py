from psi_jarvis.application.acquisition import BibliographicAcquisitionPort, BibliographicQuery


def test_bibliographic_acquisition_port_is_a_runtime_checkable_query_adapter():
    class FakeAdapter:
        source_key = "fake"

        def acquire(self, query: BibliographicQuery):
            raise NotImplementedError

    assert isinstance(FakeAdapter(), BibliographicAcquisitionPort)
    assert FakeAdapter.source_key == "fake"


def test_bibliographic_acquisition_port_requires_a_source_key_and_query_acquire():
    class InvalidAdapter:
        pass

    assert not isinstance(InvalidAdapter(), BibliographicAcquisitionPort)
