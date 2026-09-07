from __future__ import annotations

import os
from dataclasses import dataclass

from psi_jarvis.infrastructure.acquisition.scopus_transport import ScopusTransportConfig
from psi_jarvis.infrastructure.auth.scopus_oauth import ScopusOAuthConfig


@dataclass(frozen=True)
class ScopusEnvironmentConfig:
    """Configuración de Scopus obtenida desde variables de entorno."""

    api_key: str | None
    transport: ScopusTransportConfig | None
    oauth: ScopusOAuthConfig | None


def load_scopus_environment() -> ScopusEnvironmentConfig:
    api_key = os.environ.get("PSI_SCOPUS_API_KEY", "").strip() or None
    transport = None
    if api_key:
        transport = ScopusTransportConfig(
            api_key=api_key,
            insttoken=os.environ.get("PSI_SCOPUS_INSTTOKEN") or None,
            auth_token=None,
            base_url=os.environ.get(
                "PSI_SCOPUS_BASE_URL",
                "https://api.elsevier.com/content/search/scopus",
            ),
            timeout_seconds=float(os.environ.get("PSI_SCOPUS_TIMEOUT", "20")),
            count=int(os.environ.get("PSI_SCOPUS_COUNT", "20")),
        )

    client_id = os.environ.get("PSI_SCOPUS_CLIENT_ID", "").strip()
    authorization_endpoint = os.environ.get("PSI_SCOPUS_AUTHORIZATION_ENDPOINT", "").strip()
    token_endpoint = os.environ.get("PSI_SCOPUS_TOKEN_ENDPOINT", "").strip()
    oauth = None
    if client_id or authorization_endpoint or token_endpoint:
        if not (client_id and authorization_endpoint and token_endpoint):
            raise ValueError(
                "Scopus OAuth requires PSI_SCOPUS_CLIENT_ID, "
                "PSI_SCOPUS_AUTHORIZATION_ENDPOINT and PSI_SCOPUS_TOKEN_ENDPOINT"
            )
        oauth = ScopusOAuthConfig(
            client_id=client_id,
            client_secret=os.environ.get("PSI_SCOPUS_CLIENT_SECRET") or None,
            authorization_endpoint=authorization_endpoint,
            token_endpoint=token_endpoint,
            scopes=tuple(os.environ.get("PSI_SCOPUS_SCOPES", "").split()),
            redirect_port=int(os.environ.get("PSI_SCOPUS_REDIRECT_PORT", "0")),
        )

    return ScopusEnvironmentConfig(api_key=api_key, transport=transport, oauth=oauth)
