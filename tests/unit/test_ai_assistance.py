import pytest

from psi_jarvis.domain.ai.assistance import AIAssistanceRequest, AIAssistanceSuggestion


def test_ai_request_requires_provenance_fields():
    request = AIAssistanceRequest(
        paper_id="paper-1",
        title="A paper",
        abstract="An abstract",
        model="local-model",
        prompt_version="screening-helper-v1",
        input_hash="sha256:abc",
    )

    assert request.model == "local-model"
    assert request.prompt_version == "screening-helper-v1"
    assert request.input_hash == "sha256:abc"


def test_ai_suggestion_is_explicitly_non_authoritative():
    suggestion = AIAssistanceSuggestion(
        paper_id="paper-1",
        model="local-model",
        prompt_version="screening-helper-v1",
        input_hash="sha256:abc",
        output="Possible relevance cues",
        confidence=0.8,
    )

    assert suggestion.authority == "assistant-only"
    with pytest.raises(RuntimeError, match="cannot become scientific screening decisions"):
        suggestion.as_scientific_decision()


def test_ai_suggestion_rejects_invalid_confidence():
    with pytest.raises(ValueError, match="between 0 and 1"):
        AIAssistanceSuggestion(
            paper_id="paper-1",
            model="local-model",
            prompt_version="v1",
            input_hash="sha256:abc",
            output="Suggestion",
            confidence=1.1,
        )
