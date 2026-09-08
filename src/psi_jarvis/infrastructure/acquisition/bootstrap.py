from __future__ import annotations

from collections.abc import Callable

from psi_jarvis.infrastructure.acquisition.pubmed import build_pubmed_adapter
from psi_jarvis.infrastructure.acquisition.pubmed_transport import PubMedTransportConfig
from psi_jarvis.infrastructure.acquisition.registry import (
    BibliographicAdapterRegistry,
    build_bibliographic_registry,
)
from psi_jarvis.infrastructure.acquisition.scopus import build_scopus_adapter
from psi_jarvis.infrastructure.acquisition.scopus_transport import ScopusTransportConfig
from psi_jarvis.infrastructure.acquisition.wos import build_wos_adapter
from psi_jarvis.infrastructure.acquisition.wos_transport import (
    WebOfScienceTransportConfig,
)
from psi_jarvis.infrastructure.acquisition.zotero import build_zotero_adapter
from psi_jarvis.infrastructure.acquisition.zotero_transport import ZoteroTransportConfig


def build_default_bibliographic_registry(
    pubmed_config: PubMedTransportConfig,
    *,
    scopus_config: ScopusTransportConfig | None = None,
    wos_config: WebOfScienceTransportConfig | None = None,
    zotero_config: ZoteroTransportConfig | None = None,
    clock: Callable[[], object] | None = None,
    opener: Callable[..., object] | None = None,
) -> BibliographicAdapterRegistry:
    """Construye el registry con las fuentes configuradas explícitamente."""

    adapters = [
        build_pubmed_adapter(
            config=pubmed_config,
            clock=clock,
            opener=opener,
        )
    ]
    if scopus_config is not None:
        adapters.append(
            build_scopus_adapter(config=scopus_config, clock=clock, opener=opener)
        )
    if wos_config is not None:
        adapters.append(
            build_wos_adapter(config=wos_config, clock=clock, opener=opener)
        )
    if zotero_config is not None:
        adapters.append(
            build_zotero_adapter(config=zotero_config, clock=clock, opener=opener)
        )
    return build_bibliographic_registry(*adapters)
