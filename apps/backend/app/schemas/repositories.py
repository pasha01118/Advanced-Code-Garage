from datetime import datetime

from pydantic import BaseModel


class InstallationOut(BaseModel):
    id: str
    installation_id: int
    account_login: str
    account_type: str = ""
    suspended: bool = False
    linked_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InstallationListOut(BaseModel):
    installations: list[InstallationOut]


class SyncOut(BaseModel):
    installation_id: int
    repositories_added: int
    repositories_updated: int
    total: int


class RepositoryOut(BaseModel):
    id: str
    installation_id: int
    external_id: int
    full_name: str
    name: str
    owner_login: str
    private: bool = False
    default_branch: str = "main"
    html_url: str = ""
    archived: bool = False
    disabled: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RepositoryListOut(BaseModel):
    repositories: list[RepositoryOut]
