from datetime import datetime, timezone

from app.repositories.base import SupabaseRepository

INSTALLATIONS = "github_installations"
REPOSITORIES = "github_repositories"
WEBHOOK_EVENTS = "github_webhook_events"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GitHubRepository(SupabaseRepository):
    """Store GitHub App installations, repositories and webhook deliveries."""

    async def upsert_installation(
        self,
        installation_id: int,
        account_login: str,
        *,
        account_type: str = "",
        suspended: bool = False,
        linked_by: str | None = None,
    ) -> dict:
        payload = {
            "installation_id": installation_id,
            "account_login": account_login,
            "account_type": account_type,
            "suspended": suspended,
            "updated_at": _now(),
        }
        if linked_by:
            payload["linked_by"] = linked_by
        res = await self._run(
            self.db.table(INSTALLATIONS)
            .upsert(payload, on_conflict="installation_id")
            .execute
        )
        return self._row(res) or payload

    async def link_installation(self, installation_id: int, actor: str) -> dict | None:
        res = await self._run(
            self.db.table(INSTALLATIONS)
            .update({"linked_by": actor, "updated_at": _now()})
            .eq("installation_id", installation_id)
            .execute
        )
        return self._row(res)

    async def list_installations(self, limit: int = 100) -> list[dict]:
        res = await self._run(
            self.db.table(INSTALLATIONS)
            .select("*")
            .order("updated_at", desc=True)
            .limit(limit)
            .execute
        )
        return res.data or []

    async def upsert_repository(self, installation_id: int, repo: dict) -> dict:
        owner = (repo.get("owner") or {}).get("login") or repo.get("full_name", "").split("/")[0]
        payload = {
            "installation_id": installation_id,
            "external_id": int(repo["id"]),
            "full_name": repo.get("full_name") or f"{owner}/{repo.get('name', '')}",
            "name": repo.get("name", ""),
            "owner_login": owner,
            "private": bool(repo.get("private", False)),
            "default_branch": repo.get("default_branch") or "main",
            "html_url": repo.get("html_url") or "",
            "archived": bool(repo.get("archived", False)),
            "disabled": bool(repo.get("disabled", False)),
            "updated_at": _now(),
        }
        res = await self._run(
            self.db.table(REPOSITORIES)
            .upsert(payload, on_conflict="installation_id,external_id")
            .execute
        )
        return self._row(res) or payload

    async def list_repositories(self, limit: int = 200) -> list[dict]:
        res = await self._run(
            self.db.table(REPOSITORIES)
            .select("*")
            .order("full_name")
            .limit(limit)
            .execute
        )
        return res.data or []

    async def get_repository(self, repository_id: str) -> dict | None:
        res = await self._run(
            self.db.table(REPOSITORIES)
            .select("*")
            .eq("id", repository_id)
            .limit(1)
            .execute
        )
        return self._row(res)

    async def get_repository_by_external_id(
        self, installation_id: int, external_id: int
    ) -> dict | None:
        res = await self._run(
            self.db.table(REPOSITORIES)
            .select("id")
            .eq("installation_id", installation_id)
            .eq("external_id", external_id)
            .limit(1)
            .execute
        )
        return self._row(res)

    async def has_delivery(self, delivery_id: str) -> bool:
        if not delivery_id:
            return False
        res = await self._run(
            self.db.table(WEBHOOK_EVENTS)
            .select("id")
            .eq("delivery_id", delivery_id)
            .limit(1)
            .execute
        )
        return bool(res.data)

    async def record_webhook(
        self,
        delivery_id: str,
        event: str,
        action: str,
        installation_id: int | None,
        repository_full_name: str,
        payload: dict,
    ) -> dict:
        row = {
            "delivery_id": delivery_id,
            "event": event,
            "action": action,
            "installation_id": installation_id,
            "repository_full_name": repository_full_name,
            "payload": payload,
        }
        res = await self._run(self.db.table(WEBHOOK_EVENTS).insert(row).execute)
        return self._row(res) or row
