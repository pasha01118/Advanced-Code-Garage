import asyncio
from typing import Any

from supabase import Client

from app.core.supabase import get_supabase


class SupabaseRepository:
    """Base repository: lazily resolves the Supabase client and offloads the
    synchronous SDK calls off the event loop."""

    def __init__(self, db: Client | None = None) -> None:
        self._db = db

    @property
    def db(self) -> Client:
        if self._db is None:
            self._db = get_supabase()
        return self._db

    async def _run(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        def call() -> Any:
            return fn(*args, **kwargs)

        return await asyncio.to_thread(call)

    @staticmethod
    def _row(res: Any) -> dict | None:
        """Normalise postgrest results (list or dict) into a single row."""
        data = getattr(res, "data", None)
        if isinstance(data, dict):
            return data if data else None
        if isinstance(data, list):
            return data[0] if data else None
        return None