from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Liminal"
    app_version: str = "0.1.0"

    data_dir: Path = Path(__file__).parent.parent.parent / "data"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4-turbo"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 4000

    cors_origins: list[str] = ["http://localhost:3000"]

    session_default_working_dir: str = "/workspace/default"
    session_default_language: str = "en-US"

    tool_allowed_paths: list[str] = ["/workspace"]

    @property
    def sessions_dir(self) -> Path:
        return self.data_dir / "sessions"

    @property
    def knowledge_dir(self) -> Path:
        return self.data_dir / "knowledge"

    @property
    def config_dir(self) -> Path:
        return self.data_dir / "config"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"


settings = Settings()
