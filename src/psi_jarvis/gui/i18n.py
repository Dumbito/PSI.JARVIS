from __future__ import annotations

from psi_jarvis.gui.i18n_manager import BUILTIN


def tr(text: str, language: str = "es") -> str:
    """Compatibility helper for legacy callers; runtime GUI uses LanguageManager."""
    return BUILTIN.get(language, {}).get(text, text)
