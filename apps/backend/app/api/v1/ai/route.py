from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_authenticated
from app.schemas.ai import (
    AIDeleteOut,
    AIModelListOut,
    AIKeyStatusListOut,
    AISaveKeyRequest,
    AIValidateOut,
    ProviderCatalogListOut,
)
from app.services.ai_catalog import list_catalog
from app.services.ai_integration import AIIntegrationService

router = APIRouter()

AuthenticatedUser = Annotated[dict, Depends(require_authenticated)]


def get_ai_service() -> AIIntegrationService:
    return AIIntegrationService()


@router.get("/catalog", response_model=ProviderCatalogListOut)
async def get_provider_catalog(user: AuthenticatedUser) -> ProviderCatalogListOut:
    """Static catalog of curated free-tier AI providers."""
    return ProviderCatalogListOut(providers=list_catalog())


@router.get("/keys", response_model=AIKeyStatusListOut)
async def list_keys(
    user: AuthenticatedUser,
    service: AIIntegrationService = Depends(get_ai_service),
) -> AIKeyStatusListOut:
    owner_id = user.get("sub")
    return await service.statuses(owner_id)


@router.post("/keys", response_model=AIValidateOut)
async def save_key(
    req: AISaveKeyRequest,
    user: AuthenticatedUser,
    service: AIIntegrationService = Depends(get_ai_service),
) -> AIValidateOut:
    """Save (encrypted) + immediately validate a provider key with a first API call."""
    owner_id = user.get("sub")
    try:
        return await service.save_and_validate(
            owner_id, req.provider, req.api_key, req.ollama_base_url
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/keys/{provider}", response_model=AIDeleteOut)
async def delete_key(
    provider: str,
    user: AuthenticatedUser,
    service: AIIntegrationService = Depends(get_ai_service),
) -> AIDeleteOut:
    owner_id = user.get("sub")
    deleted = await service.delete(owner_id, provider)
    return AIDeleteOut(provider=provider, deleted=deleted)


@router.post("/keys/{provider}/validate", response_model=AIValidateOut)
async def validate_key(
    provider: str,
    user: AuthenticatedUser,
    service: AIIntegrationService = Depends(get_ai_service),
) -> AIValidateOut:
    """Re-run the provider's first API call to refresh the LED status."""
    owner_id = user.get("sub")
    try:
        return await service.validate(owner_id, provider)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/keys/{provider}/models", response_model=AIModelListOut)
async def list_provider_models(
    provider: str,
    user: AuthenticatedUser,
    service: AIIntegrationService = Depends(get_ai_service),
) -> AIModelListOut:
    """Live model list (10-minute in-process session cache)."""
    owner_id = user.get("sub")
    try:
        return await service.models(owner_id, provider)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc