from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://advanced-code-garage-rgke.vercel.app",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    supabase_url: str = ""
    supabase_anon_key: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_ANON_KEY", "SUPABASE_KEY"),
    )
    supabase_service_role_key: str = ""

    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    google_ai_studio_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    frontend_urls: str = ""
    frontend_origin_regex: str = r"https://[a-zA-Z0-9-]+\.vercel\.app"

    environment: str = "development"

    @property
    def cors_origins(self) -> list[str]:
        if not self.frontend_urls.strip():
            return list(DEFAULT_CORS_ORIGINS)
        return [origin.strip() for origin in self.frontend_urls.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()