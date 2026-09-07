from __future__ import annotations

from typing import Callable

from psi_jarvis.infrastructure.acquisition.pubmed import build_pubmed_adapter
from psi_jarvis.infrastructure.acquisition.pubmed_transport import PubMedTransportConfig
from psi_jarvis.infrastructure.acquisition.registry import BibliographicAdapterRegistry, build_bibliographic_registry
from psi_jarvis.infrastructure.acquisition.scopus import build_scopus_adapter
from psi_jarvis.infrastructure.acquisition.scopus_transport import ScopusTransportConfig


def build_default_bibliographic_registry(
    pubmed_config: PubMedTransportConfig,
    *,
    scopus_config: ScopusTransportConfig | None = None,
    clock: Callable[[], object] | None = None,
    opener: Callable[..., object] | None = None,
) -> BibliographicAdapterRegistry:
    """Construye el registry de producción con los adapters remotos configurados."""

    pubmed_adapter = build_pubmed_adapter(
        config=pubmed_config,
        clock=clock,
        opener=opener,
    )
    adapters = [pubmed_adapter]
    if scopus_config is not None:
        adapters.append(
            build_scopus_adapter(
                config=scopus_config,
                clock=clock,
                opener=opener,
            )
        )
    return build_bibliographic_registry(*adapters)
