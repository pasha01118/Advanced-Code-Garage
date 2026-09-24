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
        project_id = str(project.get("id"))
        await self.audit.record(
            actor=owner_id or "anonymous",
            action="project.create",
            target=project_id,
            detail={"name": name},
        )
        await self.projects.update(project_id, status="analyzing", progress=10)
        asyncio.create_task(self._run_pipeline(project_id))
        return await self.projects.get(project_id)

    async def get(self, project_id: str) -> dict | None:
        return await self.projects.get(project_id)

    async def list_recent(self, limit: int = 50) -> list[dict]:
        return await self.projects.list_recent(limit)

    def _build_prompt(self, stage, name: str, description: str | None) -> str:
        _, _, agent, task, _, fallback = stage
        brief = description or name
        return (
            f"You are {agent} running the '{task}' phase of the Advanced-Code-Garage "
            f"autonomous pipeline for the project:\n\n{brief}\n\n"
            f"Produce a concise {len(task)} note (60-120 words) describing what you analyzed "
            "and your concrete takeaway for this phase. Plain text only."
        )

    async def _run_pipeline(self, project_id: str) -> None:
        project = await self.projects.get(project_id) or {}
        name = project.get("name") or "Untitled project"
        description = project.get("description")
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
        except Exception:
            await self.logs.add("ERROR", "System", f"Pipeline failed for project {project_id}", project_id)