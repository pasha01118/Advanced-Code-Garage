import uuid
from datetime import datetime, timezone
from typing import Optional


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

    async def aggregate_providers(self) -> list[dict]:
        """Aggregate key statuses across all owners per provider."""
        from collections import defaultdict
        agg: dict[str, dict] = defaultdict(
            lambda: {"configured": 0, "active": 0, "error": 0, "quota": 0, "models": 0, "messages": []}
        )
        for row in self.rows.values():
            provider = row["provider"]
            agg[provider]["configured"] += 1
            status = row.get("status", "untested")
            if status == "active":
                agg[provider]["active"] += 1
            elif status == "error":
                agg[provider]["error"] += 1
            elif status == "quota":
                agg[provider]["quota"] += 1
            agg[provider]["models"] += row.get("model_count", 0) or 0
            if row.get("message"):
                agg[provider]["messages"].append(row["message"])
        return [
            {"provider": p, **v} for p, v in agg.items()
        ]


class FakeAgentLogsRepository:
    def __init__(self) -> None:
        self.entries: list[dict] = []

    async def add(self, level: str, agent: str, message: str, project_id: Optional[str] = None):
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


class FakeAdminRepository:
    def __init__(self) -> None:
        self.state = {
            "status": "running",
            "message": "",
            "toggles": {
                "swarm": True,
                "git_ops": True,
                "deployments": True,
                "ai_routing": True,
                "sentinel": True,
                "signups": True,
                "telemetry": True,
            },
        }
        self.provider_metrics: dict[str, dict] = {}
        self.events: list[dict] = []
        self.discussion: list[dict] = []
        self._event_id = 0
        self._discussion_id = 0

    async def get_state(self) -> dict:
        return dict(self.state)

    async def set_state(self, *, status: Optional[str] = None, message: Optional[str] = None, toggles: Optional[dict] = None) -> dict:
        if status is not None:
            self.state["status"] = status
        if message is not None:
            self.state["message"] = message
        if toggles is not None:
            self.state["toggles"] = {**self.state["toggles"], **toggles}
        return dict(self.state)

    async def set_toggle(self, name: str, enabled: bool) -> dict:
        self.state["toggles"][name] = enabled
        return dict(self.state)

    async def upsert_provider_metrics(self, *, provider: str, status: str, message: str, model_count: int, tokens_used: int, balance_available: Optional[float], checked_at: Optional[str] = None) -> dict:
        self.provider_metrics[provider] = {
            "provider": provider,
            "status": status,
            "message": message,
            "model_count": model_count,
            "tokens_used": tokens_used,
            "balance_available": balance_available,
            "checked_at": checked_at,
        }
        return dict(self.provider_metrics[provider])

    async def list_provider_metrics(self) -> list[dict]:
        return list(self.provider_metrics.values())

    async def insert_event(self, event: dict) -> dict:
        self._event_id += 1
        now = datetime.now(timezone.utc).isoformat()
        row = {
            "id": str(self._event_id),
            "created_at": now,
            "updated_at": now,
            **event,
        }
        self.events.append(row)
        return row

    async def mark_event(self, event_id: str, *, status: str, report: str) -> dict:
        for event in self.events:
            if event["id"] == event_id:
                event["status"] = status
                event["auto_fix_report"] = report
                event["updated_at"] = datetime.now(timezone.utc).isoformat()
                return dict(event)
        raise ValueError("event not found")

    async def list_events(self, limit: int = 100) -> list[dict]:
        return self.events[-limit:]

    async def append_discussion(self, *, agent: str, message: str) -> dict:
        self._discussion_id += 1
        now = datetime.now(timezone.utc).isoformat()
        row = {"id": self._discussion_id, "created_at": now, "agent": agent, "message": message}
        self.discussion.append(row)
        return row

    async def list_discussion(self, limit: int = 100) -> list[dict]:
        return self.discussion[-limit:]