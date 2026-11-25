import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.auth import _is_admin, require_authenticated
from app.schemas.auth import (
    AdminBootstrapOut,
    AdminBootstrapRequest,
    AdminForgotPasswordOut,
    AdminForgotPasswordRequest,
    AuthMeOut,
)
from app.services.admin_users import AdminUsersService
from app.services.auth_bootstrap import BootstrapError, BootstrapService
from app.core.config import get_settings
from app.core.rate_limit import enforce_rate_limit
from app.services.ops_state import require_service

router = APIRouter()

AuthenticatedUser = Annotated[dict, Depends(require_authenticated)]


@router.get("/me", response_model=AuthMeOut)
async def auth_me(user: AuthenticatedUser) -> AuthMeOut:
    """Expose the caller's effective admin status (including the env allowlist)."""
    return AuthMeOut(
        user_id=user.get("sub", ""),
        email=user.get("email"),
        is_admin=_is_admin(user),
    )


def get_bootstrap_service() -> BootstrapService:
    return BootstrapService()


def get_admin_users_service() -> AdminUsersService:
    return AdminUsersService()


async def _limit_bootstrap(request: Request) -> None:
    await enforce_rate_limit("bootstrap", request)


async def _limit_password_reset(request: Request) -> None:
    await enforce_rate_limit("admin-reset", request)


@router.post(
    "/bootstrap",
    response_model=AdminBootstrapOut,
    dependencies=[Depends(_limit_bootstrap), Depends(require_service("signups"))],
)
async def bootstrap_admin(
    req: AdminBootstrapRequest,
    service: BootstrapService = Depends(get_bootstrap_service),
) -> AdminBootstrapOut:
    """First-run Admin Sign-Up.

    Creates the platform admin directly (no confirmation email needed) and
    marks it with ``app_metadata.role == "admin"``. Only allowed while no
    admin exists yet; afterward sign-up must go through a future
    server-integrated (email-confirmed) flow.
    """
    try:
        result = await service.bootstrap(
            email=str(req.email).lower(),
            password=req.password,
            name=req.name,
            token=req.bootstrap_token,
        )
    except BootstrapError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return AdminBootstrapOut(**result)


async def _resolve_admin_users() -> list[dict]:
    settings = get_settings()
    allowlisted = {s.strip() for s in settings.admin_user_ids.split(",") if s.strip()}
    users = await AdminUsersService().list_users()
    return [u for u in users if u["admin"] or u.get("id") in allowlisted]


@router.post(
    "/admin/forgot-password",
    response_model=AdminForgotPasswordOut,
    dependencies=[Depends(_limit_password_reset)],
)
async def admin_forgot_password(
    req: AdminForgotPasswordRequest,
) -> AdminForgotPasswordOut:
    """No-email admin password reset.

    Unlocks only when ADMIN_RESET_TOKEN is configured; the admin supplies the
    reset token plus a new password (optionally targeting a specific account
    by email — defaults to the single admin account).
    """
    settings = get_settings()
    if not settings.admin_reset_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin password reset is disabled on this deployment.",
        )
    if not hmac.compare_digest(settings.admin_reset_token, req.reset_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reset token.")

    admins = await _resolve_admin_users()
    if req.email:
        admins = [u for u in admins if u["email"] == str(req.email).lower()]
    if not admins:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No admin account found.")
    if len(admins) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Multiple admin accounts exist — supply an email to target one.",
        )

    await AdminUsersService().set_identity(admins[0]["id"], new_password=req.new_password)
    return AdminForgotPasswordOut(
        user_id=admins[0]["id"],
        email=admins[0]["email"],
        message="Admin password has been reset. Sign in with the new password.",
    )