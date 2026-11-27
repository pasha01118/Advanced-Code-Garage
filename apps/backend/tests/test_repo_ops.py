import base64

import pytest
from fastapi import HTTPException

from app.api.v1.repositories.route import get_repo_ops_service
from app.core.auth import require_authenticated
from app.main import app
from app.schemas.repo_ops import (
    BranchCreateRequest,
    ConfigApplyRequest,
    ConfigPreviewRequest,
    FileWriteRequest,
    PullCreateRequest,
    RepoConfig,
)
from app.services.customization import CONFIG_PATH, config_diff, dump_config, parse_config
from app.services.repo_ops import RepoOpsService

ADMIN = {"sub": "admin", "role": "authenticated", "app_metadata": {"role": "admin"}}


class FakeRepoOpsRepository:
    def __init__(self, repository_id: str = "repo-1") -> None:
        self.repository = {
            "id": repository_id,
            "installation_id": 42,
            "full_name": "acme/demo",
            "default_branch": "main",
        }
        self.roles: dict[tuple[str, str], str] = {}
        self.audit: list[dict] = []
        self.idempotency: dict[str, dict] = {}

    async def get_repository(self, repository_id: str):
        return self.repository if repository_id == self.repository["id"] else None

    async def get_role(self, repository_id: str, user_id: str):
        return self.roles.get((repository_id, user_id))

    async def grant_permission(self, repository_id, user_id, role, granted_by):
        self.roles[(repository_id, user_id)] = role
        return {"role": role}

    async def revoke_permission(self, repository_id, user_id):
        return self.roles.pop((repository_id, user_id), None) is not None

    async def list_permissions(self, repository_id):
        return [
            {
                "id": f"perm-{i}",
                "repository_id": repository_id,
                "user_id": uid,
                "role": role,
            }
            for i, ((repo_id, uid), role) in enumerate(self.roles.items())
            if repo_id == repository_id
        ]

    async def add_audit(
        self, repository_id, actor, action, *, target="", detail=None, request_id=""
    ):
        row = {
            "id": f"audit-{len(self.audit)}",
            "repository_id": repository_id,
            "actor": actor,
            "action": action,
            "target": target,
            "detail": detail or {},
            "request_id": request_id,
        }
        self.audit.append(row)
        return row

    async def list_audit(self, repository_id, limit=100):
        return list(reversed(self.audit))[:limit]

    async def get_idempotent(self, key):
        return self.idempotency.get(key)

    async def record_idempotent(self, key, actor, repository_id, action, result):
        self.idempotency[key] = {"result": result}


