from app.repositories.agent_logs import AgentLogsRepository
from app.repositories.projects import ProjectsRepository
from app.repositories.terminal import SnippetsRepository, TerminalHistoryRepository
from app.services.audit import AuditService


class TerminalService:
    def __init__(
        self,
        snippets: SnippetsRepository | None = None,
        history: TerminalHistoryRepository | None = None,
        projects: ProjectsRepository | None = None,
        logs: AgentLogsRepository | None = None,
        audit: AuditService | None = None,
    ) -> None:
        self.snippets = snippets or SnippetsRepository()
        self.history = history or TerminalHistoryRepository()
        self.projects = projects or ProjectsRepository()
        self.logs = logs or AgentLogsRepository()
        self.audit = audit or AuditService()

    # -- snippets -------------------------------------------------------------

    async def list_snippets(self, owner_id: str) -> list[dict]:
        return await self.snippets.list(owner_id)

    async def create_snippet(
        self, owner_id: str, name: str, command: str, description: str = ""
    ) -> dict:
        row = await self.snippets.create(owner_id, name, command, description)
        await self.audit.record(
            owner_id, "snippet.create", row.get("id"), {"name": name}, owner_id
        )
        return row

    async def update_snippet(self, owner_id: str, snippet_id: str, fields: dict) -> dict | None:
        clean = {key: value for key, value in fields.items() if value is not None}
        row = await self.snippets.update(owner_id, snippet_id, clean)
        if row:
            await self.audit.record(
                owner_id, "snippet.update", snippet_id, {"fields": list(clean)}, owner_id
            )
        return row

    async def delete_snippet(self, owner_id: str, snippet_id: str) -> bool:
        deleted = await self.snippets.delete(owner_id, snippet_id)
        if deleted:
            await self.audit.record(owner_id, "snippet.delete", snippet_id, owner_id=owner_id)
        return deleted

    # -- command history ------------------------------------------------------

    async def add_history(self, owner_id: str, command: str) -> dict:
        row = await self.history.add(owner_id, command)
        await self.history.prune(owner_id)
        return row

    async def list_history(self, owner_id: str, limit: int = 100) -> list[dict]:
        rows = await self.history.list(owner_id, limit)
        return [
            {**row, "id": str(row["id"])} if row.get("id") is not None else row
            for row in rows
        ]

    async def clear_history(self, owner_id: str) -> int:
        return await self.history.clear(owner_id)

    # -- persisted agent-log tail --------------------------------------------

    async def log_history(
        self,
        owner_id: str,
        *,
        limit: int = 100,
        level: str | None = None,
        search: str | None = None,
    ) -> list[dict]:
        projects = await self.projects.list_recent(owner_id, limit=500)
        project_ids = [str(project["id"]) for project in projects if project.get("id")]
        entries = await self.logs.for_projects(
            project_ids, limit=limit, level=level, search=search
        )
        return list(reversed(entries))
