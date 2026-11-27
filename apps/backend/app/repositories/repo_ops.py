from datetime import datetime, timezone

from app.repositories.base import SupabaseRepository

PERMISSIONS = "repo_permissions"
AUDIT = "repo_audit_events"
IDEMPOTENCY = "repo_idempotency"

ROLES = ("owner", "write", "read")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RepoOpsRepository(SupabaseRepository):
    """Repository permissions, operation audit and retry safety."""

    async def get_role(self, repository_id: str, user_id: str) -> str | None:
        res = await self._run(
            self.db.table(PERMISSIONS)
            .select("role")
            .eq("repository_id", repository_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute
        )
        rows = res.data or []
        return rows[0]["role"] if rows else None

    async def grant_permission(
        self, repository_id: str, user_id: str, role: str, granted_by: str
    ) -> dict:
        if role not in ROLES:
            raise ValueError("Invalid repository role")
        row = {
            "repository_id": repository_id,
            "user_id": user_id,
            "role": role,
            "granted_by": granted_by,
            "updated_at": _now(),
        }
        res = await self._run(
            self.db.table(PERMISSIONS)
            .upsert(row, on_conflict="repository_id,user_id")
            .execute
        )
        return self._row(res) or row

    async def revoke_permission(self, repository_id: str, user_id: str) -> bool:
        res = await self._run(
            self.db.table(PERMISSIONS)
            .delete()
            .eq("repository_id", repository_id)
            .eq("user_id", user_id)
            .execute
        )
        return bool(res.data)

    async def list_permissions(self, repository_id: str) -> list[dict]:
        res = await self._run(
            self.db.table(PERMISSIONS)
            .select("id,repository_id,user_id,role,granted_by,created_at,updated_at")
            .eq("repository_id", repository_id)
            .order("role")
            .execute
        )
        return res.data or []

    async def add_audit(
        self,
        repository_id: str,
        actor: str,
        action: str,
        *,
        target: str = "",
        detail: dict | None = None,
        request_id: str = "",
    ) -> dict:
        row = {
            "repository_id": repository_id,
            "actor": actor,
            "action": action,
            "target": target,
            "detail": detail or {},
            "request_id": request_id,
        }
        res = await self._run(self.db.table(AUDIT).insert(row).execute)
        return self._row(res) or row

    async def list_audit(self, repository_id: str, limit: int = 100) -> list[dict]:
        res = await self._run(
            self.db.table(AUDIT)
            .select("*")
            .eq("repository_id", repository_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute
        )
        return res.data or []

    async def get_idempotent(self, key: str) -> dict | None:
        res = await self._run(
            self.db.table(IDEMPOTENCY)
            .select("result")
            .eq("key", key)
            .limit(1)
            .execute
        )
        rows = res.data or []
        return rows[0] if rows else None

    async def record_idempotent(
        self, key: str, actor: str, repository_id: str, action: str, result: dict
    ) -> dict:
        row = {
            "key": key,
            "actor": actor,
            "repository_id": repository_id,
            "action": action,
            "result": result,
        }
        res = await self._run(self.db.table(IDEMPOTENCY).insert(row).execute)
        return self._row(res) or row
