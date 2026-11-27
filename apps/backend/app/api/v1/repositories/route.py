from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.auth import require_admin, require_authenticated
from app.schemas.repo_ops import (
    BranchCreateRequest,
    BranchListOut,
    BranchOut,
    CommitOut,
    CompareOut,
    ConfigApplyRequest,
    ConfigOut,
    ConfigPreviewOut,
    ConfigPreviewRequest,
    FileOut,
    FileWriteRequest,
    MergeOut,
    PullCreateRequest,
    PullListOut,
    PullMergeRequest,
    PullOut,
    PullUpdateRequest,
    RepoAuditListOut,
    RepoPermissionRequest,
    RepoRoleListOut,
    TemplateListOut,
    TreeListOut,
)
from app.schemas.repositories import RepositoryListOut, RepositoryOut
from app.services.github_app import GitHubAppService, get_github_app_service
from app.services.ops_state import require_service
from app.services.repo_ops import RepoOpsService, get_repo_ops_service

router = APIRouter()

GitOps = Depends(require_service("git_ops"))
RequestID = Header(default="", alias="X-Request-ID")


@router.get("/", response_model=RepositoryListOut)
async def list_repositories(
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    service: GitHubAppService = Depends(get_github_app_service),
) -> RepositoryListOut:
    rows = await service.repo.list_repositories()
    return RepositoryListOut(repositories=rows)


@router.get("/{repository_id}", response_model=RepositoryOut)
async def get_repository(
    repository_id: str,
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    service: GitHubAppService = Depends(get_github_app_service),
) -> RepositoryOut:
    row = await service.repo.get_repository(repository_id)
    if not row:
        raise HTTPException(status_code=404, detail="Repository not found")
    return RepositoryOut(**row)


# -- Branches -----------------------------------------------------------------

@router.get("/{repository_id}/branches", response_model=BranchListOut)
async def list_branches(
    repository_id: str,
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> BranchListOut:
    return await service.list_branches(repository_id, user)


@router.post("/{repository_id}/branches", response_model=BranchOut)
async def create_branch(
    repository_id: str,
    payload: BranchCreateRequest,
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    request_id: str = RequestID,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> BranchOut:
    return await service.create_branch(repository_id, user, payload, request_id)


@router.delete("/{repository_id}/branches/{branch:path}")
async def delete_branch(
    repository_id: str,
    branch: str,
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    request_id: str = RequestID,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> dict:
    return await service.delete_branch(repository_id, branch, user, request_id)


# -- Files --------------------------------------------------------------------

@router.get("/{repository_id}/files", response_model=TreeListOut)
async def list_files(
    repository_id: str,
    branch: str = "",
    path: str = "",
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> TreeListOut:
    return await service.list_files(repository_id, user, branch, path)


@router.get("/{repository_id}/file", response_model=FileOut)
async def get_file(
    repository_id: str,
    path: str,
    branch: str = "",
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> FileOut:
    return await service.get_file(repository_id, user, path, branch)


@router.put("/{repository_id}/file", response_model=CommitOut)
async def write_file(
    repository_id: str,
    payload: FileWriteRequest,
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    request_id: str = RequestID,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> CommitOut:
    return await service.write_file(repository_id, user, payload, request_id)


# -- Pull requests ------------------------------------------------------------

@router.get("/{repository_id}/pulls", response_model=PullListOut)
async def list_pulls(
    repository_id: str,
    state: str = "open",
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> PullListOut:
    return await service.list_pulls(repository_id, user, state)


@router.post("/{repository_id}/pulls", response_model=PullOut)
async def create_pull(
    repository_id: str,
    payload: PullCreateRequest,
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    request_id: str = RequestID,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> PullOut:
    return await service.create_pull(repository_id, user, payload, request_id)


@router.patch("/{repository_id}/pulls/{number}", response_model=PullOut)
async def update_pull(
    repository_id: str,
    number: int,
    payload: PullUpdateRequest,
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    request_id: str = RequestID,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> PullOut:
    return await service.update_pull(repository_id, number, user, payload, request_id)


@router.put("/{repository_id}/pulls/{number}/merge", response_model=MergeOut)
async def merge_pull(
    repository_id: str,
    number: int,
    payload: PullMergeRequest,
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    request_id: str = RequestID,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> MergeOut:
    return await service.merge_pull(repository_id, number, user, payload, request_id)


# -- Diffs --------------------------------------------------------------------

@router.get("/{repository_id}/compare", response_model=CompareOut)
async def compare(
    repository_id: str,
    base: str = "",
    head: str = "",
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> CompareOut:
    return await service.compare(repository_id, user, base, head)


# -- Customization ------------------------------------------------------------

@router.get("/{repository_id}/config", response_model=ConfigOut)
async def get_config(
    repository_id: str,
    branch: str = "",
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> ConfigOut:
    return await service.get_config(repository_id, user, branch)


@router.post("/{repository_id}/config/preview", response_model=ConfigPreviewOut)
async def preview_config(
    repository_id: str,
    payload: ConfigPreviewRequest,
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> ConfigPreviewOut:
    return await service.preview_config(repository_id, user, payload)


@router.post("/{repository_id}/config", response_model=CommitOut)
async def apply_config(
    repository_id: str,
    payload: ConfigApplyRequest,
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    request_id: str = RequestID,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> CommitOut:
    return await service.apply_config(repository_id, user, payload, request_id)


@router.get("/{repository_id}/templates", response_model=TemplateListOut)
async def list_templates(
    repository_id: str,
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> TemplateListOut:
    return await service.templates(repository_id, user)


# -- Audit + permissions ------------------------------------------------------

@router.get("/{repository_id}/audit", response_model=RepoAuditListOut)
async def list_audit(
    repository_id: str,
    limit: int = 100,
    user: dict = Depends(require_authenticated),
    _enabled=GitOps,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> RepoAuditListOut:
    return await service.audit(repository_id, user, limit)


@router.get("/{repository_id}/permissions", response_model=RepoRoleListOut)
async def list_permissions(
    repository_id: str,
    user: dict = Depends(require_admin),
    _enabled=GitOps,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> RepoRoleListOut:
    return await service.permissions(repository_id)


@router.post("/{repository_id}/permissions")
async def grant_permission(
    repository_id: str,
    payload: RepoPermissionRequest,
    user: dict = Depends(require_admin),
    _enabled=GitOps,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> dict:
    return await service.grant(
        repository_id, payload.user_id, payload.role, str(user.get("sub") or "")
    )


@router.delete("/{repository_id}/permissions/{user_id}")
async def revoke_permission(
    repository_id: str,
    user_id: str,
    user: dict = Depends(require_admin),
    _enabled=GitOps,
    service: RepoOpsService = Depends(get_repo_ops_service),
) -> dict:
    return {"revoked": await service.revoke(repository_id, user_id)}
