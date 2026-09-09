from psi_jarvis.gui.i18n_generator import extract_gui_strings


def test_translation_extractor_includes_long_form_help_and_tutorial_copy():
    strings = set(extract_gui_strings())

    assert "Welcome to PSI.JARVIS" in strings
    assert "A reproducible workspace for scientific paper acquisition, deterministic screening, analysis, provenance and reporting. The scientific rules live outside the GUI." in strings
    assert "Create your first review project to define a protocol before importing papers." in strings
    assert "Use Papers → Import & screen to load CSV, Excel or RIS files. PSI.JARVIS normalizes metadata, removes duplicates and sends the corpus through the same screening pipeline used by the rest of the system." in strings
    assert "Use a local Ollama model for auxiliary observations. This never changes the screening decision." in strings
