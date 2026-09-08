from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from psi_jarvis.domain.ai.assistance import AIAssistanceRequest, AIAssistanceSuggestion


class OllamaError(RuntimeError):
    """Base error for the local Ollama provider."""


class OllamaUnavailableError(OllamaError):
    """Raised when the local Ollama endpoint cannot be reached."""


class OllamaResponseError(OllamaError):
    """Raised when Ollama returns an invalid or unsuccessful response."""


@dataclass(frozen=True)
class OllamaConfig:
    """Connection settings for a local Ollama daemon."""

    base_url: str = "http://127.0.0.1:11434"
    timeout_seconds: float = 60.0

    def __post_init__(self) -> None:
        if not self.base_url.strip():
            raise ValueError("Ollama base_url cannot be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("Ollama timeout_seconds must be positive")

    @classmethod
    def from_environment(cls) -> OllamaConfig:
        """Build local-provider settings without storing credentials in the repo."""
        raw_timeout = os.environ.get("PSI_OLLAMA_TIMEOUT", "60")
        try:
            timeout = float(raw_timeout)
        except ValueError as exc:
            raise ValueError("PSI_OLLAMA_TIMEOUT must be numeric") from exc
        return cls(
            base_url=os.environ.get("PSI_OLLAMA_BASE_URL", cls.base_url),
            timeout_seconds=timeout,
        )


class OllamaClient:
    """Provider adapter; it never creates or changes screening decisions."""

    def __init__(self, config: OllamaConfig | None = None) -> None:
        self.config = config or OllamaConfig.from_environment()

    def list_models(self) -> tuple[str, ...]:
        payload = self._request("/api/tags", {})
        models = payload.get("models", [])
        if not isinstance(models, list):
            raise OllamaResponseError(
                "Ollama /api/tags returned an invalid models field"
            )
        names = []
        for model in models:
            if (
                isinstance(model, dict)
                and isinstance(model.get("name"), str)
                and model["name"].strip()
            ):
                names.append(model["name"].strip())
        return tuple(names)

    def generate(self, request: AIAssistanceRequest) -> AIAssistanceSuggestion:
        prompt = (
            "You are an auxiliary scientific literature assistant. "
            "Do not make or imply a final screening decision. "
            "Provide concise evidence-oriented observations that a human reviewer can inspect.\n\n"
            f"Title: {request.title}\n\n"
            f"Abstract:\n{request.abstract}\n\n"
            "Return observations only; do not label the paper as included or excluded."
        )
        payload = self._request(
            "/api/generate",
            {
                "model": request.model,
                "prompt": prompt,
                "stream": False,
            },
        )
        output = payload.get("response")
        if not isinstance(output, str) or not output.strip():
            raise OllamaResponseError(
                "Ollama /api/generate returned no textual response"
            )
        return AIAssistanceSuggestion(
            paper_id=request.paper_id,
            model=request.model,
            prompt_version=request.prompt_version,
            input_hash=request.input_hash,
            output=output.strip(),
        )

    def _request(self, path: str, body: dict) -> dict:
        url = self.config.base_url.rstrip("/") + path
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        if path == "/api/tags":
            request = urllib.request.Request(
                url, headers={"Accept": "application/json"}, method="GET"
            )
        try:
            with urllib.request.urlopen(
                request, timeout=self.config.timeout_seconds
            ) as response:
                raw = response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise OllamaUnavailableError(
                f"Cannot reach Ollama at {self.config.base_url}"
            ) from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OllamaResponseError("Ollama returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise OllamaResponseError("Ollama returned an invalid JSON object")
        if "error" in payload:
            raise OllamaResponseError(str(payload["error"]))
        return payload
