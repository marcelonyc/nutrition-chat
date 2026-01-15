from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    app_name: str = "Nutrition Chat"
    ollama_model: str = "llama3.2:1b"
    ollama_api_base: str = "http://localhost:11434"
    ollama_api_token: str | None = None
    system_prompt: str = "You are a helpful assistant."
    database_url: str = "sqlite:///./data/chat.db"
    memory_token_limit: int = 3200
    admin_user: str | None = None
    admin_password: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
