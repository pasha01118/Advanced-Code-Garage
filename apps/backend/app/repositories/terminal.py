from datetime import datetime, timezone

from app.repositories.base import SupabaseRepository

SNIPPETS = "terminal_snippets"
HISTORY = "terminal_history"


class SnippetsRepository(SupabaseRepository):
    async def list(self, owner_id: str, limit: int = 100) -> list[dict]:
        res = await self._run(
            self.db.table(SNIPPETS)
            .select("*")
            .eq("owner_id", owner_id)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute
        )
        return res.data or []

    async def create(self, owner_id: str, name: str, command: str, description: str = "") -> dict:
        now = datetime.now(timezone.utc).isoformat()
        res = await self._run(
            self.db.table(SNIPPETS)
            .insert(
                {
                    "owner_id": owner_id,
                    "name": name,
                    "command": command,
                    "description": description,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            .execute
        )
        return self._row(res) or {}

    async def update(self, owner_id: str, snippet_id: str, fields: dict) -> dict | None:
        payload = {**fields, "updated_at": datetime.now(timezone.utc).isoformat()}
        res = await self._run(
            self.db.table(SNIPPETS)
            .update(payload)
            .eq("owner_id", owner_id)
            .eq("id", snippet_id)
            .execute
        )
        return self._row(res)

    async def delete(self, owner_id: str, snippet_id: str) -> bool:
        res = await self._run(
            self.db.table(SNIPPETS)
            .delete()
            .eq("owner_id", owner_id)
            .eq("id", snippet_id)
            .execute
        )
        return bool(res.data)


class TerminalHistoryRepository(SupabaseRepository):
    async def list(self, owner_id: str, limit: int = 100) -> list[dict]:
        res = await self._run(
            self.db.table(HISTORY)
            .select("id,command,created_at")
            .eq("owner_id", owner_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute
        )
        return res.data or []

    async def add(self, owner_id: str, command: str) -> dict:
        res = await self._run(
            self.db.table(HISTORY)
            .insert({"owner_id": owner_id, "command": command})
            .execute
        )
        return self._row(res) or {}

    async def clear(self, owner_id: str) -> int:
        res = await self._run(
            self.db.table(HISTORY).delete().eq("owner_id", owner_id).execute
        )
        return len(res.data or [])

    async def prune(self, owner_id: str, keep: int = 200) -> None:
        rows = await self.list(owner_id, limit=1000)
        stale = [row["id"] for row in rows[keep:]]
        if not stale:
            return
        await self._run(self.db.table(HISTORY).delete().in_("id", stale).execute)
