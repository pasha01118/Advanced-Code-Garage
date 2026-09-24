from supabase import create_client, Client

from app.core.config import get_settings

_supabase: Client | None = None


def get_supabase() -> Client:
    """Server-side Supabase client.

    Prefers the service-role key so RLS never blocks the trusted backend,
    and falls back to the anon key for local/dev use.
    """
    global _supabase
    if _supabase is None:
        settings = get_settings()
        if not settings.supabase_url:
            raise ValueError("SUPABASE_URL must be set in environment variables.")
        key = settings.supabase_service_role_key or settings.supabase_anon_key
        if not key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set.")
        _supabase = create_client(settings.supabase_url, key)
    return _supabase