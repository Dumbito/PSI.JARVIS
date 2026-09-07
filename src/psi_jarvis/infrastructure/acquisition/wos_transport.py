from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from psi_jarvis.application.acquisition.contracts import BibliographicQuery
from psi_jarvis.infrastructure.acquisition.remote_base import (
    RemoteAcquisitionResponse,
    read_remote_response,
)


DEFAULT_WOS_STARTER_BASE_URL = "https://api.clarivate.com/apis/wos-starter/v1"


@dataclass(frozen=True)
class WebOfScienceTransportConfig:
    """Configuración del Web of Science Starter API."""

    api_key: str
    base_url: str = DEFAULT_WOS_STARTER_BASE_URL
    timeout_seconds: float = 20.0
    limit: int = 50
    database: str = "WOS"

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise ValueError("Web of Science API key cannot be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("Web of Science timeout must be positive")
        if not 1 <= self.limit <= 50:
            raise ValueError("Web of Science limit must be between 1 and 50")
        if not self.database.strip():
            raise ValueError("Web of Science database cannot be empty")


class WebOfScienceStarterTransport:
    """Transporte HTTP mínimo para Web of Science Starter API."""

    def __init__(
        self,
        config: WebOfScienceTransportConfig,
        opener: Callable[..., object] | None = None,
    ) -> None:
        self._config = config
        self._opener = opener or urlopen

    def fetch(self, query: BibliographicQuery) -> RemoteAcquisitionResponse:
        params = self._query_parameters(query)
        url = f"{self._config.base_url.rstrip('/')}/documents?{urlencode(params)}"
        request = Request(url, method="GET")
        request.add_header("Accept", "application/json")
        request.add_header("X-ApiKey", self._config.api_key)

        with self._opener(request, timeout=self._config.timeout_seconds) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(f"Web of Science Starter API returned HTTP {status}")
            content = read_remote_response(response)
        raw_content = content.decode("utf-8")
        try:
            json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid Web of Science JSON: {exc}") from exc
        return RemoteAcquisitionResponse(raw_content=raw_content, source_locator=url)

    def _query_parameters(self, query: BibliographicQuery) -> dict[str, str]:
        params = {
            "db": self._config.database,
            "q": query.text,
            "limit": str(self._config.limit),
            "page": "1",
        }
        allowed = {"db", "limit", "page", "sortField", "detail", "modifiedTimeSpan"}
        for name, value in query.parameters:
            if name not in allowed:
                raise ValueError(f"Unsupported Web of Science parameter: {name}")
            params[name] = value
        if "limit" in params:
            try:
                limit = int(params["limit"])
            except ValueError as exc:
                raise ValueError("Web of Science limit must be an integer") from exc
            if not 1 <= limit <= 50:
                raise ValueError("Web of Science limit must be between 1 and 50")
            params["limit"] = str(limit)
        try:
            page = int(params.get("page", "1"))
        except ValueError as exc:
            raise ValueError("Web of Science page must be an integer") from exc
        if page < 1:
            raise ValueError("Web of Science page must be positive")
        params["page"] = str(page)
        return params
