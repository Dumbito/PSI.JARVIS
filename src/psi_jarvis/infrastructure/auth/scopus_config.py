from __future__ import annotations

import os
from dataclasses import dataclass

from psi_jarvis.infrastructure.acquisition.scopus_transport import ScopusTransportConfig
from psi_jarvis.infrastructure.auth.scopus_local_config import (
    ScopusLocalConfig,
    ScopusLocalConfigStore,
)
from psi_jarvis.infrastructure.auth.scopus_oauth import ScopusOAuthConfig


@dataclass(frozen=True)
class ScopusEnvironmentConfig:
    """Configuración de Scopus desde entorno o almacenamiento local seguro."""

    api_key: str | None
    transport: ScopusTransportConfig | None
    oauth: ScopusOAuthConfig | None


def _local_or_environment() -> ScopusLocalConfig | None:
    environment_key = os.environ.get("PSI_SCOPUS_API_KEY", "").strip()
    local = ScopusLocalConfigStore().load()
    if environment_key:
        return ScopusLocalConfig(
            api_key=environment_key,
            insttoken=os.environ.get("PSI_SCOPUS_INSTTOKEN") or None,
            client_id=os.environ.get("PSI_SCOPUS_CLIENT_ID") or None,
            client_secret=os.environ.get("PSI_SCOPUS_CLIENT_SECRET") or None,
            authorization_endpoint=os.environ.get("PSI_SCOPUS_AUTHORIZATION_ENDPOINT") or None,
            token_endpoint=os.environ.get("PSI_SCOPUS_TOKEN_ENDPOINT") or None,
            scopes=tuple(os.environ.get("PSI_SCOPUS_SCOPES", "").split()),
            base_url=os.environ.get(
                "PSI_SCOPUS_BASE_URL",
                "https://api.elsevier.com/content/search/scopus",
            ),
            redirect_port=int(os.environ.get("PSI_SCOPUS_REDIRECT_PORT", "0")),
        )
    return local


def load_scopus_environment() -> ScopusEnvironmentConfig:
    config = _local_or_environment()
    if config is None:
        return ScopusEnvironmentConfig(api_key=None, transport=None, oauth=None)

    if not config.api_key:
        raise ValueError("Scopus API key is required when local Scopus configuration exists")

    transport = ScopusTransportConfig(
        api_key=config.api_key,
        insttoken=config.insttoken,
        auth_token=None,
        base_url=config.base_url,
        timeout_seconds=float(os.environ.get("PSI_SCOPUS_TIMEOUT", "20")),
        count=int(os.environ.get("PSI_SCOPUS_COUNT", "20")),
    )

    oauth = None
    if config.client_id or config.authorization_endpoint or config.token_endpoint:
        if not (config.client_id and config.authorization_endpoint and config.token_endpoint):
            raise ValueError(
                "Scopus OAuth requires client ID, authorization endpoint and token endpoint"
            )
        oauth = ScopusOAuthConfig(
            client_id=config.client_id,
            client_secret=config.client_secret,
            authorization_endpoint=config.authorization_endpoint,
            token_endpoint=config.token_endpoint,
            scopes=config.scopes,
            redirect_port=config.redirect_port,
        )

    return ScopusEnvironmentConfig(api_key=config.api_key, transport=transport, oauth=oauth)
