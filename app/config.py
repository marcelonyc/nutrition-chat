from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    # Application settings
    app_name: str = "Nutrition Chat"
    
    # LLM settings
    ollama_model: str = "llama3.2:1b"
    ollama_api_base: str = "http://localhost:11434"
    ollama_api_token: str | None = None
    system_prompt: str = "You are a helpful assistant."
    memory_token_limit: int = 3200
    
    # Database settings
    database_url: str = "sqlite:///./data/chat.db"
    
    # Security settings
    secret_key: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days
    
    # Admin settings (for initial setup)
    admin_user: str | None = None
    admin_password: str | None = None
    admin_email: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Create a module-level settings instance for convenience
settings = get_settings()
