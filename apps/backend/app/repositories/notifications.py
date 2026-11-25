from datetime import datetime, timezone

from app.repositories.base import SupabaseRepository

TABLENAME = "notifications"


class NotificationsRepository(SupabaseRepository):
    async def list(self, owner_id: str, limit: int = 100, unread_only: bool = False) -> list[dict]:
        query = self.db.table(TABLENAME).select("*").eq("owner_id", owner_id)
        if unread_only:
            query = query.is_("read_at", None)
        res = await self._run(
            query.order("created_at", desc=True).limit(limit).execute
        )
        return res.data or []

    async def find_source(self, owner_id: str, source: str, source_id: str) -> dict | None:
        res = await self._run(
            self.db.table(TABLENAME)
            .select("*")
            .eq("owner_id", owner_id)
            .eq("source", source)
            .eq("source_id", source_id)
            .limit(1)
            .execute
        )
        return self._row(res)

    async def create(
        self,
        owner_id: str,
        *,
        title: str,
        body: str = "",
        type: str = "info",
        source: str = "system",
        source_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        res = await self._run(
            self.db.table(TABLENAME)
            .insert(
                {
                    "owner_id": owner_id,
                    "type": type,
                    "title": title,
                    "body": body,
                    "source": source,
                    "source_id": source_id,
                    "metadata": metadata or {},
                }
            )
            .execute
        )
        return self._row(res) or {}

    async def mark_read(self, owner_id: str, notification_id: str) -> dict | None:
        res = await self._run(
            self.db.table(TABLENAME)
            .update({"read_at": datetime.now(timezone.utc).isoformat()})
            .eq("owner_id", owner_id)
            .eq("id", notification_id)
            .execute
        )
        return self._row(res)

    async def mark_all_read(self, owner_id: str) -> int:
        res = await self._run(
            self.db.table(TABLENAME)
            .update({"read_at": datetime.now(timezone.utc).isoformat()})
            .eq("owner_id", owner_id)
            .is_("read_at", None)
            .execute
        )
        return len(res.data or [])

    async def delete(self, owner_id: str, notification_id: str) -> bool:
        res = await self._run(
            self.db.table(TABLENAME)
            .delete()
            .eq("owner_id", owner_id)
            .eq("id", notification_id)
            .execute
        )
        return bool(res.data)

    async def clear(self, owner_id: str) -> int:
        res = await self._run(
            self.db.table(TABLENAME).delete().eq("owner_id", owner_id).execute
        )
        return len(res.data or [])
