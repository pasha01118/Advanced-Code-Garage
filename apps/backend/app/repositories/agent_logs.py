from datetime import datetime, timezone

from app.repositories.base import SupabaseRepository


class AgentLogsRepository(SupabaseRepository):
    async def add(self, level: str, agent: str, message: str, project_id: str | None = None) -> dict:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "agent": agent,
            "message": message,
        }
        if project_id:
            payload["project_id"] = project_id
        res = await self._run(self.db.table("agent_logs").insert(payload).execute)
        rows = res.data or []
        return rows[0] if rows else {}

    async def recent(self, limit: int = 50) -> list[dict]:
        res = await self._run(
            self.db.table("agent_logs")
            .select("*")
            .order("timestamp", desc=True)
            .limit(limit)
            .execute
        )
        return res.data or []

    async def for_projects(
        self,
        project_ids: list[str],
        *,
        limit: int = 100,
        level: str | None = None,
        search: str | None = None,
    ) -> list[dict]:
        """Owner-scoped history: callers pass only project IDs they own."""
        if not project_ids:
            return []
        query = self.db.table("agent_logs").select("*").in_("project_id", project_ids)
        if level:
            query = query.eq("level", level)
        if search:
            query = query.ilike("message", f"%{search}%")
        res = await self._run(
            query.order("timestamp", desc=True).limit(limit).execute
        )
        return res.data or []