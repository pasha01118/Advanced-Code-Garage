from datetime import datetime, timezone

from app.repositories.base import SupabaseRepository

DEFAULT_MODE = "AI-Man"


class ModesRepository(SupabaseRepository):
    async def get(self) -> str:
        res = await self._run(
            self.db.table("execution_modes").select("value").eq("key", "system").maybe_single().execute
        )
        if not res.data:
            return DEFAULT_MODE
        return res.data.get("value", DEFAULT_MODE)

    async def set(self, value: str) -> str:
        now = datetime.now(timezone.utc).isoformat()
        res = await self._run(
            self.db.table("execution_modes")
            .update({"value": value, "updated_at": now})
            .eq("key", "system")
            .maybe_single()
            .execute
        )
        if not res.data:
            return value
        return res.data.get("value", value)