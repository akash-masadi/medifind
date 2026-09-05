from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Reads SIDECAR_* env vars, falling back to a .env file.
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SIDECAR_", extra="ignore")

    environment: str = "development"
    api_token: str = "dev-token-change-me"

    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout_seconds: float = 4.0
    groq_max_tokens: int = 400

    max_symptoms: int = 12
    max_symptom_chars: int = 400


@lru_cache
def get_settings() -> Settings:
    # Cached — settings are read once per process, not per request.
    return Settings()