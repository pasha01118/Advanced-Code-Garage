from datetime import datetime, timezone
from typing import List

from app.repositories.base import SupabaseRepository

SECRETS = "repository_secrets"
VERSIONS = "secret_versions"
AUDIT = "secret_access_audit"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class VaultRepository(SupabaseRepository):
    """Encrypted secret metadata, versions and access audit (no plaintext)."""

    async def find_active(
        self,
        owner_id: str,
        name: str,
        scope: str,
        repository_id: str | None,
        environment: str | None,
    ) -> dict | None:
        query = (
            self.db.table(SECRETS)
            .select("id,version")
            .eq("owner_id", owner_id)
            .eq("name", name)
            .eq("scope", scope)
            .is_("revoked_at", "null")
        )
        query = (
            query.is_("repository_id", "null")
            if repository_id is None
            else query.eq("repository_id", repository_id)
        )
        query = (
            query.is_("environment", "null")
            if environment is None
            else query.eq("environment", environment)
        )
        res = await self._run(query.limit(1).execute)
        return self._row(res)

    async def upsert(self, payload: dict, existing_id: str | None) -> dict:
        if existing_id:
            res = await self._run(
                self.db.table(SECRETS)
                .update(payload)
                .eq("id", existing_id)
                .execute
            )
        else:
            res = await self._run(self.db.table(SECRETS).insert(payload).execute)
        return self._row(res) or payload

    async def get(self, secret_id: str, owner_id: str | None = None) -> dict | None:
        query = self.db.table(SECRETS).select("*").eq("id", secret_id)
        if owner_id:
            query = query.eq("owner_id", owner_id)
        res = await self._run(query.limit(1).execute)
        return self._row(res)

    async def list(self, owner_id: str, repository_id: str | None = None) -> list[dict]:
        columns = (
            "id,name,scope,repository_id,environment,description,fingerprint,"
            "version,created_by,created_at,updated_at,revoked_at"
        )
        query = self.db.table(SECRETS).select(columns).eq("owner_id", owner_id)
        if repository_id:
            query = query.eq("repository_id", repository_id)
        res = await self._run(query.order("name").execute)
        return res.data or []

    async def revoke(self, secret_id: str, owner_id: str | None = None) -> bool:
        query = (
            self.db.table(SECRETS)
            .update({"revoked_at": _now(), "updated_at": _now()})
            .eq("id", secret_id)
            .is_("revoked_at", "null")
        )
        if owner_id:
            query = query.eq("owner_id", owner_id)
        res = await self._run(query.execute)
        return bool(res.data)

    async def add_version(
        self,
        secret_id: str,
        version: int,
        ciphertext: str,
        fingerprint: str,
        created_by: str,
    ) -> dict:
        row = {
            "secret_id": secret_id,
            "version": version,
            "ciphertext": ciphertext,
            "fingerprint": fingerprint,
            "created_by": created_by,
        }
        res = await self._run(self.db.table(VERSIONS).insert(row).execute)
        return self._row(res) or row

    async def get_version(self, secret_id: str, version: int) -> dict | None:
        res = await self._run(
            self.db.table(VERSIONS)
            .select("*")
            .eq("secret_id", secret_id)
            .eq("version", version)
            .limit(1)
            .execute
        )
        return self._row(res)

    async def add_access(
        self,
        secret_id: str,
        actor: str,
        action: str,
        purpose: str = "",
        request_id: str = "",
    ) -> dict:
        row = {
            "secret_id": secret_id,
            "actor": actor,
            "action": action,
            "purpose": purpose,
            "request_id": request_id,
        }
        res = await self._run(self.db.table(AUDIT).insert(row).execute)
        return self._row(res) or row

    async def list_access(self, secret_id: str, limit: int = 100) -> List[dict]:
        res = await self._run(
            self.db.table(AUDIT)
            .select("*")
            .eq("secret_id", secret_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute
        )
        return res.data or []
