from typing import Optional

from pydantic import BaseModel, Field


class ProjectOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    repo_url: Optional[str] = None
    status: str = "queued"
    progress: int = Field(default=0, ge=0, le=100)
    current_agent: Optional[str] = None
    current_task: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    template_id: Optional[str] = None
    pinned: bool = False


class ProjectListOut(BaseModel):
    projects: list[ProjectOut] = Field(default_factory=list)
