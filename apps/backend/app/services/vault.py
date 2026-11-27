from fastapi import HTTPException, status

from app.core.vault import decrypt_value, encrypt_value, fingerprint
from app.repositories.secrets import VaultRepository
from app.schemas.secrets import (
    SecretAuditListOut,
    SecretAuditOut,
    SecretCreateRequest,
    SecretListOut,
    SecretOut,
    SecretRevokeOut,
)


class VaultService:
    """Server-side secret lifecycle. Plaintext is never returned to an API."""

    def __init__(self, repo: VaultRepository | None = None) -> None:
        self.repo = repo or VaultRepository()

    async def save(
        self,
        owner_id: str,
        actor: str,
        payload: SecretCreateRequest,
        *,
        request_id: str = "",
    ) -> SecretOut:
        if payload.scope != "user" and not payload.repository_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="repository_id is required for repository and environment secrets",
            )
        if payload.scope == "environment" and not payload.environment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="environment is required for environment secrets",
            )

        existing = await self.repo.find_active(
            owner_id,
            payload.name,
            payload.scope,
            payload.repository_id,
            payload.environment,
        )
        version = int(existing.get("version") or 0) + 1 if existing else 1
        ciphertext = encrypt_value(payload.value)
        digest = fingerprint(payload.value)
        row = {
            "owner_id": owner_id,
            "name": payload.name,
            "scope": payload.scope,
            "repository_id": payload.repository_id,
            "environment": payload.environment,
            "description": payload.description,
            "fingerprint": digest,
            "version": version,
            "created_by": actor,
        }
        secret = await self.repo.upsert(row, existing.get("id") if existing else None)
        secret_id = str(secret["id"])
        await self.repo.add_version(
            secret_id, version, ciphertext, digest, actor
        )
        await self.repo.add_access(
            secret_id,
            actor,
            "rotate" if existing else "create",
            "vault write",
            request_id,
        )
        return SecretOut(**secret)

    async def list(self, owner_id: str, repository_id: str | None = None) -> SecretListOut:
        rows = await self.repo.list(owner_id, repository_id)
        return SecretListOut(secrets=[SecretOut(**row) for row in rows])

    async def revoke(
        self,
        secret_id: str,
        owner_id: str | None,
        actor: str,
        *,
        request_id: str = "",
    ) -> SecretRevokeOut:
        secret = await self.repo.get(secret_id, owner_id)
        if not secret:
            raise HTTPException(status_code=404, detail="Secret not found")
        revoked = await self.repo.revoke(secret_id, owner_id)
        if revoked:
            await self.repo.add_access(
                secret_id, actor, "revoke", "vault write", request_id
            )
        return SecretRevokeOut(id=secret_id, revoked=revoked)

    async def audit(self, secret_id: str, owner_id: str | None) -> SecretAuditListOut:
        secret = await self.repo.get(secret_id, owner_id)
        if not secret:
            raise HTTPException(status_code=404, detail="Secret not found")
        rows = await self.repo.list_access(secret_id)
        return SecretAuditListOut(entries=[SecretAuditOut(**row) for row in rows])

    async def reveal(
        self,
        secret_id: str,
        actor: str,
        purpose: str,
        *,
        request_id: str = "",
    ) -> str:
        """Internal use only: no route exposes this method."""
        secret = await self.repo.get(secret_id)
        if not secret or secret.get("revoked_at"):
            raise HTTPException(status_code=404, detail="Secret not found")
        version = await self.repo.get_version(secret_id, int(secret["version"]))
        if not version:
            raise HTTPException(status_code=404, detail="Secret version not found")
        plaintext = decrypt_value(version["ciphertext"])
        await self.repo.add_access(
            secret_id, actor, "reveal", purpose, request_id
        )
        return plaintext


def get_vault_service() -> VaultService:
    return VaultService()
