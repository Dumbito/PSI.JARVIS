from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from psi_jarvis.application.acquisition.contracts import BibliographicQuery
from psi_jarvis.infrastructure.acquisition.remote_base import (
    RemoteAcquisitionResponse,
    read_remote_response,
)

DEFAULT_SCOPUS_BASE_URL = "https://api.elsevier.com/content/search/scopus"
MAX_SCOPUS_COUNT = 200


@dataclass(frozen=True)
class ScopusTransportConfig:
    """Configuración del transporte Scopus sin secretos persistidos."""

    api_key: str
    insttoken: str | None = None
    auth_token: str | None = None
    base_url: str = DEFAULT_SCOPUS_BASE_URL
    timeout_seconds: float = 20.0
    count: int = 20

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise ValueError("Scopus API key cannot be empty")
        if self.insttoken is not None and not self.insttoken.strip():
            raise ValueError("Scopus institution token cannot be empty")
        if self.auth_token is not None and not self.auth_token.strip():
            raise ValueError("Scopus authentication token cannot be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("Scopus timeout must be positive")
        if not 1 <= self.count <= MAX_SCOPUS_COUNT:
            raise ValueError(f"Scopus count must be between 1 and {MAX_SCOPUS_COUNT}")


class ScopusSearchTransport:
    """Transporte HTTP mínimo para Scopus Search API en JSON."""

    def __init__(
        self,
        config: ScopusTransportConfig,
        opener: Callable[..., object] | None = None,
    ) -> None:
        self._config = config
        self._opener = opener or urlopen

    def fetch(self, query: BibliographicQuery) -> RemoteAcquisitionResponse:
        params = self._common_query_params()
        params.update(self._query_parameters(query))
        params["query"] = query.text
        params["count"] = str(self._config.count)

        raw_content, request_url = self._request(params)
        self._validate_json(raw_content)
        return RemoteAcquisitionResponse(
            raw_content=raw_content, source_locator=request_url
        )

    def _request(self, params: Mapping[str, str]) -> tuple[str, str]:
        url = f"{self._config.base_url.rstrip('/')}?{urlencode(dict(params))}"
        request = Request(url, method="GET")
        request.add_header("Accept", "application/json")
        request.add_header("X-ELS-APIKey", self._config.api_key)
        if self._config.insttoken:
            request.add_header("X-ELS-Insttoken", self._config.insttoken)
        if self._config.auth_token:
            request.add_header("Authorization", f"Bearer {self._config.auth_token}")

        with self._opener(request, timeout=self._config.timeout_seconds) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(f"Scopus Search API returned HTTP {status}")
            content = read_remote_response(response)
        return content.decode("utf-8"), self._safe_source_locator(params)

    @staticmethod
    def _common_query_params() -> dict[str, str]:
        return {"httpAccept": "application/json"}

    def _query_parameters(self, query: BibliographicQuery) -> dict[str, str]:
        allowed = {
            "view",
            "field",
            "suppressNavLinks",
            "date",
            "start",
            "sort",
            "content",
            "subj",
            "alias",
            "facets",
            "ver",
        }
        parameters: dict[str, str] = {}
        for name, value in query.parameters:
            if name == "count":
                raise ValueError(
                    "Scopus count is controlled by transport configuration"
                )
            if name not in allowed:
                raise ValueError(f"Unsupported Scopus Search parameter: {name}")
            parameters[name] = value

        raw_start = parameters.get("start")
        if raw_start is not None:
            try:
                start = int(raw_start)
            except ValueError as exc:
                raise ValueError("Scopus start must be a non-negative integer") from exc
            if start < 0:
                raise ValueError("Scopus start must be a non-negative integer")
            parameters["start"] = str(start)

        return parameters

    @staticmethod
    def _validate_json(content: str) -> None:
        try:
            json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid Scopus Search JSON: {exc}") from exc

    def _safe_source_locator(self, params: Mapping[str, str]) -> str:
        return f"{self._config.base_url.rstrip('/')}?{urlencode(dict(params))}"
