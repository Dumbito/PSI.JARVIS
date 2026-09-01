from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PSI.JARVIS"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_prefix="PSI_JARVIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
