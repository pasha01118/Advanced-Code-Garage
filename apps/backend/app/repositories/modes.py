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
        res = await self._run(
            self.db.table("execution_modes")
            .update({"value": value, "updated_at": now})
            .eq("key", "system")
            .execute
        )
        row = self._row(res)
        if not row:
            return value
        return row.get("value", value)