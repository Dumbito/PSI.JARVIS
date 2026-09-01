from psi_jarvis.core.settings import Settings


def test_settings_defaults():
    settings = Settings()

    assert settings.app_name == "PSI.JARVIS"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.debug is False


def test_settings_environment_override(monkeypatch):
    monkeypatch.setenv("PSI_JARVIS_DEBUG", "true")

    settings = Settings()

    assert settings.debug is True
