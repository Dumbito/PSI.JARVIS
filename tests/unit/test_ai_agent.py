from __future__ import annotations

from psi_jarvis.gui.ai_assistant import MODES, PROMPT_VERSION, _build_prompt


def test_jarvis_agent_has_scientific_modes_and_spanish_prompt():
    names = [name for name, _ in MODES]
    assert "PICO" in names
    assert "Methodology" in names
    assert "Possible exclusion criteria" in names
    assert PROMPT_VERSION == "jarvis-agent-v2-es"
    prompt = _build_prompt(
        "PICO",
        "Extrae PICO.",
        "Título de prueba",
        "Abstract de prueba",
        "Incluir adultos",
    )
    assert "Respond in Spanish" in prompt
    assert "Do not issue a final inclusion/exclusion decision" in prompt
    assert "Título de prueba" in prompt
    assert "Abstract de prueba" in prompt
    assert "Incluir adultos" in prompt
