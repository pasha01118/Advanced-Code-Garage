from fastapi import APIRouter, Depends, Header

from app.core.auth import _is_admin, require_authenticated
from app.schemas.secrets import (
    SecretAuditListOut,
    SecretCreateRequest,
    SecretListOut,
    SecretOut,
    SecretRevokeOut,
)
from app.services.vault import VaultService, get_vault_service

router = APIRouter()


@router.get("/", response_model=SecretListOut)
async def list_secrets(
    repository_id: str | None = None,
    user: dict = Depends(require_authenticated),
    service: VaultService = Depends(get_vault_service),
) -> SecretListOut:
    return await service.list(user["sub"], repository_id)


@router.post("/", response_model=SecretOut)
async def save_secret(
    payload: SecretCreateRequest,
    user: dict = Depends(require_authenticated),
    x_request_id: str = Header(default="", alias="X-Request-ID"),
    service: VaultService = Depends(get_vault_service),
) -> SecretOut:
    return await service.save(
        user["sub"], user["sub"], payload, request_id=x_request_id
    )


@router.get("/{secret_id}/audit", response_model=SecretAuditListOut)
async def secret_audit(
    secret_id: str,
    user: dict = Depends(require_authenticated),
    service: VaultService = Depends(get_vault_service),
) -> SecretAuditListOut:
    return await service.audit(secret_id, None if _is_admin(user) else user["sub"])


@router.delete("/{secret_id}", response_model=SecretRevokeOut)
async def revoke_secret(
    secret_id: str,
    user: dict = Depends(require_authenticated),
    x_request_id: str = Header(default="", alias="X-Request-ID"),
    service: VaultService = Depends(get_vault_service),
) -> SecretRevokeOut:
    return await service.revoke(
        secret_id,
        None if _is_admin(user) else user["sub"],
        user["sub"],
        request_id=x_request_id,
    )
