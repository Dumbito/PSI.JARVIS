from __future__ import annotations

import json
from dataclasses import dataclass
from collections.abc import Callable
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from psi_jarvis.application.acquisition.contracts import BibliographicQuery
from psi_jarvis.infrastructure.acquisition.remote_base import (
    RemoteAcquisitionResponse,
    read_remote_response,
)


DEFAULT_ZOTERO_BASE_URL = "https://api.zotero.org"


@dataclass(frozen=True)
class ZoteroTransportConfig:
    """Configuración del Zotero Web API v3 para bibliotecas de usuario."""

    user_id: str
    api_key: str
    base_url: str = DEFAULT_ZOTERO_BASE_URL
    timeout_seconds: float = 20.0
    limit: int = 100

    def __post_init__(self) -> None:
        if not self.user_id.strip():
            raise ValueError("Zotero user ID cannot be empty")
        if not self.api_key.strip():
            raise ValueError("Zotero API key cannot be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("Zotero timeout must be positive")
        if not 1 <= self.limit <= 100:
            raise ValueError("Zotero limit must be between 1 and 100")


class ZoteroWebApiTransport:
    """Transporte HTTP mínimo para lectura de la biblioteca Zotero del usuario."""

    def __init__(
        self,
        config: ZoteroTransportConfig,
        opener: Callable[..., object] | None = None,
    ) -> None:
        self._config = config
        self._opener = opener or urlopen

    def fetch(self, query: BibliographicQuery) -> RemoteAcquisitionResponse:
        params = self._query_parameters(query)
        path = f"/users/{quote(self._config.user_id, safe='')}/items"
        url = f"{self._config.base_url.rstrip('/')}{path}?{urlencode(params)}"
        request = Request(url, method="GET")
        request.add_header("Accept", "application/json")
        request.add_header("Zotero-API-Version", "3")
        request.add_header("Zotero-API-Key", self._config.api_key)

        with self._opener(request, timeout=self._config.timeout_seconds) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(f"Zotero Web API returned HTTP {status}")
            content = read_remote_response(response)
        raw_content = content.decode("utf-8")
        try:
            json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid Zotero JSON: {exc}") from exc
        return RemoteAcquisitionResponse(
            raw_content=raw_content, source_locator=self._safe_locator(params)
        )

    def _query_parameters(self, query: BibliographicQuery) -> dict[str, str]:
        params = {
            "format": "json",
            "v": "3",
            "limit": str(self._config.limit),
        }
        if query.text.strip():
            params["q"] = query.text
        allowed = {"qmode", "qinclude", "sort", "direction", "start", "collectionKey"}
        for name, value in query.parameters:
            if name not in allowed:
                raise ValueError(f"Unsupported Zotero parameter: {name}")
            params[name] = value
        try:
            limit = int(params["limit"])
        except ValueError as exc:
            raise ValueError("Zotero limit must be an integer") from exc
        if not 1 <= limit <= 100:
            raise ValueError("Zotero limit must be between 1 and 100")
        params["limit"] = str(limit)
        if "start" in params:
            try:
                start = int(params["start"])
            except ValueError as exc:
                raise ValueError("Zotero start must be an integer") from exc
            if start < 0:
                raise ValueError("Zotero start must be non-negative")
            params["start"] = str(start)
        return params

    def _safe_locator(self, params: dict[str, str]) -> str:
        return f"{self._config.base_url.rstrip('/')}/users/{quote(self._config.user_id, safe='')}/items?{urlencode(params)}"
