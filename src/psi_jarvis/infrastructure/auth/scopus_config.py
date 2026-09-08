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
    local = ScopusLocalConfigStore().load()
    environment_key = os.environ.get("PSI_SCOPUS_API_KEY", "").strip()
    environment_oauth_keys = (
        "PSI_SCOPUS_CLIENT_ID",
        "PSI_SCOPUS_CLIENT_SECRET",
        "PSI_SCOPUS_AUTHORIZATION_ENDPOINT",
        "PSI_SCOPUS_TOKEN_ENDPOINT",
        "PSI_SCOPUS_SCOPES",
        "PSI_SCOPUS_REDIRECT_PORT",
    )
    has_environment_oauth = any(
        os.environ.get(key, "").strip() for key in environment_oauth_keys
    )

    if environment_key or has_environment_oauth:
        return ScopusLocalConfig(
            api_key=environment_key or (local.api_key if local is not None else ""),
            insttoken=os.environ.get("PSI_SCOPUS_INSTTOKEN")
            or (local.insttoken if local else None),
            client_id=os.environ.get("PSI_SCOPUS_CLIENT_ID") or None,
            client_secret=os.environ.get("PSI_SCOPUS_CLIENT_SECRET") or None,
            authorization_endpoint=os.environ.get("PSI_SCOPUS_AUTHORIZATION_ENDPOINT")
            or None,
            token_endpoint=os.environ.get("PSI_SCOPUS_TOKEN_ENDPOINT") or None,
            scopes=tuple(os.environ.get("PSI_SCOPUS_SCOPES", "").split()),
            base_url=os.environ.get(
                "PSI_SCOPUS_BASE_URL",
                local.base_url
                if local is not None
                else "https://api.elsevier.com/content/search/scopus",
            ),
            redirect_port=int(os.environ.get("PSI_SCOPUS_REDIRECT_PORT", "0")),
        )
    return local


def load_scopus_environment() -> ScopusEnvironmentConfig:
    config = _local_or_environment()
    if config is None:
        return ScopusEnvironmentConfig(api_key=None, transport=None, oauth=None)

    has_oauth = any(
        value
        for value in (
            config.client_id,
            config.authorization_endpoint,
            config.token_endpoint,
        )
    )
    if has_oauth and not config.client_id:
        raise ValueError("PSI_SCOPUS_CLIENT_ID is required for Scopus OAuth")
    if has_oauth and not config.authorization_endpoint:
        raise ValueError(
            "PSI_SCOPUS_AUTHORIZATION_ENDPOINT is required for Scopus OAuth"
        )
    if has_oauth and not config.token_endpoint:
        raise ValueError("PSI_SCOPUS_TOKEN_ENDPOINT is required for Scopus OAuth")

    if not config.api_key:
        raise ValueError(
            "Scopus API key is required when local Scopus configuration exists"
        )

    transport = ScopusTransportConfig(
        api_key=config.api_key,
        insttoken=config.insttoken,
        auth_token=None,
        base_url=config.base_url,
        timeout_seconds=float(os.environ.get("PSI_SCOPUS_TIMEOUT", "20")),
        count=int(os.environ.get("PSI_SCOPUS_COUNT", "20")),
    )

    oauth = None
    if has_oauth:
        oauth = ScopusOAuthConfig(
            client_id=config.client_id,
            client_secret=config.client_secret,
            authorization_endpoint=config.authorization_endpoint,
            token_endpoint=config.token_endpoint,
            scopes=config.scopes,
            redirect_port=config.redirect_port,
        )

    return ScopusEnvironmentConfig(
        api_key=config.api_key, transport=transport, oauth=oauth
    )
