from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from psi_jarvis.infrastructure.acquisition.scopus_transport import ScopusTransportConfig
from psi_jarvis.infrastructure.auth.scopus_oauth import (
    JsonTokenStore,
    ScopusOAuthClient,
    ScopusOAuthConfig,
    ScopusOAuthToken,
)


class ScopusConnectionStatus(StrEnum):
    UNCONFIGURED = "unconfigured"
    CONFIGURED = "configured"
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    EXPIRED = "expired"


@dataclass(frozen=True)
class ScopusConnection:
    status: ScopusConnectionStatus
    token: ScopusOAuthToken | None = None
    transport_config: ScopusTransportConfig | None = None


class ScopusConnectionManager:
    """Administra credenciales API/OAuth de Scopus fuera del dominio bibliográfico."""

    def __init__(
        self,
        oauth_config: ScopusOAuthConfig | None,
        token_store: JsonTokenStore,
        oauth_client: ScopusOAuthClient | None = None,
        transport_config: ScopusTransportConfig | None = None,
    ) -> None:
        self._oauth_config = oauth_config
        self._token_store = token_store
        self._transport_config = transport_config
        self._oauth_client = oauth_client or (
            ScopusOAuthClient(oauth_config) if oauth_config is not None else None
        )

    def inspect(self) -> ScopusConnection:
        if self._transport_config is not None and self._oauth_config is None:
            return ScopusConnection(
                ScopusConnectionStatus.CONFIGURED,
                transport_config=self._transport_config,
            )
        if self._oauth_config is None:
            return ScopusConnection(ScopusConnectionStatus.UNCONFIGURED)
        token = self._token_store.load()
        if token is None:
            return ScopusConnection(ScopusConnectionStatus.DISCONNECTED)
        if token.is_expired:
            return ScopusConnection(ScopusConnectionStatus.EXPIRED, token, self._transport_config)
        return ScopusConnection(ScopusConnectionStatus.CONNECTED, token, self._transport_config)

    def login(self) -> ScopusConnection:
        if self._oauth_client is None:
            raise RuntimeError("Scopus OAuth is not configured")
        token = self._oauth_client.login()
        self._token_store.save(token)
        return ScopusConnection(ScopusConnectionStatus.CONNECTED, token, self._transport_config)

    def logout(self) -> None:
        self._token_store.delete()

    def ensure_connected(self) -> ScopusConnection:
        connection = self.inspect()
        if connection.status is ScopusConnectionStatus.CONFIGURED:
            return connection
        if connection.status is ScopusConnectionStatus.CONNECTED:
            return connection
        if connection.status is ScopusConnectionStatus.EXPIRED and connection.token is not None:
            if not connection.token.refresh_token or self._oauth_client is None:
                raise RuntimeError("Scopus OAuth token is expired and cannot be refreshed")
            refreshed = self._oauth_client.refresh_token(connection.token.refresh_token)
            if refreshed.refresh_token is None:
                refreshed = ScopusOAuthToken(
                    access_token=refreshed.access_token,
                    token_type=refreshed.token_type,
                    expires_at=refreshed.expires_at,
                    refresh_token=connection.token.refresh_token,
                    scope=refreshed.scope,
                )
            self._token_store.save(refreshed)
            return ScopusConnection(
                ScopusConnectionStatus.CONNECTED,
                refreshed,
                self._transport_config,
            )
        if connection.status is ScopusConnectionStatus.DISCONNECTED:
            raise RuntimeError("Scopus is not connected")
        raise RuntimeError(f"Scopus is not available: {connection.status.value}")

    def apply_token(self, transport_config: ScopusTransportConfig | None = None) -> ScopusTransportConfig:
        config = transport_config or self._transport_config
        if config is None:
            raise RuntimeError("Scopus transport is not configured")
        connection = self.ensure_connected()
        if connection.status is ScopusConnectionStatus.CONFIGURED:
            return config
        token = connection.token
        if token is None:
            raise RuntimeError("Scopus connection has no OAuth token")
        return ScopusTransportConfig(
            api_key=config.api_key,
            insttoken=config.insttoken,
            auth_token=token.access_token,
            base_url=config.base_url,
            timeout_seconds=config.timeout_seconds,
            count=config.count,
        )
