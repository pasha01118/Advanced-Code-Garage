from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SecretScope = Literal["user", "repository", "environment"]


class SecretCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_]+$")
    value: str = Field(min_length=1, max_length=8192)
    scope: SecretScope = "repository"
    repository_id: str | None = None
    environment: str | None = Field(default=None, max_length=64)
    description: str = Field(default="", max_length=300)


class SecretOut(BaseModel):
    id: str
    name: str
    scope: SecretScope
    repository_id: str | None = None
    environment: str | None = None
    description: str = ""
    fingerprint: str
    version: int
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    revoked_at: datetime | None = None


class SecretListOut(BaseModel):
    secrets: list[SecretOut]


class SecretRevokeOut(BaseModel):
    id: str
    revoked: bool


class SecretAuditOut(BaseModel):
    id: str
    secret_id: str
    actor: str
    action: str
    purpose: str = ""
    request_id: str = ""
    created_at: datetime | None = None


class SecretAuditListOut(BaseModel):
    entries: list[SecretAuditOut]
