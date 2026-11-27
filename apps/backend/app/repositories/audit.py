from app.repositories.base import SupabaseRepository

TABLENAME = "audit_log"


class AuditRepository(SupabaseRepository):
    async def add(
        self,
        actor: str,
        action: str,
        target: str | None = None,
        detail: dict | None = None,
        owner_id: str | None = None,
    ) -> dict:
        payload: dict = {"actor": actor, "action": action}
        if target:
            payload["target"] = target
        if detail:
            payload["detail"] = detail
        if owner_id:
            payload["owner_id"] = owner_id
        res = await self._run(self.db.table(TABLENAME).insert(payload).execute)
        rows = res.data or []
        return rows[0] if rows else {}

    async def list(
        self,
        owner_id: str | None = None,
        *,
        limit: int = 100,
        action: str | None = None,
        since: str | None = None,
    ) -> list[dict]:
        query = self.db.table(TABLENAME).select("*")
        if owner_id:
            query = query.eq("owner_id", owner_id)
        if action:
            query = query.eq("action", action)
        if since:
            query = query.gte("created_at", since)
        res = await self._run(
            query.order("created_at", desc=True).limit(limit).execute
        )
        return res.data or []
