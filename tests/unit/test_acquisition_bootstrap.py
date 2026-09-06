from psi_jarvis.infrastructure.acquisition import (
    PubMedAdapter,
    PubMedTransportConfig,
    build_default_bibliographic_registry,
)


def test_default_bibliographic_registry_contains_configured_pubmed_adapter():
    config = PubMedTransportConfig(
        tool="psi_jarvis",
        email="researcher@example.org",
        api_key="secret-key",
    )

    registry = build_default_bibliographic_registry(config)

    assert registry.sources() == ("pubmed",)
    adapter = registry.resolve("pubmed")
    assert isinstance(adapter, PubMedAdapter)
    assert adapter.source_key == "pubmed"
    assert adapter.adapter_key == "pubmed-efetch"
    assert adapter.adapter_version == "1"
