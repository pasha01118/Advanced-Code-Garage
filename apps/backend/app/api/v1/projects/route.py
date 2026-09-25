from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import require_authenticated
from app.schemas.project import ProjectListOut, ProjectOut
from app.services.ops_state import require_service
from app.services.project import ProjectService

router = APIRouter()


class ProjectInitRequest(BaseModel):
    name: str
    description: Optional[str] = None
    repo_url: Optional[str] = None


AuthenticatedUser = Annotated[dict, Depends(require_authenticated)]


def get_project_service() -> ProjectService:
    return ProjectService()


@router.post("/", response_model=ProjectOut, dependencies=[Depends(require_service("swarm"))])
async def initialize_project(
    req: ProjectInitRequest,
    user: AuthenticatedUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectOut:
    owner_id = user.get("sub")
    project = await service.create(req.name, req.description, req.repo_url, owner_id)
    return ProjectOut(**project)


@router.get("/", response_model=ProjectListOut)
async def list_projects(user: AuthenticatedUser, service: ProjectService = Depends(get_project_service)) -> ProjectListOut:
    return ProjectListOut(projects=await service.list_recent())


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project_status(
    project_id: str,
    user: AuthenticatedUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectOut:
    project = await service.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(**project)