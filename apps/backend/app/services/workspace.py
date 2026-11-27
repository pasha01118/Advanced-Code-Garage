from collections import Counter
from datetime import datetime, timedelta, timezone

from app.repositories.admin_repo import AdminRepository
from app.repositories.agent_logs import AgentLogsRepository
from app.repositories.ai_keys import AIKeysRepository
from app.repositories.projects import ProjectsRepository
from app.repositories.workspace import TemplatesRepository
from app.routers.agents import ROSTER
from app.services.ai_catalog import list_catalog
from app.services.mode import ModeService
from app.services.notifications import NotificationService
from app.services.ops_state import OpsStateService

NAVIGATION = [
    {"title": "Overview", "href": "/"},
    {"title": "Terminal", "href": "/terminal"},
    {"title": "Projects", "href": "/projects"},
    {"title": "AI Integration", "href": "/ai-integration"},
    {"title": "Metrics", "href": "/metrics"},
    {"title": "Notifications", "href": "/notifications"},
    {"title": "Preferences", "href": "/preferences"},
    {"title": "Audit log", "href": "/audit"},
    {"title": "Control Panel", "href": "/admin"},
]


class WorkspaceService:
    def __init__(
        self,
        projects: ProjectsRepository | None = None,
        templates: TemplatesRepository | None = None,
        logs: AgentLogsRepository | None = None,
        ai_keys: AIKeysRepository | None = None,
        notifications: NotificationService | None = None,
        ops: OpsStateService | None = None,
        admin: AdminRepository | None = None,
        modes: ModeService | None = None,
    ) -> None:
        self.projects = projects or ProjectsRepository()
        self.templates = templates or TemplatesRepository()
        self.logs = logs or AgentLogsRepository()
        self.ai_keys = ai_keys or AIKeysRepository()
        self.notifications = notifications or NotificationService()
        self.ops = ops or OpsStateService()
        self.admin = admin or AdminRepository()
        self.modes = modes or ModeService()

    async def list_templates(self) -> list[dict]:
        return await self.templates.list()

    async def search(self, owner_id: str, query: str) -> list[dict]:
        needle = query.strip().lower()
        results: list[dict] = []

        def add(result_type: str, item_id: str, title: str, subtitle: str, href: str) -> None:
            haystack = f"{title} {subtitle}".lower()
            if needle and needle not in haystack:
                return
            results.append(
                {
                    "type": result_type,
                    "id": item_id,
                    "title": title,
                    "subtitle": subtitle or None,
                    "href": href,
                }
            )

        for item in NAVIGATION:
            add("navigation", item["href"], item["title"], "Open page", item["href"])
        for project in await self.projects.list_recent(owner_id, limit=100):
            project_id = str(project.get("id") or "")
            add(
                "project",
                project_id,
                project.get("name") or "Untitled project",
                f"Project · {project.get('status') or 'queued'}",
                f"/projects?project={project_id}",
            )
        for template in await self.templates.list():
            add(
                "template",
                str(template.get("id") or ""),
                template.get("name") or "Template",
                "Create project from template",
                f"/projects?template={template.get('id') or ''}",
            )
        for entry in list_catalog():
            add(
                "provider",
                entry["id"],
                entry.get("name") or entry["id"],
                "AI provider integration",
                "/ai-integration",
            )
        if needle:
            results.sort(key=lambda item: (not item["title"].lower().startswith(needle), item["title"]))
        return results[:40]

    async def metrics(self, owner_id: str) -> dict:
        projects = await self.projects.list_recent(owner_id, limit=500)
        by_status = Counter(str(project.get("status") or "queued") for project in projects)
        for status in ("queued", "analyzing", "delivered", "failed"):
            by_status.setdefault(status, 0)

        today = datetime.now(timezone.utc).date()
        recent: list[dict] = []
        for days_ago in range(6, -1, -1):
            day = today - timedelta(days=days_ago)
            label = day.isoformat()
            count = 0
            for project in projects:
                created = str(project.get("created_at") or "")
                if created.startswith(label):
                    count += 1
            recent.append({"label": label, "value": count})

        keys = await self.ai_keys.list_by_owner(owner_id)
        project_ids = [str(project["id"]) for project in projects if project.get("id")]
        logs = await self.logs.for_projects(project_ids, limit=500)
        events = await self.admin.list_events(limit=500)
        event_count = sum(
            1
            for event in events
            if event.get("status") == "open"
            and event.get("owner_id") in (None, owner_id)
        )
        counts = await self.notifications.counts(owner_id)
        state = await self.ops.get_state()
        return {
            "projects_total": len(projects),
            "projects_by_status": dict(by_status),
            "projects_recent": recent,
            "active_agents": len(ROSTER),
            "system_mode": await self.modes.get(),
            "providers_active": sum(1 for key in keys if key.get("status") == "active"),
            "providers_configured": len(keys),
            "notifications_unread": counts["unread"],
            "logs_recent": len(logs),
            "sentinel_open": event_count,
            "app_status": str(state.get("status") or "running"),
        }
