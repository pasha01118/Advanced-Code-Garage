from datetime import datetime, timezone

from app.repositories.base import SupabaseRepository

TABLENAME = "user_preferences"

DEFAULTS: dict = {
    "theme": "dark",
    "accent": "blue",
    "density": "comfortable",
    "reduced_motion": False,
}


class PreferencesRepository(SupabaseRepository):
    """Per-user appearance settings, with safe in-memory defaults."""

    async def get(self, owner_id: str) -> dict:
        res = await self._run(
            self.db.table(TABLENAME).select("*").eq("owner_id", owner_id).limit(1).execute
        )
        row = self._row(res) or {}
        return {**DEFAULTS, **{k: row[k] for k in DEFAULTS if k in row},
                "updated_at": row.get("updated_at")}

    async def upsert(self, owner_id: str, changes: dict) -> dict:
        current = await self.get(owner_id)
        payload = {
            "owner_id": owner_id,
            **{key: current[key] for key in DEFAULTS},
            **{key: value for key, value in changes.items() if value is not None and key in DEFAULTS},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        res = await self._run(
            self.db.table(TABLENAME).upsert(payload, on_conflict="owner_id").execute
        )
        row = self._row(res) or payload
        return {**DEFAULTS, **{k: row[k] for k in DEFAULTS if k in row},
                "updated_at": row.get("updated_at")}
