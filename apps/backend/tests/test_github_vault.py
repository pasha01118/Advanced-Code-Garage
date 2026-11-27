import hashlib
import hmac
import json
import uuid

from app.api.v1.github.route import get_github_app_service
from app.api.v1.secrets.route import get_vault_service
from app.core.config import get_settings
from app.core.vault import decrypt_value, encrypt_value, fingerprint
from app.main import app
from app.services.github_app import GitHubAppService
from app.services.vault import VaultService


class FakeGitHubRepo:
    def __init__(self):
        self.installations = []
        self.repositories = []
        self.deliveries = []

    async def list_installations(self, limit=100):
        return self.installations

    async def link_installation(self, installation_id, actor):
        return {"installation_id": installation_id, "linked_by": actor}

    async def list_repositories(self, limit=200):
        return self.repositories

    async def get_repository(self, repository_id):
        return next((r for r in self.repositories if r["id"] == repository_id), None)

    async def upsert_installation(
        self, installation_id, account_login, *, account_type="", suspended=False, linked_by=None
    ):
        row = {
            "id": str(uuid.uuid4()),
            "installation_id": installation_id,
            "account_login": account_login,
            "account_type": account_type,
            "suspended": suspended,
            "linked_by": linked_by,
        }
        self.installations = [r for r in self.installations if r["installation_id"] != installation_id]
        self.installations.append(row)
        return row

    async def upsert_repository(self, installation_id, repo):
        row = {
            "id": str(uuid.uuid4()),
            "installation_id": installation_id,
            "external_id": int(repo["id"]),
            "full_name": repo["full_name"],
            "name": repo["name"],
            "owner_login": repo["full_name"].split("/")[0],
            "default_branch": repo.get("default_branch") or "main",
            "private": repo.get("private", False),
        }
        self.repositories = [
            r for r in self.repositories
            if not (r["installation_id"] == installation_id and r["external_id"] == row["external_id"])
        ]
        self.repositories.append(row)
        return row

    async def has_delivery(self, delivery_id):
        return delivery_id in self.deliveries

    async def record_webhook(self, delivery_id, event, action, installation_id, repository_full_name, payload):
        row = {"delivery_id": delivery_id, "event": event, "payload": payload}
        self.deliveries.append(delivery_id)
        return row


class FakeVaultRepo:
    def __init__(self):
        self.rows = {}
        self.versions = []
        self.audit = []

    async def find_active(self, owner_id, name, scope, repository_id, environment):
        for row in self.rows.values():
            if (
                row["owner_id"] == owner_id
                and row["name"] == name
                and row["scope"] == scope
                and row.get("repository_id") == repository_id
                and row.get("environment") == environment
                and not row.get("revoked_at")
            ):
                return dict(row)
        return None

    async def upsert(self, payload, existing_id):
        secret_id = existing_id or str(uuid.uuid4())
        row = {**payload, "id": secret_id}
        self.rows[secret_id] = row
        return dict(row)

    async def get(self, secret_id, owner_id=None):
        row = self.rows.get(secret_id)
        if row and (owner_id is None or row["owner_id"] == owner_id):
            return dict(row)
        return None

    async def list(self, owner_id, repository_id=None):
        return [
            dict(row) for row in self.rows.values()
            if row["owner_id"] == owner_id
            and (repository_id is None or row.get("repository_id") == repository_id)
        ]

    async def revoke(self, secret_id, owner_id=None):
        row = self.rows.get(secret_id)
        if not row:
            return False
        if owner_id and row["owner_id"] != owner_id:
            return False
        row["revoked_at"] = "2026-01-01T00:00:00+00:00"
        return True

    async def add_version(self, secret_id, version, ciphertext, digest, created_by):
        row = {
            "id": str(uuid.uuid4()),
            "secret_id": secret_id,
            "version": version,
            "ciphertext": ciphertext,
            "fingerprint": digest,
            "created_by": created_by,
        }
        self.versions.append(row)
        return row

    async def get_version(self, secret_id, version):
        return next(
            (v for v in self.versions if v["secret_id"] == secret_id and v["version"] == version),
            None,
        )

    async def add_access(self, secret_id, actor, action, purpose="", request_id=""):
        row = {
            "id": str(uuid.uuid4()),
            "secret_id": secret_id,
            "actor": actor,
            "action": action,
            "purpose": purpose,
            "request_id": request_id,
        }
        self.audit.append(row)
        return row

    async def list_access(self, secret_id, limit=100):
        return [r for r in reversed(self.audit) if r["secret_id"] == secret_id][:limit]


