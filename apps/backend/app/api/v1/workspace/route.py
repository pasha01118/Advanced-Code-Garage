from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.projects.route import get_project_service
from app.core.auth import _is_admin, require_authenticated
from app.schemas.advanced import (
    AuditListOut,
    BulkProjectRequest,
    BulkProjectResultOut,
    MetricsOverviewOut,
    ProjectMetaUpdateRequest,
    ProjectTemplateListOut,
    SearchOut,
)
from app.services.audit import AuditService
from app.services.ops_state import require_service
from app.services.project import ProjectService
from app.services.workspace import WorkspaceService

router = APIRouter()

AuthenticatedUser = Annotated[dict, Depends(require_authenticated)]


def get_workspace_service() -> WorkspaceService:
    return WorkspaceService()


def get_audit_service() -> AuditService:
    return AuditService()


@router.get("/search", response_model=SearchOut)
async def search_workspace(
    user: AuthenticatedUser,
    q: str = Query(default="", max_length=120),
    service: WorkspaceService = Depends(get_workspace_service),
) -> SearchOut:
    return SearchOut(results=await service.search(str(user.get("sub")), q))


@router.get("/templates", response_model=ProjectTemplateListOut)
async def list_templates(
    user: AuthenticatedUser,
    service: WorkspaceService = Depends(get_workspace_service),
) -> ProjectTemplateListOut:
    return ProjectTemplateListOut(templates=await service.list_templates())


@router.get("/metrics", response_model=MetricsOverviewOut)
async def workspace_metrics(
    user: AuthenticatedUser,
    service: WorkspaceService = Depends(get_workspace_service),
) -> MetricsOverviewOut:
    return MetricsOverviewOut(**await service.metrics(str(user.get("sub"))))


@router.get("/audit", response_model=AuditListOut)
async def workspace_audit(
    user: AuthenticatedUser,
    all_users: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    action: Optional[str] = Query(default=None, max_length=80),
    since: Optional[str] = None,
    audit: AuditService = Depends(get_audit_service),
) -> AuditListOut:
    owner_id = None
    if all_users:
        if not _is_admin(user):
            raise HTTPException(status_code=403, detail="Administrator access required.")
    else:
        owner_id = str(user.get("sub"))
    entries = await audit.list(owner_id, limit=limit, action=action, since=since)
    return AuditListOut(entries=entries)


@router.patch("/projects/{project_id}")
async def update_project_meta(
    project_id: str,
    req: ProjectMetaUpdateRequest,
    user: AuthenticatedUser,
    service: ProjectService = Depends(get_project_service),
) -> dict:
    row = await service.update_meta(
        str(user.get("sub")),
        project_id,
        req.model_dump(exclude_unset=True),
    )
    return {"id": str(row.get("id") or project_id), "updated": True}


@router.post(
    "/projects/bulk",
    response_model=BulkProjectResultOut,
    dependencies=[Depends(require_service("swarm"))],
)
async def bulk_project_action(
    req: BulkProjectRequest,
    user: AuthenticatedUser,
    service: ProjectService = Depends(get_project_service),
) -> BulkProjectResultOut:
    affected = await service.bulk_action(
        str(user.get("sub")), req.ids, req.action, req.value
    )
    return BulkProjectResultOut(affected=affected, action=req.action)
