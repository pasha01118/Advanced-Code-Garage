import os
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
        validation_alias=AliasChoices(
            "SUPABASE_PUBLISHABLE_KEY",
            "SUPABASE_ANON_KEY",
            "SUPABASE_KEY",
        ),
    )
    supabase_service_role_key: str = ""

    secret_key: str = "change-me"
    # Optional dedicated key for encrypting user AI-provider API keys.
    # Falls back to SECRET_KEY when unset.
    user_key_encryption_key: str = ""
    # If set, first-run Admin Sign-Up additionally requires this token.
    app_bootstrap_token: str = ""
    # Comma-separated JWT 'sub' allowlist that may act as admin even without
    # the app_metadata.role claim (legacy accounts).
    admin_user_ids: str = ""
    # Token that unlocks the admin "forgot password" reset (no email possible).
    admin_reset_token: str = ""
    # Seconds between Sentinel self-healing cycles. Never allow a busy loop.
    sentinel_interval_seconds: int = Field(default=60, ge=1)
    # Max auth-sensitive requests per IP per minute (in-process best effort).
    auth_rate_limit_per_minute: int = Field(default=10, ge=1)
    # Only these socket peers may supply X-Forwarded-For (e.g. Render's proxies).
    trusted_proxy_cidrs: str = ""
    # Bearer token required by the Vercel Cron endpoint that replaces the
    # in-process Sentinel loop on serverless runtimes.
    cron_secret: str = ""

    # GitHub App foundation. Private key is PEM text with literal \n allowed.
    github_app_id: str = ""
    github_app_slug: str = ""
    github_app_private_key: str = ""
    github_app_webhook_secret: str = ""

    # Versioned envelope-encryption keys for the repository secrets vault.
    # Previous KEKs use "v1:<secret>,v2:<secret>" so rotation never breaks reads.
    vault_kek_version: str = "v1"
    vault_previous_keks: str = ""

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    google_ai_studio_key: str = ""
    google_ai_studio_proxy: str = ""
    google_ai_studio_proxy_token: str = ""
    ollama_base_url: str = "http://localhost:11434"

    frontend_urls: str = ""
    # Anchored: Starlette uses re.match, so without `$` an attacker domain like
    # https://preview.vercel.app.evil.tld would be trusted with credentials.
    frontend_origin_regex: str = r"^https://[a-zA-Z0-9-]+\.vercel\.app$"

    environment: str = "development"

    @property
    def cors_origins(self) -> list[str]:
        if not self.frontend_urls.strip():
            return list(DEFAULT_CORS_ORIGINS)
        return [origin.strip() for origin in self.frontend_urls.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_serverless(self) -> bool:
        """Vercel Functions are per-request, so process-lifetime work cannot run."""
        return bool(os.environ.get("VERCEL"))


@lru_cache
def get_settings() -> Settings:
    return Settings()