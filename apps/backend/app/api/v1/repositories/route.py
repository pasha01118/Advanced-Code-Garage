from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_authenticated
from app.schemas.repositories import RepositoryListOut, RepositoryOut
from app.services.github_app import GitHubAppService, get_github_app_service
from app.services.ops_state import require_service

router = APIRouter()


@router.get("/", response_model=RepositoryListOut)
async def list_repositories(
    user: dict = Depends(require_authenticated),
    _enabled=Depends(require_service("git_ops")),
    service: GitHubAppService = Depends(get_github_app_service),
) -> RepositoryListOut:
    rows = await service.repo.list_repositories()
    return RepositoryListOut(repositories=rows)


@router.get("/{repository_id}", response_model=RepositoryOut)
async def get_repository(
    repository_id: str,
    user: dict = Depends(require_authenticated),
    _enabled=Depends(require_service("git_ops")),
    service: GitHubAppService = Depends(get_github_app_service),
) -> RepositoryOut:
    row = await service.repo.get_repository(repository_id)
    if not row:
        raise HTTPException(status_code=404, detail="Repository not found")
    return RepositoryOut(**row)
