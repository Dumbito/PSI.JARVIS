from __future__ import annotations

from psi_jarvis.infrastructure.acquisition.wos_transport import (
    WebOfScienceTransportConfig,
)
from psi_jarvis.infrastructure.acquisition.zotero_transport import ZoteroTransportConfig
from psi_jarvis.infrastructure.auth.scopus_connection import (
    ScopusConnectionManager,
    ScopusConnectionStatus,
)
from psi_jarvis.infrastructure.connections.source_connections import (
    CredentialMethod,
    SourceConnectionDefinition,
    SourceConnectionRegistry,
    SourceConnectionState,
    SourceConnectionStatus,
)


PUBMED_SOURCE = SourceConnectionDefinition(
    key="pubmed",
    display_name="PubMed",
    requires_auth=False,
)
SCOPUS_SOURCE = SourceConnectionDefinition(
    key="scopus",
    display_name="Scopus",
    requires_auth=True,
    credential_methods=(
        CredentialMethod.API_KEY,
        CredentialMethod.INSTITUTIONAL_TOKEN,
        CredentialMethod.OAUTH,
    ),
)
WOS_SOURCE = SourceConnectionDefinition(
    key="web_of_science",
    display_name="Web of Science",
    requires_auth=True,
    credential_methods=(CredentialMethod.API_KEY, CredentialMethod.OAUTH),
)
ZOTERO_SOURCE = SourceConnectionDefinition(
    key="zotero",
    display_name="Zotero",
    requires_auth=True,
    credential_methods=(CredentialMethod.API_KEY, CredentialMethod.OAUTH),
)


def build_default_source_connection_registry(
    scopus_manager: ScopusConnectionManager,
    *,
    wos_config: WebOfScienceTransportConfig | None = None,
    zotero_config: ZoteroTransportConfig | None = None,
) -> SourceConnectionRegistry:
    registry = SourceConnectionRegistry()

    registry.register(
        PUBMED_SOURCE,
        lambda: SourceConnectionState(
            source=PUBMED_SOURCE,
            status=SourceConnectionStatus.AVAILABLE,
            credential_method=CredentialMethod.NONE,
            detail="Fuente pública sin autenticación.",
        ),
    )
    registry.register(SCOPUS_SOURCE, lambda: _scopus_state(scopus_manager))
    registry.register(
        WOS_SOURCE,
        lambda: _configured_api_state(
            WOS_SOURCE,
            wos_config is not None,
            "Credencial configurada; falta verificar el acceso efectivo a la API.",
        ),
    )
    registry.register(
        ZOTERO_SOURCE,
        lambda: _configured_api_state(
            ZOTERO_SOURCE,
            zotero_config is not None,
            "Credencial configurada; falta verificar el acceso efectivo a la API.",
        ),
    )
    return registry


def _configured_api_state(
    source: SourceConnectionDefinition,
    configured: bool,
    detail: str,
) -> SourceConnectionState:
    if configured:
        return SourceConnectionState(
            source=source,
            status=SourceConnectionStatus.CONFIGURED,
            credential_method=CredentialMethod.API_KEY,
            detail=detail,
        )
    return SourceConnectionState(
        source=source,
        status=SourceConnectionStatus.UNAVAILABLE,
        detail="Conector disponible, pero no hay credencial configurada.",
    )


def _scopus_state(manager: ScopusConnectionManager) -> SourceConnectionState:
    connection = manager.inspect()
    if connection.status is ScopusConnectionStatus.CONNECTED:
        return SourceConnectionState(
            source=SCOPUS_SOURCE,
            status=SourceConnectionStatus.AVAILABLE,
            credential_method=CredentialMethod.OAUTH,
            detail="OAuth conectado; acceso API sujeto a los permisos de Elsevier.",
        )
    if connection.status is ScopusConnectionStatus.CONFIGURED:
        method = (
            CredentialMethod.INSTITUTIONAL_TOKEN
            if connection.transport_config is not None
            and connection.transport_config.insttoken
            else CredentialMethod.API_KEY
        )
        return SourceConnectionState(
            source=SCOPUS_SOURCE,
            status=SourceConnectionStatus.CONFIGURED,
            credential_method=method,
            detail="Credencial configurada; falta verificar el acceso efectivo a la API.",
        )
    if connection.status is ScopusConnectionStatus.EXPIRED:
        return SourceConnectionState(
            source=SCOPUS_SOURCE,
            status=SourceConnectionStatus.AUTH_EXPIRED,
            credential_method=CredentialMethod.OAUTH,
            detail="La sesión OAuth expiró.",
        )
    if connection.status is ScopusConnectionStatus.DISCONNECTED:
        return SourceConnectionState(
            source=SCOPUS_SOURCE,
            status=SourceConnectionStatus.AUTH_REQUIRED,
            detail="Configura una credencial de Scopus para habilitar la fuente.",
        )
    return SourceConnectionState(
        source=SCOPUS_SOURCE,
        status=SourceConnectionStatus.UNAVAILABLE,
        detail="Scopus no está configurado.",
    )
