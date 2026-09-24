from app.repositories.base import SupabaseRepository


class ProjectsRepository(SupabaseRepository):
    async def create(self, name: str, description: str | None, repo_url: str | None, owner_id: str | None = None) -> dict:
        payload: dict = {"name": name}
        if description:
            payload["description"] = description
        if repo_url:
            payload["repo_url"] = repo_url
        if owner_id:
            payload["owner_id"] = owner_id
        res = await self._run(self.db.table("projects").insert(payload).execute)
        rows = res.data or []
        return rows[0] if rows else {}

    async def get(self, project_id: str) -> dict | None:
        res = await self._run(
            self.db.table("projects").select("*").eq("id", project_id).maybe_single().execute
        )
        return res.data

    async def update(self, project_id: str, **fields) -> dict | None:
        res = await self._run(
            self.db.table("projects").update(fields).eq("id", project_id).maybe_single().execute
        )
        return res.data

    async def list_recent(self, limit: int = 50) -> list[dict]:
        res = await self._run(
            self.db.table("projects")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute
        )
        return res.data or []