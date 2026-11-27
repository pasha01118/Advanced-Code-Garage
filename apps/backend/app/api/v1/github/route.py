import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.core.auth import require_admin
from app.schemas.repositories import InstallationListOut, SyncOut
from app.services.github_app import GitHubAppService, GitHubNotConfigured, get_github_app_service
from app.services.ops_state import require_service

router = APIRouter()

Admin = Depends(require_admin)
GitOps = Depends(require_service("git_ops"))


@router.post("/webhook", include_in_schema=False)
async def webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
    service: GitHubAppService = Depends(get_github_app_service),
):
    if not service.webhook_is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub App webhook is not configured",
        )
    body = await request.body()
    if not service.verify_webhook(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    try:
        payload = json.loads(body)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    await service.handle_webhook(
        payload, x_github_event or "ping", x_github_delivery or ""
    )
    return {"status": "ok"}


@router.get("/installations", response_model=InstallationListOut)
async def list_installations(
    user: dict = Admin,
    _enabled: bool = GitOps,
    service: GitHubAppService = Depends(get_github_app_service),
) -> InstallationListOut:
    rows = await service.repo.list_installations()
    return InstallationListOut(installations=rows)


@router.post("/installations/{installation_id}/sync", response_model=SyncOut)
async def sync_installation(
    installation_id: int,
    user: dict = Admin,
    _enabled: bool = GitOps,
    service: GitHubAppService = Depends(get_github_app_service),
) -> SyncOut:
    try:
        await service.repo.link_installation(installation_id, user["sub"])
        result = await service.sync_installation(installation_id)
    except GitHubNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return SyncOut(**result)
