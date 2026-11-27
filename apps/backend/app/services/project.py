import asyncio
import logging
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.config import get_settings
from app.core.event_bus import bus
from app.repositories.agent_logs import AgentLogsRepository
from app.repositories.projects import ProjectsRepository
from app.repositories.workspace import TemplatesRepository
from app.services.audit import AuditService
from app.services.model_router import ModelRouter
from app.services.notifications import NotificationService

STAGES = [
    (0, 10, "Mr. Ravish Kumar", "Market Mapping & Requirements Analysis", "INFO", "Ravish is analyzing requirements..."),
    (10, 35, "Mr. Ravish Kumar", "Market Mapping & Requirements Analysis", "INFO", "Market viability scan complete."),
    (35, 55, "Ms. Sumati Madam", "Roadmap Synthesis", "DEBUG", "Phased roadmap generated."),
    (55, 75, "Mr. Arman Ali Khan", "Code Synthesis", "DEBUG", "Boilerplate and component logic being synthesized."),
    (75, 90, "Mr. Sadath Ali Khan", "Security Audit", "WARN", "Zero-tolerance scan in progress."),
    (90, 100, "Git-Sir", "Delivery", "OK", "Security gate passed. Project delivered."),
]

logger = logging.getLogger(__name__)

STAGE_DELAY_SECONDS = 0.8
PROJECT_STATUSES = {"queued", "analyzing", "delivered", "failed"}

# Strong references to background pipelines: a bare create_task() can be
# garbage-collected mid-flight, and shutdown must be able to cancel them.
_pipeline_tasks: set[asyncio.Task] = set()


def cancel_pipeline_tasks() -> None:
    """Cancel all in-flight project pipelines (called during app shutdown)."""
    for task in tuple(_pipeline_tasks):
        task.cancel()


