from app.repositories.base import SupabaseRepository


class AuditRepository(SupabaseRepository):
    async def add(self, actor: str, action: str, target: str | None = None, detail: dict | None = None) -> dict:
        payload: dict = {"actor": actor, "action": action}
        if target:
            payload["target"] = target
        if detail:
            payload["detail"] = detail
        res = await self._run(self.db.table("audit_log").insert(payload).execute)
        rows = res.data or []
        return rows[0] if rows else {}