class FakeGitHub:
    def __init__(self, repo: FakeRepoOpsRepository) -> None:
        self.repo = repo
        self.calls: list[tuple[str, str, dict | None, dict | None]] = []
        self.files: dict[str, str] = {}

    async def request(self, installation_id, method, path, *, json_body=None, params=None):
        self.calls.append((method, path, json_body, params))
        if method == "GET" and path.endswith("/branches/main"):
            return {"commit": {"sha": "source-sha"}}
        if method == "GET" and path.endswith("/branches"):
            return [{"name": "main", "commit": {"sha": "source-sha"}, "protected": True}]
        if method == "POST" and path.endswith("/git/refs"):
            return {"ref": json_body["ref"]}
        if method == "DELETE" and "/git/refs/heads/" in path:
            return {}
        if method == "GET" and "/git/trees/" in path:
            return {
                "tree": [
                    {"path": "README.md", "type": "blob", "sha": "a", "size": 12},
                    {"path": CONFIG_PATH, "type": "blob", "sha": "b", "size": 8},
                    {"path": "src", "type": "tree", "sha": "c"},
                ],
                "truncated": False,
            }
        if method == "GET" and "/contents/" in path:
            name = path.split("/contents/", 1)[1]
            if name not in self.files:
                raise HTTPException(status_code=404, detail="Not found")
            return {
                "content": base64.b64encode(self.files[name].encode()).decode(),
                "sha": f"sha-{name}",
                "size": len(self.files[name]),
            }
        if method == "PUT" and "/contents/" in path:
            name = path.split("/contents/", 1)[1]
            self.files[name] = base64.b64decode(json_body["content"]).decode()
            return {
                "commit": {"sha": "commit-1"},
                "content": {"html_url": f"https://github.com/acme/demo/blob/main/{name}"},
            }
        if method == "GET" and path.endswith("/pulls"):
            return [
                {
                    "number": 7,
                    "title": "Add feature",
                    "state": (params or {}).get("state", "open"),
                    "head": {"ref": "feature"},
                    "base": {"ref": "main"},
                    "html_url": "https://github.com/acme/demo/pull/7",
                    "draft": False,
                }
            ]
        if method == "POST" and path.endswith("/pulls"):
            return {
                "number": 8,
                "title": json_body["title"],
                "state": "open",
                "head": {"ref": json_body["head"]},
                "base": {"ref": json_body["base"]},
                "html_url": "https://github.com/acme/demo/pull/8",
                "draft": json_body["draft"],
            }
        if method == "PUT" and "/merge" in path:
            return {"merged": True, "sha": "merge-sha", "message": "Pull Request merged"}
        if method == "GET" and "/compare/" in path:
            return {
                "ahead_by": 1,
                "behind_by": 0,
                "total_commits": 1,
                "files": [
                    {
                        "filename": "README.md",
                        "status": "modified",
                        "additions": 1,
                        "deletions": 0,
                        "patch": "@@ -1 +1 @@\n+hello",
                    }
                ],
            }
        raise AssertionError(f"Unexpected GitHub call: {method} {path}")


@pytest.fixture()
def ops_env():
    repo = FakeRepoOpsRepository()
    github = FakeGitHub(repo)
    service = RepoOpsService(github=github)
    app.dependency_overrides[get_repo_ops_service] = lambda: service
    yield service, github, repo
    app.dependency_overrides.pop(get_repo_ops_service, None)


def test_customization_validates_and_round_trips_config():
    config = RepoConfig(agent_mode="Autonomous", required_checks=["pytest"])
    text = dump_config(config)
    assert parse_config(text) == config
    assert "agent_mode: Autonomous" in text
    assert "version: 1" in text
    assert "agent_mode: Manual" in config_diff(
        text, dump_config(RepoConfig(agent_mode="Manual"))
    )
    with pytest.raises(HTTPException):
        parse_config("- not a mapping")


@pytest.mark.asyncio
async def test_repo_ops_requires_explicit_permission(ops_env):
    service, _, repo = ops_env
    user = {"sub": "reader"}
    with pytest.raises(HTTPException) as denied:
        await service.authorize(repo.repository, user, write=False)
    assert denied.value.status_code == 403

    repo.roles[("repo-1", "reader")] = "read"
    await service.authorize(repo.repository, user, write=False)
    with pytest.raises(HTTPException):
        await service.authorize(repo.repository, user, write=True)


