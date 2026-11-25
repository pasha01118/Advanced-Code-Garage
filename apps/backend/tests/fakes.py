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

    async def create(
        self,
        name,
        description=None,
        repo_url=None,
        owner_id=None,
        *,
        tags=None,
        template_id=None,
    ):
        now = datetime.now(timezone.utc).isoformat()
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
            "created_at": now,
            "updated_at": now,
            "tags": list(tags or []),
            "template_id": template_id,
            "pinned": False,
        }
        self.rows[row["id"]] = row
        return row

    async def get(self, project_id: str, owner_id=None):
        row = self.rows.get(project_id)
        if row is None or (owner_id is not None and row.get("owner_id") != owner_id):
            return None
        return row

    async def update(self, project_id: str, **fields):
        row = self.rows.get(project_id)
        if row is None:
            return None
        row.update(fields)
        return row

    async def list_recent(self, owner_id=None, limit: int = 50):
        items = [dict(r) for r in self.rows.values() if owner_id is None or r.get("owner_id") == owner_id]
        items.sort(key=lambda r: r["created_at"], reverse=True)
        return items[:limit]

    async def list_filtered(
        self, owner_id, *, status=None, tag=None, search=None, limit: int = 100
    ):
        items = [
            dict(r)
            for r in self.rows.values()
            if r.get("owner_id") == owner_id
            and (not status or r.get("status") == status)
            and (not tag or tag in (r.get("tags") or []))
            and (not search or search.lower() in str(r.get("name") or "").lower())
        ]
        items.sort(key=lambda r: (not bool(r.get("pinned")), r["created_at"]), reverse=True)
        return items[:limit]

    async def update_for_owner(self, owner_id, project_id, fields):
        row = self.rows.get(project_id)
        if row is None or row.get("owner_id") != owner_id:
            return None
        row.update(fields)
        return dict(row)

    async def bulk_update(self, owner_id, project_ids, fields):
        affected = 0
        for project_id in project_ids:
            row = self.rows.get(project_id)
            if row and row.get("owner_id") == owner_id:
                row.update(fields)
                affected += 1
        return affected

    async def bulk_delete(self, owner_id, project_ids):
        affected = 0
        for project_id in project_ids:
            row = self.rows.get(project_id)
            if row and row.get("owner_id") == owner_id:
                self.rows.pop(project_id, None)
                affected += 1
        return affected


class FakeAuditRepository:
    def __init__(self) -> None:
        self.entries: list[dict] = []

    async def add(self, actor, action, target=None, detail=None, owner_id=None):
        entry = {
            "id": str(len(self.entries) + 1),
            "actor": actor,
            "action": action,
            "target": target,
            "detail": detail,
            "owner_id": owner_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.entries.append(entry)
        return entry

    async def list(self, owner_id=None, *, limit=100, action=None, since=None):
        entries = [
            dict(entry)
            for entry in reversed(self.entries)
            if (owner_id is None or entry.get("owner_id") == owner_id)
            and (not action or entry.get("action") == action)
        ]
        return entries[:limit]


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

    async def for_projects(self, project_ids, *, limit=100, level=None, search=None):
        entries = [
            dict(entry)
            for entry in reversed(self.entries)
            if entry.get("project_id") in project_ids
            and (not level or str(entry.get("level") or "").upper() == level.upper())
            and (not search or search.lower() in str(entry.get("message") or "").lower())
        ]
        return entries[:limit]


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

    async def list_failing(self) -> list[dict]:
        return [
            dict(row) for row in self.rows.values() if row.get("status") in ("error", "quota")
        ]

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


class FakePreferencesRepository:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    async def get(self, owner_id):
        return dict(self.rows.get(owner_id) or {})

    async def upsert(self, owner_id, changes):
        row = {**self.rows.get(owner_id, {}), **changes}
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.rows[owner_id] = row
        return dict(row)


class FakeSnippetsRepository:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self._id = 0

    async def list(self, owner_id, limit: int = 100):
        return [dict(r) for r in self.rows.values() if r["owner_id"] == owner_id][:limit]

    async def create(self, owner_id, name, command, description=""):
        self._id += 1
        now = datetime.now(timezone.utc).isoformat()
        row = {
            "id": str(self._id),
            "owner_id": owner_id,
            "name": name,
            "command": command,
            "description": description,
            "created_at": now,
            "updated_at": now,
        }
        self.rows[row["id"]] = row
        return dict(row)

    async def update(self, owner_id, snippet_id, fields):
        row = self.rows.get(snippet_id)
        if row is None or row["owner_id"] != owner_id:
            return None
        row.update(fields)
        return dict(row)

    async def delete(self, owner_id, snippet_id):
        row = self.rows.get(snippet_id)
        if row is None or row["owner_id"] != owner_id:
            return False
        self.rows.pop(snippet_id)
        return True


class FakeHistoryRepository:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self._id = 0

    async def list(self, owner_id, limit=100):
        return [
            dict(row) for row in reversed(self.rows) if row["owner_id"] == owner_id
        ][:limit]

    async def add(self, owner_id, command):
        self._id += 1
        row = {
            "id": str(self._id),
            "owner_id": owner_id,
            "command": command,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.rows.append(row)
        return dict(row)

    async def clear(self, owner_id):
        before = len(self.rows)
        self.rows = [row for row in self.rows if row["owner_id"] != owner_id]
        return before - len(self.rows)

    async def prune(self, owner_id, keep: int = 200):
        pass


class FakeNotificationsRepository:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self._id = 0

    async def list(self, owner_id, limit=100, unread_only=False):
        return [
            dict(row)
            for row in reversed(self.rows)
            if row["owner_id"] == owner_id
            and (not unread_only or not row.get("read_at"))
        ][:limit]

    async def find_source(self, owner_id, source, source_id):
        for row in self.rows:
            if (
                row["owner_id"] == owner_id
                and row.get("source") == source
                and row.get("source_id") == source_id
            ):
                return dict(row)
        return None

    async def create(
        self,
        owner_id,
        *,
        title,
        body="",
        type="info",
        source="system",
        source_id=None,
        metadata=None,
    ):
        self._id += 1
        row = {
            "id": str(self._id),
            "owner_id": owner_id,
            "type": type,
            "title": title,
            "body": body,
            "source": source,
            "source_id": source_id,
            "read_at": None,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.rows.append(row)
        return dict(row)

    async def mark_read(self, owner_id, notification_id):
        for row in self.rows:
            if row["owner_id"] == owner_id and row["id"] == notification_id:
                row["read_at"] = datetime.now(timezone.utc).isoformat()
                return dict(row)
        return None

    async def mark_all_read(self, owner_id):
        count = 0
        for row in self.rows:
            if row["owner_id"] == owner_id and not row.get("read_at"):
                row["read_at"] = datetime.now(timezone.utc).isoformat()
                count += 1
        return count

    async def delete(self, owner_id, notification_id):
        for row in self.rows:
            if row["owner_id"] == owner_id and row["id"] == notification_id:
                self.rows.remove(row)
                return True
        return False

    async def clear(self, owner_id):
        before = len(self.rows)
        self.rows = [row for row in self.rows if row["owner_id"] != owner_id]
        return before - len(self.rows)


class FakeTemplatesRepository:
    def __init__(self) -> None:
        self.rows = [
            {
                "id": "blank",
                "name": "Blank project",
                "description": "Start from an empty workspace.",
                "default_description": "",
                "default_status": "queued",
                "tags": [],
                "sort_order": 0,
            }
        ]

    async def list(self):
        return list(self.rows)

    async def get(self, template_id):
        return next((dict(row) for row in self.rows if row["id"] == template_id), None)