from psi_jarvis.application.acquisition.contracts import BibliographicQuery
from psi_jarvis.infrastructure.acquisition.registry import BibliographicAdapterRegistry
from psi_jarvis.infrastructure.acquisition.remote_base import RemoteAcquisitionResponse
from psi_jarvis.infrastructure.acquisition.wos import WebOfScienceAdapter
from psi_jarvis.infrastructure.acquisition.zotero import ZoteroAdapter


def test_multi_source_adapters_expose_stable_unique_identity():
    adapters = (
        WebOfScienceAdapter(lambda query: RemoteAcquisitionResponse(raw_content='{"hits":[]}')),
        ZoteroAdapter(lambda query: RemoteAcquisitionResponse(raw_content='[]')),
    )
    registry = BibliographicAdapterRegistry()
    for adapter in adapters:
        registry.register(adapter)

    assert registry.sources() == ("web_of_science", "zotero")
    assert len({adapter.adapter_key for adapter in adapters}) == 2
    assert all(adapter.adapter_version == "1" for adapter in adapters)


def test_empty_remote_results_still_produce_audit_receipt():
    for adapter in (
        WebOfScienceAdapter(lambda query: RemoteAcquisitionResponse(raw_content='{"hits":[]}')),
        ZoteroAdapter(lambda query: RemoteAcquisitionResponse(raw_content='[]')),
    ):
        result = adapter.acquire(BibliographicQuery(text="memory"))
        assert result.papers == ()
        assert result.receipt.source_key == adapter.source_key
        assert result.receipt.adapter_key == adapter.adapter_key
