from typing import Any, Literal

from pydantic import BaseModel, Field

Theme = Literal["dark", "light"]
Accent = Literal["blue", "emerald", "violet", "amber"]
Density = Literal["comfortable", "compact"]
NotificationType = Literal["info", "success", "warn", "error"]


class PreferencesOut(BaseModel):
    theme: Theme = "dark"
    accent: Accent = "blue"
    density: Density = "comfortable"
    reduced_motion: bool = False
    updated_at: str | None = None


class UpdatePreferencesRequest(BaseModel):
    theme: Theme | None = None
    accent: Accent | None = None
    density: Density | None = None
    reduced_motion: bool | None = None


class SnippetOut(BaseModel):
    id: str
    name: str
    command: str
    description: str
    created_at: str | None = None
    updated_at: str | None = None


class SnippetListOut(BaseModel):
    snippets: list[SnippetOut]


class SnippetCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    command: str = Field(min_length=1, max_length=4000)
    description: str = Field(default="", max_length=300)


class SnippetUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    command: str | None = Field(default=None, min_length=1, max_length=4000)
    description: str | None = Field(default=None, max_length=300)


class HistoryEntryOut(BaseModel):
    id: str
    command: str
    created_at: str | None = None


class HistoryListOut(BaseModel):
    entries: list[HistoryEntryOut]


class HistoryCreateRequest(BaseModel):
    command: str = Field(min_length=1, max_length=4000)


class LogHistoryEntryOut(BaseModel):
    timestamp: str | None = None
    level: str
    agent: str
    message: str
    project_id: str | None = None


class LogHistoryOut(BaseModel):
    entries: list[LogHistoryEntryOut]


class NotificationOut(BaseModel):
    id: str
    type: NotificationType
    title: str
    body: str
    source: str
    source_id: str | None = None
    read_at: str | None = None
    created_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationListOut(BaseModel):
    notifications: list[NotificationOut]


class NotificationReadOut(BaseModel):
    id: str
    read: bool


class NotificationCountsOut(BaseModel):
    total: int
    unread: int


class ProjectTemplateOut(BaseModel):
    id: str
    name: str
    description: str
    default_description: str
    default_status: str
    tags: list[str]
    sort_order: int


class ProjectTemplateListOut(BaseModel):
    templates: list[ProjectTemplateOut]


class ProjectMetaUpdateRequest(BaseModel):
    tags: list[str] | None = Field(default=None, max_length=20)
    template_id: str | None = None
    pinned: bool | None = None


class BulkProjectRequest(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=100)
    action: Literal["tag", "untag", "pin", "unpin", "delete", "status"]
    value: str | None = None


class BulkProjectResultOut(BaseModel):
    affected: int
    action: str


class SearchResultOut(BaseModel):
    type: str
    id: str
    title: str
    subtitle: str | None = None
    href: str


class SearchOut(BaseModel):
    results: list[SearchResultOut]


class AuditEntryOut(BaseModel):
    id: str
    actor: str | None = None
    action: str
    target: str | None = None
    detail: dict[str, Any] | None = None
    owner_id: str | None = None
    created_at: str | None = None


class AuditListOut(BaseModel):
    entries: list[AuditEntryOut]


class MetricPointOut(BaseModel):
    label: str
    value: int


class MetricsOverviewOut(BaseModel):
    projects_total: int
    projects_by_status: dict[str, int]
    projects_recent: list[MetricPointOut]
    active_agents: int
    system_mode: str
    providers_active: int
    providers_configured: int
    notifications_unread: int
    logs_recent: int
    sentinel_open: int
    app_status: str
