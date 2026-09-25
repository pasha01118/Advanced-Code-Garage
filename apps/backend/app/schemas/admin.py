from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class AppStatus(str, Enum):
    running = "running"
    maintenance = "maintenance"
    shutdown = "shutdown"


class AppStateOut(BaseModel):
    status: AppStatus
    message: str
    toggles: dict[str, bool]
    updated_at: datetime | None = None


class SetAppStateRequest(BaseModel):
    status: AppStatus
    message: str = Field(default="", max_length=300)


class SetToggleRequest(BaseModel):
    enabled: bool


class ProviderUsageOut(BaseModel):
    provider: str
    status: str
    message: str = ""
    model_count: int = 0
    tokens_used: int = 0
    balance_available: float | None = None
    checked_at: datetime | None = None
    suggestion: str = ""


class ProviderUsageListOut(BaseModel):
    providers: list[ProviderUsageOut]


class SentinelEventOut(BaseModel):
    id: str
    created_at: datetime
    severity: str
    scope: str
    agent: str
    title: str
    message: str = ""
    status: str = "open"
    suggested_fix: str = ""
    auto_fix_report: str = ""


class SentinelDiscussionEntryOut(BaseModel):
    id: int
    created_at: datetime
    agent: str
    message: str


class SentinelSnapshotOut(BaseModel):
    running: bool
    last_run_at: datetime | None = None
    interval_seconds: int
    events: list[SentinelEventOut]
    discussion: list[SentinelDiscussionEntryOut]


class UserRowOut(BaseModel):
    id: str
    email: str
    created_at: datetime | None = None
    confirmed: bool = False
    banned_until: datetime | None = None
    admin: bool = False
    last_sign_in_at: datetime | None = None


class UserListOut(BaseModel):
    users: list[UserRowOut]


class SetUserRequest(BaseModel):
    action: str = Field(pattern="^(suspend|reactivate)$")
    duration_minutes: int = Field(default=60, ge=1, le=525600)


class SuspendUserRequest(BaseModel):
    duration_minutes: int = Field(default=60, ge=1, le=525600)


class UpdateAccountRequest(BaseModel):
    email: EmailStr | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=128)
    reset_token: str | None = None


class UpdateAccountOut(BaseModel):
    user_id: str | None = None
    email: str
    message: str


class RunSentinelOut(BaseModel):
    events_added: int
    discussion_added: int


class SentinelEventListOut(BaseModel):
    events: list[SentinelEventOut]


class SentinelDiscussionListOut(BaseModel):
    discussion: list[SentinelDiscussionEntryOut]