import time
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import _is_admin, require_admin, require_authenticated, require_user
from app.core.config import get_settings
from app.repositories.admin_repo import AdminRepository
from app.schemas.admin import (
    AppStateOut,
    ProviderUsageListOut,
    ProviderUsageOut,
    RunSentinelOut,
    SentinelDiscussionEntryOut,
    SentinelEventOut,
    SentinelSnapshotOut,
    SetAppStateRequest,
    SetToggleRequest,
    SuspendUserRequest,
    UpdateAccountOut,
    UpdateAccountRequest,
    UserListOut,
    UserRowOut,
)
from app.services.admin_users import AdminUsersService
from app.services.ai_catalog import list_catalog
from app.services.ops_state import OpsStateService, require_service
from app.services.sentinel import PROVIDER_SUGGESTIONS, SentinelService
from app.services.sentinel_runtime import get_sentinel_service as shared_sentinel_service

router = APIRouter()

AdminUser = Annotated[dict, Depends(require_admin)]


def get_ops_service() -> OpsStateService:
    return OpsStateService()


def get_sentinel_service() -> SentinelService:
    # One instance is shared with the background loop so snapshots and manual
    # runs observe (and guard against) the real cycle state.
    return shared_sentinel_service()


def get_admin_users_service() -> AdminUsersService:
    return AdminUsersService()


def get_admin_repo() -> AdminRepository:
    return AdminRepository()


@router.get("/state", response_model=AppStateOut)
async def get_state(
    user: Annotated[dict, Depends(require_authenticated)],
    ops: OpsStateService = Depends(get_ops_service),
) -> AppStateOut:
    """Operational state visible to any signed-in user (powers the banner)."""
    return AppStateOut(**await ops.get_state())


@router.post("/state", response_model=AppStateOut)
async def set_state(
    req: SetAppStateRequest,
    user: AdminUser,
    ops: OpsStateService = Depends(get_ops_service),
) -> AppStateOut:
    state = await ops.set_status(status=req.status.value, message=req.message)
    return AppStateOut(**state)


@router.post("/toggles/{name}", response_model=AppStateOut)
async def set_toggle(
    name: str,
    req: SetToggleRequest,
    user: AdminUser,
    ops: OpsStateService = Depends(get_ops_service),
) -> AppStateOut:
    allowed = {"swarm", "git_ops", "deployments", "ai_routing", "sentinel", "signups", "telemetry"}
    if name not in allowed:
        raise HTTPException(status_code=400, detail=f"Unknown toggle '{name}'.")
    return AppStateOut(**await ops.set_toggle(name, req.enabled))


@router.get("/providers/usage", response_model=ProviderUsageListOut)
async def provider_usage(
    user: AdminUser,
    ops: OpsStateService = Depends(get_ops_service),
) -> ProviderUsageListOut:
    rows = await ops.repo.list_provider_metrics()
    lookup = {r["provider"]: r for r in rows}
    out = []
    for entry in list_catalog():
        row = lookup.get(entry["id"], {})
        status_value = row.get("status") or "untested"
        out.append(
            ProviderUsageOut(
                provider=entry["id"],
                status=status_value,
                message=row.get("message") or "",
                model_count=row.get("model_count") or 0,
                tokens_used=row.get("tokens_used") or 0,
                balance_available=row.get("balance_available"),
                checked_at=row.get("checked_at"),
                suggestion=PROVIDER_SUGGESTIONS.get(status_value, ""),
            )
        )
    return ProviderUsageListOut(providers=out)


@router.get(
    "/sentinel/events",
    response_model=list[SentinelEventOut],
    dependencies=[Depends(require_service("sentinel"))],
)
async def sentinel_events(user: AdminUser, repo: AdminRepository = Depends(get_admin_repo)) -> list[SentinelEventOut]:
    events = await repo.list_events(limit=200)
    return [SentinelEventOut(**e) for e in events]


@router.get(
    "/sentinel/discussion",
    response_model=list[SentinelDiscussionEntryOut],
    dependencies=[Depends(require_service("sentinel"))],
)
async def sentinel_discussion(user: AdminUser, repo: AdminRepository = Depends(get_admin_repo)) -> list[SentinelDiscussionEntryOut]:
    discussion = await repo.list_discussion(limit=200)
    return [SentinelDiscussionEntryOut(**d) for d in discussion]


@router.get(
    "/sentinel/snapshot",
    response_model=SentinelSnapshotOut,
    dependencies=[Depends(require_service("sentinel"))],
)
async def sentinel_snapshot(
    user: AdminUser,
    service: SentinelService = Depends(get_sentinel_service),
) -> SentinelSnapshotOut:
    events = await service.repo.list_events(limit=100)
    discussion = await service.repo.list_discussion(limit=100)
    return SentinelSnapshotOut(
        running=service.running,
        last_run_at=service.last_run_at,
        interval_seconds=get_settings().sentinel_interval_seconds,
        events=[SentinelEventOut(**e) for e in events],
        discussion=[SentinelDiscussionEntryOut(**d) for d in discussion],
    )


