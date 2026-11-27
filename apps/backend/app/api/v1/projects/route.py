from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth import require_authenticated
from app.schemas.project import ProjectListOut, ProjectOut
from app.services.notifications import NotificationService
from app.services.ops_state import require_service
from app.services.project import ProjectService

router = APIRouter()


class ProjectInitRequest(BaseModel):
    name: str
    description: Optional[str] = None
    repo_url: Optional[str] = None
    template_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list, max_length=20)


AuthenticatedUser = Annotated[dict, Depends(require_authenticated)]


def get_project_service() -> ProjectService:
    return ProjectService(notifications=NotificationService())


@router.post("/", response_model=ProjectOut, dependencies=[Depends(require_service("swarm"))])
async def initialize_project(
    req: ProjectInitRequest,
    user: AuthenticatedUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectOut:
    owner_id = user.get("sub")
    project = await service.create(
        req.name,
        req.description,
        req.repo_url,
        owner_id,
        tags=req.tags,
        template_id=req.template_id,
    )
    return ProjectOut(**project)


@router.get("/", response_model=ProjectListOut)
async def list_projects(
    user: AuthenticatedUser,
    status: Optional[str] = Query(default=None, pattern="^(queued|analyzing|delivered|failed)$"),
    tag: Optional[str] = None,
    search: Optional[str] = Query(default=None, max_length=120),
    limit: int = Query(default=100, ge=1, le=200),
    service: ProjectService = Depends(get_project_service),
) -> ProjectListOut:
    projects = await service.list_filtered(
        str(user.get("sub")), status=status, tag=tag, search=search, limit=limit
    )
    return ProjectListOut(projects=[ProjectOut(**project) for project in projects])


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project_status(
    project_id: str,
    user: AuthenticatedUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectOut:
    # Service-role DB access bypasses RLS, so ownership must be enforced here.
    project = await service.get(project_id, user.get("sub"))
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(**project)