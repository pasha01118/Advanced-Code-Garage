import os

from app.core.config import Settings


def test_settings_read_uppercase_env_names(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://ref.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-token")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-token")

    settings = Settings()

    assert settings.supabase_url == "https://ref.supabase.co"
    assert settings.supabase_anon_key == "anon-token"
    assert settings.supabase_service_role_key == "service-token"


def test_settings_read_legacy_supabase_key_env_name(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://ref.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "legacy-token")

    settings = Settings()

    assert settings.supabase_anon_key == "legacy-token"