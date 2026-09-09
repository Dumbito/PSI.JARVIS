from __future__ import annotations

from psi_jarvis.gui.ai_assistant import MODES, PROMPT_VERSION, _build_prompt
from psi_jarvis.gui.i18n import tr


def test_jarvis_agent_has_scientific_modes_and_spanish_prompt():
    names = [name for name, _ in MODES]
    assert "PICO" in names
    assert "Metodología" in names
    assert "Posibles criterios de exclusión" in names
    assert PROMPT_VERSION == "jarvis-agent-v2-es"
    prompt = _build_prompt(
        "PICO",
        "Extrae PICO.",
        "Título de prueba",
        "Abstract de prueba",
        "Incluir adultos",
    )
    assert "Responde en español" in prompt
    assert "No emitas una decisión final" in prompt
    assert "Título de prueba" in prompt
    assert "Abstract de prueba" in prompt
    assert "Incluir adultos" in prompt


def test_spanish_translation_covers_main_navigation():
    assert tr("Dashboard") == "Panel"
    assert tr("Projects") == "Proyectos"
    assert tr("Papers") == "Artículos"
    assert tr("Reports") == "Informes"
    assert tr("Settings") == "Configuración"
