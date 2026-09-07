from psi_jarvis.infrastructure.acquisition.bootstrap import build_default_bibliographic_registry
from psi_jarvis.infrastructure.acquisition.pubmed_transport import PubMedTransportConfig
from psi_jarvis.infrastructure.acquisition.scopus import ScopusAdapter
from psi_jarvis.infrastructure.acquisition.scopus_transport import ScopusTransportConfig


def test_default_registry_resolves_configured_scopus_adapter():
    registry = build_default_bibliographic_registry(
        PubMedTransportConfig(
            tool="psi_jarvis",
            email="researcher@example.org",
            api_key="pubmed-key",
        ),
        scopus_config=ScopusTransportConfig(api_key="scopus-key"),
    )

    assert registry.sources() == ("pubmed", "scopus")
    adapter = registry.resolve("scopus")
    assert isinstance(adapter, ScopusAdapter)
    assert adapter.source_key == "scopus"
    assert adapter.adapter_key == "scopus-search"
    assert adapter.adapter_version == "1"
