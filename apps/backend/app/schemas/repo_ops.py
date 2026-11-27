from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

AgentMode = Literal["Autonomous", "AI-Man", "Manual"]


class BranchOut(BaseModel):
    name: str
    sha: str = ""
    protected: bool = False


class BranchListOut(BaseModel):
    branches: list[BranchOut]


class BranchCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    from_ref: str = Field(default="", max_length=255)


class TreeEntryOut(BaseModel):
    path: str
    type: str = "blob"
    sha: str = ""
    size: int | None = None


class TreeListOut(BaseModel):
    branch: str
    truncated: bool = False
    entries: list[TreeEntryOut]


class FileOut(BaseModel):
    path: str
    branch: str
    content: str
    sha: str = ""
    size: int = 0
    truncated: bool = False


class FileWriteRequest(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    content: str = Field(max_length=2_000_000)
    message: str = Field(default="Update via Advanced Code Garage", max_length=500)
    branch: str = Field(default="", max_length=255)
    sha: str = Field(default="", max_length=100)
    idempotency_key: str = Field(default="", max_length=200)


class CommitOut(BaseModel):
    commit_sha: str = ""
    path: str = ""
    branch: str = ""
    content_url: str = ""


class PullOut(BaseModel):
    number: int
    title: str
    state: str = "open"
    head: str = ""
    base: str = ""
    url: str = ""
    draft: bool = False


class PullListOut(BaseModel):
    pulls: list[PullOut]


class PullCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    head: str = Field(min_length=1, max_length=255)
    base: str = Field(default="", max_length=255)
    body: str = Field(default="", max_length=10_000)
    draft: bool = False
    idempotency_key: str = Field(default="", max_length=200)


class PullUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    body: str | None = Field(default=None, max_length=10_000)
    state: Literal["open", "closed"] | None = None


class PullMergeRequest(BaseModel):
    merge_method: Literal["merge", "squash", "rebase"] = "merge"
    commit_title: str = Field(default="", max_length=300)
    commit_message: str = Field(default="", max_length=2000)
    idempotency_key: str = Field(default="", max_length=200)


class MergeOut(BaseModel):
    merged: bool
    sha: str = ""
    message: str = ""


class CompareFileOut(BaseModel):
    filename: str
    status: str = ""
    additions: int = 0
    deletions: int = 0
    patch: str = ""


class CompareOut(BaseModel):
    base: str
    head: str
    ahead_by: int = 0
    behind_by: int = 0
    total_commits: int = 0
    files: list[CompareFileOut]


class RepoConfig(BaseModel):
    version: int = Field(default=1, ge=1, le=100)
    agent_mode: AgentMode = "AI-Man"
    allowed_providers: list[str] = Field(default_factory=list)
    review_rules: list[str] = Field(default_factory=list)
    required_checks: list[str] = Field(default_factory=list)
    deployment_targets: list[str] = Field(default_factory=list)
    branch_protection: bool = False
    secret_bindings: dict[str, str] = Field(default_factory=dict)
    custom_commands: dict[str, str] = Field(default_factory=dict)


class ConfigOut(BaseModel):
    repository_id: str
    branch: str
    path: str
    exists: bool
    sha: str = ""
    config: RepoConfig
    yaml: str


class ConfigPreviewRequest(BaseModel):
    config: RepoConfig
    branch: str = Field(default="", max_length=255)
    message: str = Field(default="Update .acg/config.yaml", max_length=500)


class ConfigPreviewOut(BaseModel):
    path: str
    branch: str
    diff: str
    changed: bool


class ConfigApplyRequest(BaseModel):
    config: RepoConfig
    branch: str = Field(default="", max_length=255)
    message: str = Field(default="Update .acg/config.yaml", max_length=500)
    idempotency_key: str = Field(default="", max_length=200)


class TemplateOut(BaseModel):
    id: str
    name: str
    description: str = ""
    config: RepoConfig


class TemplateListOut(BaseModel):
    templates: list[TemplateOut]


class RepoAuditOut(BaseModel):
    id: str
    repository_id: str
    actor: str
    action: str
    target: str = ""
    detail: dict[str, Any] = Field(default_factory=dict)
    request_id: str = ""
    created_at: datetime | None = None


class RepoAuditListOut(BaseModel):
    entries: list[RepoAuditOut]


class RepoRoleOut(BaseModel):
    id: str
    repository_id: str
    user_id: str
    role: str
    granted_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RepoRoleListOut(BaseModel):
    entries: list[RepoRoleOut]


class RepoPermissionRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=255)
    role: Literal["owner", "write", "read"]
