from app.repositories.base import SupabaseRepository

TABLENAME = "project_templates"


class TemplatesRepository(SupabaseRepository):
    async def list(self) -> list[dict]:
        res = await self._run(
            self.db.table(TABLENAME)
            .select("*")
            .order("sort_order")
            .execute
        )
        return res.data or []

    async def get(self, template_id: str) -> dict | None:
        res = await self._run(
            self.db.table(TABLENAME).select("*").eq("id", template_id).limit(1).execute
        )
        return self._row(res)