class ProjectService:
    def __init__(
        self,
        projects: ProjectsRepository | None = None,
        logs: AgentLogsRepository | None = None,
        audit: AuditService | None = None,
        router: ModelRouter | None = None,
        templates: TemplatesRepository | None = None,
        notifications: NotificationService | None = None,
    ) -> None:
        self.projects = projects or ProjectsRepository()
        self.logs = logs or AgentLogsRepository()
        self.audit = audit or AuditService()
        self.router = router or ModelRouter()
        self.templates = templates or TemplatesRepository()
        self.notifications = notifications

    async def create(
        self,
        name: str,
        description: str | None = None,
        repo_url: str | None = None,
        owner_id: str | None = None,
        *,
        tags: list[str] | None = None,
        template_id: str | None = None,
    ) -> dict:
        template: dict | None = None
        if template_id:
            template = await self.templates.get(template_id)
            if template is None:
                raise HTTPException(status_code=400, detail=f"Unknown template '{template_id}'.")
        final_description = description
        if final_description is None and template:
            final_description = template.get("default_description") or None
        final_tags = list(tags or [])
        if template and not final_tags:
            final_tags = list(template.get("tags") or [])
        project = await self.projects.create(
            name,
            final_description,
            repo_url,
            owner_id,
            tags=final_tags,
            template_id=template_id,
        )
        if not project or not project.get("id"):
            raise RuntimeError("Project insert did not return a row")
        project_id = str(project["id"])
        await self.audit.record(
            actor=owner_id or "anonymous",
            action="project.create",
            target=project_id,
            detail={"name": name, "template_id": template_id},
            owner_id=owner_id,
        )
        await self.projects.update(project_id, status="analyzing", progress=10)
        if get_settings().is_serverless:
            # A detached task can be frozen when a serverless invocation returns.
            # Finish the pipeline before responding so the project is durable.
            await self._run_pipeline(project_id, owner_id)
        else:
            task = asyncio.create_task(self._run_pipeline(project_id, owner_id))
            _pipeline_tasks.add(task)
            task.add_done_callback(_pipeline_tasks.discard)
        return await self.projects.get(project_id)

    async def get(self, project_id: str, owner_id: str | None = None) -> dict | None:
        return await self.projects.get(project_id, owner_id)

    async def list_recent(self, owner_id: str | None = None, limit: int = 50) -> list[dict]:
        return await self.projects.list_recent(owner_id, limit)

    async def list_filtered(
        self,
        owner_id: str,
        *,
        status: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        return await self.projects.list_filtered(
            owner_id, status=status, tag=tag, search=search, limit=limit
        )

    async def list_templates(self) -> list[dict]:
        return await self.templates.list()

    async def update_meta(
        self, owner_id: str, project_id: str, fields: dict
    ) -> dict:
        current = await self.projects.get(project_id, owner_id)
        if current is None:
            raise HTTPException(status_code=404, detail="Project not found")
        clean = {key: value for key, value in fields.items() if value is not None}
        if "template_id" in clean and clean["template_id"]:
            if await self.templates.get(clean["template_id"]) is None:
                raise HTTPException(status_code=400, detail="Unknown template.")
        row = await self.projects.update_for_owner(owner_id, project_id, clean) or current
        await self.audit.record(
            actor=owner_id,
            action="project.update",
            target=project_id,
            detail={"fields": sorted(clean)},
            owner_id=owner_id,
        )
        return row

    async def bulk_action(
        self, owner_id: str, ids: list[str], action: str, value: str | None = None
    ) -> int:
        if action == "status" and value not in PROJECT_STATUSES:
            raise HTTPException(status_code=400, detail="Unsupported project status.")
        if action in {"tag", "untag"} and not value:
            raise HTTPException(status_code=400, detail="A tag value is required.")
        affected = 0
        if action in {"pin", "unpin", "status"}:
            field = {
                "pin": "pinned",
                "unpin": "pinned",
                "status": "status",
            }[action]
            payload = {field: action == "pin" if action in {"pin", "unpin"} else value}
            affected = await self.projects.bulk_update(owner_id, ids, payload)
        elif action == "delete":
            affected = await self.projects.bulk_delete(owner_id, ids)
        else:
            for project_id in ids:
                project = await self.projects.get(project_id, owner_id)
                if project is None:
                    continue
                tags = list(project.get("tags") or [])
                if action == "tag" and value not in tags:
                    tags.append(value)
                elif action == "untag":
                    tags = [tag for tag in tags if tag != value]
                else:
                    continue
                if await self.projects.update_for_owner(owner_id, project_id, {"tags": tags}):
                    affected += 1
        await self.audit.record(
            actor=owner_id,
            action=f"project.bulk.{action}",
            target=", ".join(ids[:10]),
            detail={"count": affected, "value": value},
            owner_id=owner_id,
        )
        return affected

    def _build_prompt(self, stage, name: str, description: str | None) -> str:
        _, _, agent, task, _, fallback = stage
        brief = description or name
        return (
            f"You are {agent} running the '{task}' phase of the Advanced-Code-Garage "
            f"autonomous pipeline for the project:\n\n{brief}\n\n"
            f"Produce a concise {len(task)} note (60-120 words) describing what you analyzed "
            "and your concrete takeaway for this phase. Plain text only."
        )

    async def _run_pipeline(self, project_id: str, owner_id: str | None = None) -> None:
        project = await self.projects.get(project_id) or {}
        name = project.get("name") or "Untitled project"
        description = project.get("description")
        owner = project.get("owner_id") or owner_id
        try:
            for start, end, agent, task, level, fallback in STAGES:
                await asyncio.sleep(STAGE_DELAY_SECONDS)
                await self.projects.update(
                    project_id,
                    status="analyzing",
                    progress=end,
                    current_agent=agent,
                    current_task=task,
                )
                prompt = self._build_prompt((start, end, agent, task, level, fallback), name, description)
                text, _ = await self.router.complete(prompt)
                message = text.strip() or fallback
                event = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": level,
                    "agent": agent,
                    "message": message,
                    "project_id": project_id,
                    "owner_id": owner,
                }
                await self.logs.add(level, agent, message, project_id)
                await bus.publish(event)
            await self.projects.update(
                project_id,
                status="delivered",
                progress=100,
                current_agent=None,
                current_task=None,
            )
            if self.notifications:
                try:
                    await self.notifications.project_delivered(owner, project_id, name)
                except Exception as exc:
                    # Delivery already succeeded: a notification failure must not
                    # flip the project to `failed` or publish a pipeline error.
                    logger.warning(
                        "project %s delivered but notification failed: %s",
                        project_id,
                        type(exc).__name__,
                    )
        except asyncio.CancelledError:
            await self.projects.update(
                project_id,
                status="queued",
                current_agent=None,
                current_task=None,
            )
            raise
        except Exception as exc:
            message = f"Pipeline failed for project {project_id}: {type(exc).__name__}"
            await self.projects.update(
                project_id,
                status="failed",
                current_agent=None,
                current_task=None,
            )
            await self.logs.add("ERROR", "System", message, project_id)
            await bus.publish(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "ERROR",
                    "agent": "System",
                    "message": message,
                    "project_id": project_id,
                    "owner_id": owner,
                }
            )
            if self.notifications:
                await self.notifications.project_failed(owner, project_id, message)
