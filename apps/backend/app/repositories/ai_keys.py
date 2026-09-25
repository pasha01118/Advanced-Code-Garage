from datetime import datetime, timezone

from app.repositories.base import SupabaseRepository

TABLENAME = "user_ai_keys"


class AIKeysRepository(SupabaseRepository):
    """Per-user AI provider keys. Plaintext never touches the DB: the service
    encrypts before persisting and decrypts after reading."""

    async def upsert(
        self,
        owner_id: str,
        provider: str,
        *,
        key_ciphertext: str | None = None,
        ollama_base_url: str | None = None,
        status: str = "untested",
        message: str = "",
    ) -> dict:
        payload: dict = {
            "owner_id": owner_id,
            "provider": provider,
            "status": status,
            "message": message,
        }
        if key_ciphertext:
            payload["key_ciphertext"] = key_ciphertext
        if ollama_base_url:
            payload["ollama_base_url"] = ollama_base_url
        res = await self._run(
            self.db.table(TABLENAME)
            .upsert(payload, on_conflict="owner_id,provider")
            .execute
        )
        rows = res.data or []
        return rows[0] if rows else payload

    async def get(self, owner_id: str, provider: str) -> dict | None:
        res = await self._run(
            self.db.table(TABLENAME)
            .select("*")
            .eq("owner_id", owner_id)
            .eq("provider", provider)
            .limit(1)
            .execute
        )
        return self._row(res)

    async def list_by_owner(self, owner_id: str) -> list[dict]:
        res = await self._run(
            self.db.table(TABLENAME)
            .select("*")
            .eq("owner_id", owner_id)
            .order("provider")
            .execute
        )
        return res.data or []

    async def update_status(
        self,
        owner_id: str,
        provider: str,
        *,
        status: str,
        message: str = "",
        model_count: int = 0,
    ) -> dict | None:
        res = await self._run(
            self.db.table(TABLENAME)
            .update(
                {
                    "status": status,
                    "message": message,
                    "model_count": model_count,
                    "last_validated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("owner_id", owner_id)
            .eq("provider", provider)
            .execute
        )
        return self._row(res)

    async def delete(self, owner_id: str, provider: str) -> bool:
        res = await self._run(
            self.db.table(TABLENAME)
            .delete()
            .eq("owner_id", owner_id)
            .eq("provider", provider)
            .execute
        )
        rows = res.data or []
        return bool(rows)

    async def aggregate_providers(self) -> list[dict]:
        """Per-provider health across all users (for the Sentinel scan)."""
        res = await self._run(
            self.db.table(TABLENAME).select("provider,status,message,model_count").execute
        )
        aggregated: dict[str, dict] = {}
        for row in res.data or []:
            provider = row.get("provider")
            status = row.get("status", "untested")
            entry = aggregated.setdefault(
                provider,
                {"provider": provider, "configured": 0, "active": 0, "error": 0, "quota": 0,
                 "models": 0, "messages": []},
            )
            entry["configured"] += 1
            entry["models"] += row.get("model_count", 0) or 0
            if status == "active":
                entry["active"] += 1
            elif status == "error":
                entry["error"] += 1
            elif status == "quota":
                entry["quota"] += 1
            if row.get("message"):
                entry["messages"].append(row.get("message"))
        return sorted(aggregated.values(), key=lambda e: e["provider"])