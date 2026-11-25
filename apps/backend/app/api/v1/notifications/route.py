from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import require_authenticated
from app.schemas.advanced import (
    NotificationCountsOut,
    NotificationListOut,
    NotificationOut,
)
from app.services.notifications import NotificationService

router = APIRouter()

AuthenticatedUser = Annotated[dict, Depends(require_authenticated)]


def get_notification_service() -> NotificationService:
    return NotificationService()


def _owner(user: dict) -> str:
    return str(user.get("sub"))


@router.get("/", response_model=NotificationListOut)
async def list_notifications(
    user: AuthenticatedUser,
    unread_only: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationListOut:
    rows = await service.list(_owner(user), limit=limit, unread_only=unread_only)
    return NotificationListOut(notifications=rows)


@router.get("/counts", response_model=NotificationCountsOut)
async def notification_counts(
    user: AuthenticatedUser,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationCountsOut:
    return NotificationCountsOut(**await service.counts(_owner(user)))


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: str,
    user: AuthenticatedUser,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationOut:
    row = await service.mark_read(_owner(user), notification_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationOut(**row)


@router.post("/read-all", response_model=dict)
async def mark_all_read(
    user: AuthenticatedUser,
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    count = await service.mark_all_read(_owner(user))
    return {"updated": count}


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: str,
    user: AuthenticatedUser,
    service: NotificationService = Depends(get_notification_service),
) -> None:
    if not await service.delete(_owner(user), notification_id):
        raise HTTPException(status_code=404, detail="Notification not found")


@router.delete("/", status_code=204)
async def clear_notifications(
    user: AuthenticatedUser,
    service: NotificationService = Depends(get_notification_service),
) -> None:
    await service.clear(_owner(user))
