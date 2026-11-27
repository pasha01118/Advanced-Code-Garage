from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import require_authenticated
from app.schemas.advanced import PreferencesOut, UpdatePreferencesRequest
from app.services.preferences import PreferencesService

router = APIRouter()

AuthenticatedUser = Annotated[dict, Depends(require_authenticated)]


def get_preferences_service() -> PreferencesService:
    return PreferencesService()


@router.get("/", response_model=PreferencesOut)
async def get_preferences(
    user: AuthenticatedUser,
    service: PreferencesService = Depends(get_preferences_service),
) -> PreferencesOut:
    return PreferencesOut(**await service.get(str(user.get("sub"))))


@router.put("/", response_model=PreferencesOut)
async def update_preferences(
    req: UpdatePreferencesRequest,
    user: AuthenticatedUser,
    service: PreferencesService = Depends(get_preferences_service),
) -> PreferencesOut:
    return PreferencesOut(
        **await service.update(str(user.get("sub")), req.model_dump(exclude_unset=True))
    )
