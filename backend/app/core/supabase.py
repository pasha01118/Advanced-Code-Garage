import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        url: str = os.environ.get("SUPABASE_URL", "")
        key: str = os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            raise ValueError("Supabase URL and Key must be set in environment variables.")
        _supabase = create_client(url, key)
    return _supabase
