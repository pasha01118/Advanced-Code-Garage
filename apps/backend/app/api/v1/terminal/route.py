from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import require_authenticated
from app.schemas.advanced import (
    HistoryCreateRequest,
    HistoryListOut,
    LogHistoryOut,
    SnippetCreateRequest,
    SnippetListOut,
    SnippetOut,
    SnippetUpdateRequest,
)
from app.services.terminal import TerminalService

router = APIRouter()

AuthenticatedUser = Annotated[dict, Depends(require_authenticated)]


def get_terminal_service() -> TerminalService:
    return TerminalService()


def _owner(user: dict) -> str:
    return str(user.get("sub"))


@router.get("/snippets", response_model=SnippetListOut)
async def list_snippets(
    user: AuthenticatedUser,
    service: TerminalService = Depends(get_terminal_service),
) -> SnippetListOut:
    return SnippetListOut(snippets=await service.list_snippets(_owner(user)))


@router.post("/snippets", response_model=SnippetOut, status_code=201)
async def create_snippet(
    req: SnippetCreateRequest,
    user: AuthenticatedUser,
    service: TerminalService = Depends(get_terminal_service),
) -> SnippetOut:
    return SnippetOut(**await service.create_snippet(_owner(user), req.name, req.command, req.description))


@router.patch("/snippets/{snippet_id}", response_model=SnippetOut)
async def update_snippet(
    snippet_id: str,
    req: SnippetUpdateRequest,
    user: AuthenticatedUser,
    service: TerminalService = Depends(get_terminal_service),
) -> SnippetOut:
    row = await service.update_snippet(
        _owner(user), snippet_id, req.model_dump(exclude_unset=True)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return SnippetOut(**row)


@router.delete("/snippets/{snippet_id}", status_code=204)
async def delete_snippet(
    snippet_id: str,
    user: AuthenticatedUser,
    service: TerminalService = Depends(get_terminal_service),
) -> None:
    if not await service.delete_snippet(_owner(user), snippet_id):
        raise HTTPException(status_code=404, detail="Snippet not found")


@router.get("/history", response_model=HistoryListOut)
async def list_history(
    user: AuthenticatedUser,
    limit: int = Query(default=100, ge=1, le=500),
    service: TerminalService = Depends(get_terminal_service),
) -> HistoryListOut:
    return HistoryListOut(entries=await service.list_history(_owner(user), limit))


@router.post("/history", response_model=dict, status_code=201)
async def add_history(
    req: HistoryCreateRequest,
    user: AuthenticatedUser,
    service: TerminalService = Depends(get_terminal_service),
) -> dict:
    row = await service.add_history(_owner(user), req.command)
    return {"id": str(row.get("id") or ""), "saved": True}


@router.delete("/history", status_code=204)
async def clear_history(
    user: AuthenticatedUser,
    service: TerminalService = Depends(get_terminal_service),
) -> None:
    await service.clear_history(_owner(user))


@router.get("/logs", response_model=LogHistoryOut)
async def log_history(
    user: AuthenticatedUser,
    limit: int = Query(default=100, ge=1, le=500),
    level: Optional[str] = Query(default=None, max_length=20),
    search: Optional[str] = Query(default=None, max_length=120),
    service: TerminalService = Depends(get_terminal_service),
) -> LogHistoryOut:
    entries = await service.log_history(
        _owner(user), limit=limit, level=level, search=search
    )
    return LogHistoryOut(entries=entries)
