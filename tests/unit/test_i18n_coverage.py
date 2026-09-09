from __future__ import annotations

from psi_jarvis.gui.i18n_generator import extract_gui_strings


def test_i18n_extractor_keeps_long_form_gui_copy():
    source = set(extract_gui_strings())
    assert source
    assert any(len(value) > 200 for value in source)
    assert any("reproducible workspace" in value.lower() for value in source)
    assert any("screening" in value.lower() for value in source)
