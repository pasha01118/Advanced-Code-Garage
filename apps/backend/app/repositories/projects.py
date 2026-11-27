from app.repositories.base import SupabaseRepository

TABLENAME = "projects"


class ProjectsRepository(SupabaseRepository):
    async def create(
        self,
        name: str,
        description: str | None,
        repo_url: str | None,
        owner_id: str | None = None,
        *,
        tags: list[str] | None = None,
        template_id: str | None = None,
    ) -> dict:
        payload: dict = {"name": name}
        if description:
            payload["description"] = description
        if repo_url:
            payload["repo_url"] = repo_url
        if owner_id:
            payload["owner_id"] = owner_id
        if tags:
            payload["tags"] = tags
        if template_id:
            payload["template_id"] = template_id
        res = await self._run(self.db.table(TABLENAME).insert(payload).execute)
        rows = res.data or []
        return rows[0] if rows else {}

    async def get(self, project_id: str, owner_id: str | None = None) -> dict | None:
        query = self.db.table(TABLENAME).select("*").eq("id", project_id)
        if owner_id:
            query = query.eq("owner_id", owner_id)
        res = await self._run(query.limit(1).execute)
        return self._row(res)

    async def update(self, project_id: str, **fields) -> dict | None:
        res = await self._run(
            self.db.table(TABLENAME).update(fields).eq("id", project_id).execute
        )
        return self._row(res)

    async def list_recent(self, owner_id: str | None = None, limit: int = 50) -> list[dict]:
        query = self.db.table(TABLENAME).select("*")
        if owner_id:
            query = query.eq("owner_id", owner_id)
        res = await self._run(query.order("created_at", desc=True).limit(limit).execute)
        return res.data or []

    async def list_filtered(
        self,
        owner_id: str,
        *,
        status: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        query = self.db.table(TABLENAME).select("*").eq("owner_id", owner_id)
        if status:
            query = query.eq("status", status)
        if tag:
            query = query.contains("tags", [tag])
        if search:
            query = query.ilike("name", f"%{search}%")
        res = await self._run(
            query.order("pinned", desc=True).order("updated_at", desc=True).limit(limit).execute
        )
        return res.data or []

    async def update_for_owner(self, owner_id: str, project_id: str, fields: dict) -> dict | None:
        if not fields:
            return await self.get(project_id, owner_id)
        res = await self._run(
            self.db.table(TABLENAME)
            .update(fields)
            .eq("owner_id", owner_id)
            .eq("id", project_id)
            .execute
        )
        return self._row(res)

    async def bulk_update(
        self, owner_id: str, project_ids: list[str], fields: dict
    ) -> int:
        if not project_ids or not fields:
            return 0
        res = await self._run(
            self.db.table(TABLENAME)
            .update(fields)
            .eq("owner_id", owner_id)
            .in_("id", project_ids)
            .execute
        )
        return len(res.data or [])

    async def bulk_delete(self, owner_id: str, project_ids: list[str]) -> int:
        if not project_ids:
            return 0
        res = await self._run(
            self.db.table(TABLENAME)
            .delete()
            .eq("owner_id", owner_id)
            .in_("id", project_ids)
            .execute
        )
        return len(res.data or [])
