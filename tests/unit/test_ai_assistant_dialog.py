"""GUI-level regression coverage for the JARVIS/Ollama assistant dialog.

Everything under gui/ai_assistant.py was previously only exercised at
the OllamaClient/domain-contract level (mocked HTTP calls, no real
QDialog). This drives the actual AIAssistantDialog end to end with a
fake client standing in for Ollama, confirming what a manual test
already found by hand: the dialog degrades gracefully when Ollama is
unavailable, and correctly displays a real suggestion - always
labelled as auxiliary, never as a scientific decision - when a model
responds successfully.
"""

from __future__ import annotations

import psi_jarvis.gui.ai_assistant as ai_assistant_module
from psi_jarvis.domain.ai.assistance import AIAssistanceSuggestion
from psi_jarvis.infrastructure.ollama_client import OllamaUnavailableError

SAMPLE_DETAILS = {
    "title": "Dermatologist-level classification of skin cancer",
    "abstract": "A deep learning approach to skin lesion classification.",
    "paper_id": "11111111-1111-1111-1111-111111111111",
}


class _FakeClientUnavailable:
    def list_models(self):
        raise OllamaUnavailableError("Cannot reach Ollama at http://127.0.0.1:11434")

    def generate(self, request):
        raise AssertionError("generate() should not be reachable with no model")


class _FakeClientWithModel:
    def list_models(self):
        return ("llama3",)

    def generate(self, request):
        return AIAssistanceSuggestion(
            paper_id=request.paper_id,
            model=request.model,
            prompt_version=request.prompt_version,
            input_hash=request.input_hash,
            output="Population: skin lesion images. No final decision implied.",
        )


def test_dialog_disables_analysis_when_ollama_is_unavailable(qtbot, monkeypatch):
    monkeypatch.setattr(
        ai_assistant_module, "OllamaClient", lambda: _FakeClientUnavailable()
    )
    dialog = ai_assistant_module.AIAssistantDialog(SAMPLE_DETAILS)
    qtbot.addWidget(dialog)

    qtbot.waitUntil(lambda: "unavailable" in dialog.status.text().lower(), timeout=2000)

    assert dialog.ask.isEnabled() is False
    assert "127.0.0.1:11434" in dialog.status.text()


def test_dialog_shows_a_labeled_auxiliary_suggestion_on_success(qtbot, monkeypatch):
    monkeypatch.setattr(
        ai_assistant_module, "OllamaClient", lambda: _FakeClientWithModel()
    )
    dialog = ai_assistant_module.AIAssistantDialog(SAMPLE_DETAILS)
    qtbot.addWidget(dialog)

    qtbot.waitUntil(lambda: dialog.ask.isEnabled(), timeout=2000)
    assert dialog.models.currentText() == "llama3"

    dialog.ask.click()
    qtbot.waitUntil(lambda: bool(dialog.output.toPlainText()), timeout=2000)

    assert "No final decision implied" in dialog.output.toPlainText()
    assert "assistant-only" in dialog.status.text()
    assert "llama3" in dialog.status.text()
