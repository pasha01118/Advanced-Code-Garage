from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import require_admin
from app.schemas.auth import (
    AdminBootstrapOut,
    AdminBootstrapRequest,
    AdminForgotPasswordOut,
    AdminForgotPasswordRequest,
)
from app.services.admin_users import AdminUsersService
from app.services.auth_bootstrap import BootstrapError, BootstrapService
from app.core.config import get_settings

router = APIRouter()


def get_bootstrap_service() -> BootstrapService:
    return BootstrapService()


def get_admin_users_service() -> AdminUsersService:
    return AdminUsersService()


@router.post("/bootstrap", response_model=AdminBootstrapOut)
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
    users = await AdminUsersService().list_users()
    return [u for u in users if u["admin"]]


@router.post("/admin/forgot-password", response_model=AdminForgotPasswordOut)
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
    if settings.admin_reset_token != req.reset_token:
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