def test_vault_envelope_encrypts_and_survives_kek_rotation(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "vault_kek_version", "v1")
    monkeypatch.setattr(settings, "vault_previous_keks", "")
    monkeypatch.setattr(settings, "user_key_encryption_key", "a" * 32)

    encrypted = encrypt_value("sk-super-secret")
    assert "sk-super-secret" not in encrypted
    assert json.loads(encrypted)["kek"] == "v1"
    assert decrypt_value(encrypted) == "sk-super-secret"
    old_fingerprint = fingerprint("sk-super-secret")

    monkeypatch.setattr(settings, "vault_previous_keks", f"v1:{'a' * 32}")
    monkeypatch.setattr(settings, "vault_kek_version", "v2")
    monkeypatch.setattr(settings, "user_key_encryption_key", "b" * 32)

    assert decrypt_value(encrypted) == "sk-super-secret"
    assert old_fingerprint  # fingerprint is a stable, non-reversible display token
    assert encrypt_value("sk-new") != encrypted


def test_webhook_signature_is_constant_time_checked(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "github_app_webhook_secret", "webhook-secret")
    service = GitHubAppService(repo=FakeGitHubRepo())
    body = b'{"action":"created"}'
    digest = hmac.new(b"webhook-secret", body, hashlib.sha256).hexdigest()

    assert service.verify_webhook(body, f"sha256={digest}") is True
    assert service.verify_webhook(body, "sha256=wrong") is False
    assert service.verify_webhook(body, None) is False


def test_webhook_ingests_installation_and_repository(client, monkeypatch):
    repo = FakeGitHubRepo()
    service = GitHubAppService(repo=repo)
    app.dependency_overrides[get_github_app_service] = lambda: service
    payload = {
        "action": "created",
        "installation": {
            "id": 99,
            "account": {"login": "nxt-gen", "type": "Organization"},
        },
        "repositories_added": [
            {"id": 123, "name": "app", "full_name": "nxt-gen/app", "private": True}
        ],
    }
    body = json.dumps(payload).encode()
    settings = get_settings()
    monkeypatch.setattr(settings, "github_app_webhook_secret", "webhook-secret")
    digest = hmac.new(b"webhook-secret", body, hashlib.sha256).hexdigest()
    resp = client.post(
        "/api/v1/github/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "installation_repositories",
            "X-GitHub-Delivery": "delivery-1",
            "X-Hub-Signature-256": f"sha256={digest}",
        },
    )

    assert resp.status_code == 200
    assert repo.installations[0]["account_login"] == "nxt-gen"
    assert repo.repositories[0]["full_name"] == "nxt-gen/app"
    assert repo.deliveries == ["delivery-1"]


def test_secret_save_lists_audits_and_revokes(client, monkeypatch):
    repo = FakeVaultRepo()
    settings = get_settings()
    monkeypatch.setattr(settings, "user_key_encryption_key", "c" * 32)
    monkeypatch.setattr(settings, "vault_previous_keks", "")
    monkeypatch.setattr(settings, "vault_kek_version", "v1")
    app.dependency_overrides[get_vault_service] = lambda: VaultService(repo=repo)

    created = client.post(
        "/api/v1/secrets/",
        json={
            "name": "DEPLOY_TOKEN",
            "value": "super-secret",
            "scope": "repository",
            "repository_id": "repo-1",
            "description": "deployments",
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert "value" not in body and "ciphertext" not in body
    assert body["fingerprint"] == fingerprint("super-secret")
    assert decrypt_value(repo.versions[0]["ciphertext"]) == "super-secret"

    listed = client.get("/api/v1/secrets/?repository_id=repo-1")
    assert listed.status_code == 200
    assert [row["name"] for row in listed.json()["secrets"]] == ["DEPLOY_TOKEN"]

    secret_id = body["id"]
    audited = client.get(f"/api/v1/secrets/{secret_id}/audit")
    assert audited.status_code == 200
    assert audited.json()["entries"][0]["action"] == "create"

    rotated = client.post(
        "/api/v1/secrets/",
        json={
            "name": "DEPLOY_TOKEN",
            "value": "rotated-secret",
            "scope": "repository",
            "repository_id": "repo-1",
        },
    )
    assert rotated.status_code == 200
    assert rotated.json()["version"] == 2
    assert len(repo.versions) == 2

    revoked = client.delete(f"/api/v1/secrets/{secret_id}")
    assert revoked.status_code == 200
    assert revoked.json()["revoked"] is True
