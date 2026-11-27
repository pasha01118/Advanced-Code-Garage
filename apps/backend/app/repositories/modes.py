from datetime import datetime, timezone

from app.repositories.base import SupabaseRepository

DEFAULT_MODE = "AI-Man"


class ModesRepository(SupabaseRepository):
    async def get(self) -> str:
        res = await self._run(
            self.db.table("execution_modes").select("value").eq("key", "system").limit(1).execute
        )
        row = self._row(res)
        if not row:
            return DEFAULT_MODE
        return row.get("value", DEFAULT_MODE)

    async def set(self, value: str) -> str:
        now = datetime.now(timezone.utc).isoformat()
        # Upsert so a missing seed row cannot silently swallow a mode change.
        res = await self._run(
            self.db.table("execution_modes")
            .upsert({"key": "system", "value": value, "updated_at": now}, on_conflict="key")
            .execute
        )
        row = self._row(res)
        return row.get("value", value) if row else value