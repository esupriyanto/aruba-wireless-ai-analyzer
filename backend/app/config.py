"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class ArubaSettings(BaseSettings):
    """Aruba Wireless Controller connection settings."""

    model_config = {"env_prefix": "ARUBA_"}

    controller_host: str = "192.168.1.1"
    controller_port: int = 4343
    username: str = "admin"
    password: str = ""
    api_version: str = "v1"
    ssl_verify: bool = False


class HermesSettings(BaseSettings):
    """Hermes AI Agent connection settings."""

    model_config = {"env_prefix": "HERMES_"}

    agent_url: str = "http://hermes:8080"
    api_key: str = ""


class LLMSettings(BaseSettings):
    """LLM provider settings."""

    model_config = {"env_prefix": "LLM_"}

    provider: str = "openrouter"
    model: str = "anthropic/claude-sonnet-4"
    openrouter_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"


class AppSettings(BaseSettings):
    """General application settings."""

    model_config = {"env_prefix": ""}

    mock_mode: bool = True
    poll_interval_seconds: int = 30
    alert_rssi_threshold: int = -75
    alert_channel_util_threshold: int = 80
    log_level: str = "INFO"


class Settings:
    """Root settings container that composes all sub-settings."""

    def __init__(self) -> None:
        self.aruba = ArubaSettings()
        self.hermes = HermesSettings()
        self.llm = LLMSettings()
        self.app = AppSettings()

    @property
    def mock_mode(self) -> bool:
        return self.app.mock_mode


settings = Settings()
