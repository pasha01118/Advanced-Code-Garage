import asyncio
from datetime import datetime, timezone

from app.core.event_bus import bus
from app.repositories.agent_logs import AgentLogsRepository
from app.repositories.projects import ProjectsRepository
from app.services.audit import AuditService
from app.services.model_router import ModelRouter

STAGES = [
    (0, 10, "Mr. Ravish Kumar", "Market Mapping & Requirements Analysis", "INFO", "Ravish is analyzing requirements..."),
    (10, 35, "Mr. Ravish Kumar", "Market Mapping & Requirements Analysis", "INFO", "Market viability scan complete."),
    (35, 55, "Ms. Sumati Madam", "Roadmap Synthesis", "DEBUG", "Phased roadmap generated."),
    (55, 75, "Mr. Arman Ali Khan", "Code Synthesis", "DEBUG", "Boilerplate and component logic being synthesized."),
    (75, 90, "Mr. Sadath Ali Khan", "Security Audit", "WARN", "Zero-tolerance scan in progress."),
    (90, 100, "Git-Sir", "Delivery", "OK", "Security gate passed. Project delivered."),
]

STAGE_DELAY_SECONDS = 0.8

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
    ) -> None:
        self.projects = projects or ProjectsRepository()
        self.logs = logs or AgentLogsRepository()
        self.audit = audit or AuditService()
        self.router = router or ModelRouter()

    async def create(
        self,
        name: str,
        description: str | None = None,
        repo_url: str | None = None,
        owner_id: str | None = None,
    ) -> dict:
        project = await self.projects.create(name, description, repo_url, owner_id)
        if not project or not project.get("id"):
            raise RuntimeError("Project insert did not return a row")
        project_id = str(project["id"])
        await self.audit.record(
            actor=owner_id or "anonymous",
            action="project.create",
            target=project_id,
            detail={"name": name},
        )
        await self.projects.update(project_id, status="analyzing", progress=10)
        task = asyncio.create_task(self._run_pipeline(project_id, owner_id))
        _pipeline_tasks.add(task)
        task.add_done_callback(_pipeline_tasks.discard)
        return await self.projects.get(project_id)

    async def get(self, project_id: str, owner_id: str | None = None) -> dict | None:
        return await self.projects.get(project_id, owner_id)

    async def list_recent(self, owner_id: str | None = None, limit: int = 50) -> list[dict]:
        return await self.projects.list_recent(owner_id, limit)

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
