import pytest
from fastapi.testclient import TestClient

from app.api.v1.admin.route import get_admin_repo, get_admin_users_service, get_ops_service, get_sentinel_service
from app.api.v1.auth.route import get_admin_users_service as auth_get_admin_users_service
from app.core.auth import require_admin, require_authenticated
from app.main import app
from app.repositories.admin_repo import AdminRepository
from app.services.admin_users import AdminUsersService
from app.services.ops_state import OpsStateService
from app.services.sentinel import SentinelService

from tests.fakes import (
    FakeAdminRepository,
    FakeAIKeysRepository,
    FakeAgentLogsRepository,
)


def _authed_user():
    return {"sub": "test-user", "role": "authenticated", "email": "tester@example.com"}


def _admin_user():
    return {"sub": "admin-user", "role": "authenticated", "email": "admin@example.com", "app_metadata": {"role": "admin"}}


@pytest.fixture()
def admin_fakes():
    return {
        "admin_repo": FakeAdminRepository(),
        "ai_keys": FakeAIKeysRepository(),
        "agent_logs": FakeAgentLogsRepository(),
    }


@pytest.fixture()
def admin_client(admin_fakes):
    def override_admin_repo() -> AdminRepository:
        return admin_fakes["admin_repo"]

    def override_ai_keys() -> FakeAIKeysRepository:
        return admin_fakes["ai_keys"]

    def override_agent_logs() -> FakeAgentLogsRepository:
        return admin_fakes["agent_logs"]

    def override_ops_service() -> OpsStateService:
        return OpsStateService(repo=admin_fakes["admin_repo"])

    def override_sentinel_service() -> SentinelService:
        return SentinelService(
            repo=admin_fakes["admin_repo"],
            ai_keys=admin_fakes["ai_keys"],
            logs=admin_fakes["agent_logs"],
            ops=OpsStateService(repo=admin_fakes["admin_repo"]),
        )

    class FakeAdminUsersService:
        async def list_users(self):
            return [
                {
                    "id": "admin-user",
                    "email": "admin@example.com",
                    "created_at": "2024-01-01T00:00:00Z",
                    "confirmed": True,
                    "banned_until": None,
                    "admin": True,
                    "last_sign_in_at": "2024-01-01T00:00:00Z",
                },
                {
                    "id": "regular-user",
                    "email": "user@example.com",
                    "created_at": "2024-01-01T00:00:00Z",
                    "confirmed": True,
                    "banned_until": None,
                    "admin": False,
                    "last_sign_in_at": "2024-01-01T00:00:00Z",
                },
            ]

        async def set_identity(self, user_id, *, email=None, new_password=None):
            payload = {}
            if email:
                payload["email"] = email
            if new_password:
                payload["password"] = new_password
            return payload

        async def suspend(self, user_id, duration_minutes):
            pass

        async def reactivate(self, user_id):
            pass

    app.dependency_overrides[get_admin_repo] = override_admin_repo
    app.dependency_overrides[get_ops_service] = override_ops_service
    app.dependency_overrides[get_sentinel_service] = override_sentinel_service
    app.dependency_overrides[get_admin_users_service] = lambda: FakeAdminUsersService()
    app.dependency_overrides[auth_get_admin_users_service] = lambda: FakeAdminUsersService()
    app.dependency_overrides[require_admin] = _admin_user
    app.dependency_overrides[require_authenticated] = _authed_user

    yield TestClient(app)
    app.dependency_overrides.clear()


class TestAdminState:
    def test_get_state(self, admin_client):
        resp = admin_client.get("/api/v1/admin/state")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"
        assert "toggles" in data

    def test_set_state_admin(self, admin_client):
        resp = admin_client.post("/api/v1/admin/state", json={"status": "maintenance", "message": "Under maintenance"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "maintenance"
        assert data["message"] == "Under maintenance"

    def test_set_toggle(self, admin_client):
        resp = admin_client.post("/api/v1/admin/toggles/swarm", json={"enabled": False})
        assert resp.status_code == 200
        data = resp.json()
        assert data["toggles"]["swarm"] is False

    def test_set_toggle_invalid(self, admin_client):
        resp = admin_client.post("/api/v1/admin/toggles/invalid", json={"enabled": True})
        assert resp.status_code == 400


class TestAdminProviders:
    def test_provider_usage(self, admin_client, admin_fakes):
        admin_fakes["admin_repo"].provider_metrics["openrouter"] = {
            "provider": "openrouter",
            "status": "active",
            "message": "Healthy.",
            "model_count": 10,
            "tokens_used": 0,
            "balance_available": None,
            "checked_at": "2024-01-01T00:00:00Z",
        }
        resp = admin_client.get("/api/v1/admin/providers/usage")
        assert resp.status_code == 200
        data = resp.json()
        assert "providers" in data
        assert len(data["providers"]) > 0
        openrouter = next(p for p in data["providers"] if p["provider"] == "openrouter")
        assert openrouter["status"] == "active"
        assert openrouter["model_count"] == 10


class TestAdminSentinel:
    def test_sentinel_run(self, admin_client):
        resp = admin_client.post("/api/v1/admin/sentinel/run")
        assert resp.status_code == 200
        data = resp.json()
        assert "events_added" in data
        assert "discussion_added" in data

    def test_sentinel_snapshot(self, admin_client):
        resp = admin_client.get("/api/v1/admin/sentinel/snapshot")
        assert resp.status_code == 200
        data = resp.json()
        assert "running" in data
        assert "events" in data
        assert "discussion" in data

    def test_sentinel_events(self, admin_client, admin_fakes):
        admin_fakes["admin_repo"].events.append({
            "id": "1", "created_at": "2024-01-01T00:00:00Z", "status": "open",
            "title": "Test", "message": "msg", "severity": "error", "scope": "provider",
            "agent": "Sentinel", "suggested_fix": "fix", "auto_fix_report": ""
        })
        resp = admin_client.get("/api/v1/admin/sentinel/events")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test"

    def test_sentinel_discussion(self, admin_client, admin_fakes):
        admin_fakes["admin_repo"].discussion.append({
            "id": 1, "created_at": "2024-01-01T00:00:00Z", "agent": "Test", "message": "Hello"
        })
        resp = admin_client.get("/api/v1/admin/sentinel/discussion")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["message"] == "Hello"


class TestAdminUsers:
    def test_list_users(self, admin_client):
        resp = admin_client.get("/api/v1/admin/users")
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert len(data["users"]) == 2
        admin = next(u for u in data["users"] if u["admin"])
        assert admin["email"] == "admin@example.com"

    def test_suspend_user(self, admin_client):
        resp = admin_client.post("/api/v1/admin/users/regular-user/suspend", json={"duration_minutes": 60})
        assert resp.status_code == 200
        assert resp.json()["suspended"] is True

    def test_reactivate_user(self, admin_client):
        resp = admin_client.post("/api/v1/admin/users/regular-user/reactivate")
        assert resp.status_code == 200
        assert resp.json()["suspended"] is False

    def test_update_account(self, admin_client):
        resp = admin_client.post("/api/v1/admin/account", json={"email": "new@example.com", "new_password": "newpass123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "admin-user"
        assert "email changed" in data["message"]
        assert "password changed" in data["message"]