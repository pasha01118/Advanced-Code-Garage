import uuid
from datetime import datetime, timezone


class FakeModesRepository:
    def __init__(self) -> None:
        self.value = "AI-Man"

    async def get(self) -> str:
        return self.value

    async def set(self, value: str) -> str:
        self.value = value
        return self.value


class FakeProjectsRepository:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    async def create(self, name, description=None, repo_url=None, owner_id=None):
        row = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "repo_url": repo_url,
            "owner_id": owner_id,
            "status": "queued",
            "progress": 0,
            "current_agent": None,
            "current_task": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.rows[row["id"]] = row
        return row

    async def get(self, project_id: str):
        return self.rows.get(project_id)

    async def update(self, project_id: str, **fields):
        row = self.rows.get(project_id)
        if row is None:
            return None
        row.update(fields)
        return row

    async def list_recent(self, limit: int = 50):
        items = [dict(r) for r in self.rows.values()]
        items.sort(key=lambda r: r["created_at"], reverse=True)
        return items[:limit]


class FakeAuditRepository:
    def __init__(self) -> None:
        self.entries: list[dict] = []

    async def add(self, actor, action, target=None, detail=None):
        entry = {"actor": actor, "action": action, "target": target, "detail": detail}
        self.entries.append(entry)
        return entry


class FakeLogsRepository:
    def __init__(self) -> None:
        self.entries: list[dict] = []

    async def add(self, level, agent, message, project_id=None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "agent": agent,
            "message": message,
            "project_id": project_id,
        }
        self.entries.append(entry)
        return entry

    async def recent(self, limit: int = 50):
        return list(reversed(self.entries[-limit:]))