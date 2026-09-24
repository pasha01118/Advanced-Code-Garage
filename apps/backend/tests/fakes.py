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


class FakeAIKeysRepository:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict] = {}

    async def upsert(self, owner_id, provider, *, key_ciphertext=None, ollama_base_url=None, status="untested", message=""):
        payload = {
            "owner_id": owner_id,
            "provider": provider,
            "status": status,
            "message": message,
            "model_count": 0,
            "last_validated_at": None,
        }
        if key_ciphertext:
            payload["key_ciphertext"] = key_ciphertext
        if ollama_base_url:
            payload["ollama_base_url"] = ollama_base_url
        self.rows[(owner_id, provider)] = payload
        return dict(payload)

    async def get(self, owner_id, provider):
        return self.rows.get((owner_id, provider))

    async def list_by_owner(self, owner_id):
        return [dict(row) for (oid, _p), row in self.rows.items() if oid == owner_id]

    async def update_status(self, owner_id, provider, *, status, message="", model_count=0):
        row = self.rows.get((owner_id, provider))
        if row is None:
            return None
        row["status"] = status
        row["message"] = message
        row["model_count"] = model_count
        row["last_validated_at"] = datetime.now(timezone.utc).isoformat()
        return dict(row)

    async def delete(self, owner_id, provider):
        return self.rows.pop((owner_id, provider), None) is not None