@router.post(
    "/sentinel/run",
    response_model=RunSentinelOut,
    dependencies=[Depends(require_service("sentinel"))],
)
async def run_sentinel(
    user: AdminUser,
    service: SentinelService = Depends(get_sentinel_service),
) -> RunSentinelOut:
    result = await service.run_cycle()
    return RunSentinelOut(**result)


def _is_banned(banned_until: object) -> bool:
    if not banned_until:
        return False
    try:
        until = datetime.fromisoformat(str(banned_until).replace("Z", "+00:00"))
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
        return until > datetime.now(timezone.utc)
    except (TypeError, ValueError):
        # Malformed Supabase data must not keep an admin stream alive.
        return True


async def _still_admin(
    token: str | None,
    user: dict,
    users: AdminUsersService,
    ops: OpsStateService,
) -> bool:
    """Re-check auth, admin status and the feature gate on long-lived streams."""
    try:
        await ops.ensure_available("sentinel")
        current = (
            await require_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
            if token
            else user
        )
        sub = current.get("sub")
        if not sub:
            return False
        # Re-read the user from Supabase: the JWT's app_metadata is a snapshot
        # from sign-in and cannot reflect a later role change or suspension.
        fresh = await users.get_user(sub) if hasattr(users, "get_user") else current
        if _is_banned(fresh.get("banned_until")):
            return False
        metadata = fresh.get("app_metadata") or current.get("app_metadata") or {}
        return _is_admin({**current, "app_metadata": metadata})
    except Exception:
        return False


async def _sentinel_stream(
    service: SentinelService,
    token: str | None,
    user: dict,
    users: AdminUsersService,
    ops: OpsStateService,
):
    import asyncio
    import json
    queue = await service.bus.subscribe()
    last_check = 0.0
    try:
        while True:
            event = None
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
            except asyncio.TimeoutError:
                pass
            # Re-check at most every 15s: streams can be bursty, but Supabase
            # lookups must not scale with event volume.
            now = time.monotonic()
            if event is None or now - last_check >= 15.0:
                if not await _still_admin(token, user, users, ops):
                    break
                last_check = now
            if event is None:
                yield ": keepalive\n\n"
            else:
                yield f"data: {json.dumps(event)}\n\n"
    finally:
        await service.bus.unsubscribe(queue)


@router.get("/sentinel/stream", dependencies=[Depends(require_service("sentinel"))])
async def sentinel_stream(
    request: Request,
    user: AdminUser,
    service: SentinelService = Depends(get_sentinel_service),
    users: AdminUsersService = Depends(get_admin_users_service),
    ops: OpsStateService = Depends(get_ops_service),
) -> StreamingResponse:
    header = request.headers.get("authorization", "")
    token = header[7:].strip() if header.lower().startswith("bearer ") else None
    return StreamingResponse(
        _sentinel_stream(service, token, user, users, ops),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/users", response_model=UserListOut)
async def list_users(
    user: AdminUser, service: AdminUsersService = Depends(get_admin_users_service)
) -> UserListOut:
    rows = await service.list_users()
    return UserListOut(users=[UserRowOut(**row) for row in rows])


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    req: SuspendUserRequest,
    user: AdminUser,
    service: AdminUsersService = Depends(get_admin_users_service),
) -> dict:
    await service.suspend(user_id, req.duration_minutes)
    return {"user_id": user_id, "suspended": True, "duration_minutes": req.duration_minutes}


@router.post("/users/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    user: AdminUser,
    service: AdminUsersService = Depends(get_admin_users_service),
) -> dict:
    await service.reactivate(user_id)
    return {"user_id": user_id, "suspended": False}


@router.post("/account", response_model=UpdateAccountOut)
async def update_account(
    req: UpdateAccountRequest,
    user: AdminUser,
    service: AdminUsersService = Depends(get_admin_users_service),
) -> UpdateAccountOut:
    """Change the signed-in admin's login email and/or password."""
    payload = await service.set_identity(
        user["sub"],
        email=str(req.email).lower() if req.email else None,
        new_password=req.new_password,
    )
    parts = []
    if "email" in payload:
        parts.append("login email changed")
    if "password" in payload:
        parts.append("password changed")
    return UpdateAccountOut(
        user_id=user["sub"],
        email=str(req.email or user.get("email") or ""),
        message=", ".join(parts) + ".",
    )