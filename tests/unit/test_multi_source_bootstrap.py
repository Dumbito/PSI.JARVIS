from psi_jarvis.infrastructure.acquisition import (
    PubMedAdapter,
    PubMedTransportConfig,
    ScopusAdapter,
    ScopusTransportConfig,
    WebOfScienceAdapter,
    WebOfScienceTransportConfig,
    ZoteroAdapter,
    ZoteroTransportConfig,
    build_default_bibliographic_registry,
)


def test_bootstrap_keeps_pubmed_only_by_default():
    registry = build_default_bibliographic_registry(
        PubMedTransportConfig(tool="psi_jarvis", email="researcher@example.org")
    )
    assert registry.sources() == ("pubmed",)
    assert isinstance(registry.resolve("pubmed"), PubMedAdapter)


def test_bootstrap_registers_all_explicitly_configured_sources():
    registry = build_default_bibliographic_registry(
        PubMedTransportConfig(tool="psi_jarvis", email="researcher@example.org"),
        scopus_config=ScopusTransportConfig(api_key="scopus-key"),
        wos_config=WebOfScienceTransportConfig(api_key="wos-key"),
        zotero_config=ZoteroTransportConfig(user_id="123", api_key="zotero-key"),
    )
    assert registry.sources() == ("pubmed", "scopus", "web_of_science", "zotero")
    assert isinstance(registry.resolve("scopus"), ScopusAdapter)
    assert isinstance(registry.resolve("web_of_science"), WebOfScienceAdapter)
    assert isinstance(registry.resolve("zotero"), ZoteroAdapter)
