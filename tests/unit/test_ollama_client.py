from __future__ import annotations

import json
import urllib.error

import pytest

from psi_jarvis.domain.ai.assistance import AIAssistanceRequest
from psi_jarvis.infrastructure.ollama_client import (
    OllamaClient,
    OllamaConfig,
    OllamaResponseError,
    OllamaUnavailableError,
)


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def request() -> AIAssistanceRequest:
    return AIAssistanceRequest(
        paper_id="paper-1",
        title="Neural correlates of memory",
        abstract="A short abstract.",
        model="qwen3:8b",
        prompt_version="assistant-v1",
        input_hash="abc123",
    )


def test_list_models_uses_ollama_tags(monkeypatch):
    def fake_urlopen(req, timeout):
        assert req.full_url == "http://127.0.0.1:11434/api/tags"
        assert req.method == "GET"
        assert timeout == 12
        return FakeResponse({"models": [{"name": "qwen3:8b"}, {"name": "llama3.1:8b"}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = OllamaClient(OllamaConfig(timeout_seconds=12))
    assert client.list_models() == ("qwen3:8b", "llama3.1:8b")


def test_generate_returns_assistant_only_suggestion(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        assert req.full_url.endswith("/api/generate")
        assert req.method == "POST"
        assert timeout == 60
        return FakeResponse({"response": "The abstract reports a memory-related neural association."})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    suggestion = OllamaClient().generate(request())

    assert suggestion.paper_id == "paper-1"
    assert suggestion.model == "qwen3:8b"
    assert suggestion.prompt_version == "assistant-v1"
    assert suggestion.input_hash == "abc123"
    assert suggestion.authority == "assistant-only"
    assert "final screening decision" in captured["payload"]["prompt"]
    assert captured["payload"]["stream"] is False


def test_generate_rejects_empty_response(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout: FakeResponse({"response": ""}))
    with pytest.raises(OllamaResponseError, match="no textual response"):
        OllamaClient().generate(request())


def test_unavailable_ollama_is_explicit(monkeypatch):
    def fake_urlopen(req, timeout):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(OllamaUnavailableError, match="Cannot reach Ollama"):
        OllamaClient().list_models()
