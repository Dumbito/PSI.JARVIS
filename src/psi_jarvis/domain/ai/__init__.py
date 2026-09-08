"""Auxiliary AI/NLP contracts.

The AI layer is intentionally separate from deterministic screening. It may
produce suggestions and provenance, but it cannot represent or mutate a
scientific screening decision.
"""

from psi_jarvis.domain.ai.assistance import AIAssistanceSuggestion, AIAssistanceRequest

__all__ = ["AIAssistanceRequest", "AIAssistanceSuggestion"]
