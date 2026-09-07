from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable


class SourceConnectionStatus(StrEnum):
    AVAILABLE = "available"
    CONFIGURED = "configured"
    UNAVAILABLE = "unavailable"
    AUTH_REQUIRED = "auth_required"
    AUTH_EXPIRED = "auth_expired"
    ACCESS_LIMITED = "access_limited"
    ERROR = "error"


class CredentialMethod(StrEnum):
    NONE = "none"
    API_KEY = "api_key"
    INSTITUTIONAL_TOKEN = "institutional_token"
    OAUTH = "oauth"


@dataclass(frozen=True)
class SourceConnectionDefinition:
    key: str
    display_name: str
    requires_auth: bool
    credential_methods: tuple[CredentialMethod, ...] = ()


@dataclass(frozen=True)
class SourceConnectionState:
    source: SourceConnectionDefinition
    status: SourceConnectionStatus
    credential_method: CredentialMethod = CredentialMethod.NONE
    detail: str | None = None


class SourceConnectionRegistry:
    """Registro agnóstico del estado de disponibilidad de fuentes externas."""

    def __init__(self) -> None:
        self._definitions: dict[str, SourceConnectionDefinition] = {}
        self._inspectors: dict[str, Callable[[], SourceConnectionState]] = {}

    def register(
        self,
        definition: SourceConnectionDefinition,
        inspector: Callable[[], SourceConnectionState],
    ) -> None:
        if not definition.key.strip():
            raise ValueError("Source connection key cannot be empty")
        if definition.key in self._definitions:
            raise ValueError(f"Source connection already registered: {definition.key}")
        self._definitions[definition.key] = definition
        self._inspectors[definition.key] = inspector

    def inspect(self, source_key: str) -> SourceConnectionState:
        try:
            return self._inspectors[source_key]()
        except KeyError as exc:
            raise KeyError(f"Unknown source connection: {source_key}") from exc

    def inspect_all(self) -> tuple[SourceConnectionState, ...]:
        return tuple(self._inspectors[key]() for key in sorted(self._inspectors))

    def sources(self) -> tuple[str, ...]:
        return tuple(sorted(self._definitions))