@pytest.mark.asyncio
async def test_repo_ops_branches_files_pr_diffs_and_audit(ops_env):
    service, github, repo = ops_env

    branches = await service.list_branches("repo-1", ADMIN)
    assert branches.branches[0].protected is True

    created = await service.create_branch(
        "repo-1", ADMIN, BranchCreateRequest(name="feature", from_ref="main")
    )
    assert created.name == "feature" and created.sha == "source-sha"

    files = await service.list_files("repo-1", ADMIN)
    assert [entry.path for entry in files.entries] == [
        "README.md",
        CONFIG_PATH,
        "src",
    ]

    github.files["README.md"] = "# Demo\n"
    fetched = await service.get_file("repo-1", ADMIN, "README.md")
    assert fetched.content == "# Demo\n"

    commit = await service.write_file(
        "repo-1",
        ADMIN,
        FileWriteRequest(
            path="README.md",
            content="# Changed\n",
            message="Update readme",
            idempotency_key="readme-1",
        ),
        request_id="req-1",
    )
    assert commit.commit_sha == "commit-1"
    assert github.files["README.md"] == "# Changed\n"

    pull = await service.create_pull(
        "repo-1",
        ADMIN,
        PullCreateRequest(title="Add feature", head="feature", base="main"),
    )
    assert pull.number == 8
    diff = await service.compare("repo-1", ADMIN, "main", "feature")
    assert diff.ahead_by == 1 and diff.files[0].filename == "README.md"

    # A replayed idempotency key must not call GitHub again.
    before = len(github.calls)
    await service.write_file(
        "repo-1",
        ADMIN,
        FileWriteRequest(
            path="README.md",
            content="# Changed\n",
            message="Update readme",
            idempotency_key="readme-1",
        ),
    )
    assert len(github.calls) == before

    actions = [entry["action"] for entry in repo.audit]
    assert "branch.create" in actions
    assert "file.write" in actions
    assert "pull.create" in actions
    assert any(entry["request_id"] == "req-1" for entry in repo.audit)


@pytest.mark.asyncio
async def test_config_is_write_only_metadata_until_committed(ops_env):
    service, github, _ = ops_env

    current = await service.get_config("repo-1", ADMIN)
    assert current.exists is False and current.config.agent_mode == "AI-Man"

    preview = await service.preview_config(
        "repo-1",
        ADMIN,
        ConfigPreviewRequest(config=RepoConfig(agent_mode="Autonomous")),
    )
    assert preview.changed is True and "agent_mode: Autonomous" in preview.diff

    applied = await service.apply_config(
        "repo-1",
        ADMIN,
        ConfigApplyRequest(
            config=RepoConfig(agent_mode="Autonomous"),
            idempotency_key="config-1",
        ),
    )
    assert applied.commit_sha == "commit-1"
    assert "agent_mode: Autonomous" in github.files[CONFIG_PATH]

    reread = await service.get_config("repo-1", ADMIN)
    assert reread.exists is True and reread.config.agent_mode == "Autonomous"


def test_repo_ops_api_routes(client, ops_env):
    _, _, repo = ops_env
    repo.roles[("repo-1", "test-user")] = "owner"

    assert client.get("/api/v1/repositories/repo-1/branches").status_code == 200
    assert client.get("/api/v1/repositories/repo-1/files").status_code == 200
    assert client.get("/api/v1/repositories/repo-1/pulls").status_code == 200
    assert client.get("/api/v1/repositories/repo-1/templates").status_code == 200
    assert client.get("/api/v1/repositories/repo-1/audit").status_code == 200

    config = client.get("/api/v1/repositories/repo-1/config")
    assert config.status_code == 200 and config.json()["exists"] is False

    preview = client.post(
        "/api/v1/repositories/repo-1/config/preview",
        json={"config": {"agent_mode": "Manual"}},
    )
    assert preview.status_code == 200 and preview.json()["changed"] is True

    applied = client.post(
        "/api/v1/repositories/repo-1/config",
        json={"config": {"agent_mode": "Manual"}, "idempotency_key": "api-config"},
    )
    assert applied.status_code == 200 and applied.json()["commit_sha"] == "commit-1"

    # A fresh role-less user is rejected.
    repo.roles.pop(("repo-1", "test-user"))
    assert client.get("/api/v1/repositories/repo-1/branches").status_code == 403


def test_permission_routes_require_admin(client, ops_env):
    assert client.get("/api/v1/repositories/repo-1/permissions").status_code == 403

    app.dependency_overrides[require_authenticated] = lambda: ADMIN
    assert client.get("/api/v1/repositories/repo-1/permissions").status_code == 200
    granted = client.post(
        "/api/v1/repositories/repo-1/permissions",
        json={"user_id": "test-user", "role": "write"},
    )
    assert granted.status_code == 200
    assert client.delete(
        "/api/v1/repositories/repo-1/permissions/test-user"
    ).json() == {"revoked": True}
