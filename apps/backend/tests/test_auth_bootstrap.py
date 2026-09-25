import asyncio
import json
from contextlib import contextmanager

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.v1.auth.route import get_bootstrap_service
from app.main import app
from app.services.auth_bootstrap import BootstrapError, BootstrapService


@contextmanager
def raises_bootstrap(status_code: int):
    with pytest.raises(BootstrapError) as exc_info:
        yield
    assert exc_info.value.status_code == status_code


class FakeSupabaseAdmin:
    def __init__(self, users: list[dict] | None = None) -> None:
        self.users = users or []
        self.creates: list[dict] = []
        self.updates: list[tuple[str, dict]] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and path.endswith("/admin/users"):
            return httpx.Response(200, json={"users": self.users})
        if request.method == "POST" and path.endswith("/admin/users"):
            body = json.loads(request.content or b"{}")
            self.creates.append(body)
            return httpx.Response(200, json={"id": "created-admin-id", "email": body["email"]})
        if request.method == "PUT" and "/admin/users/" in path:
            user_id = path.rsplit("/", 1)[-1]
            body = json.loads(request.content or b"{}")
            self.updates.append((user_id, body))
            return httpx.Response(200, json={"id": user_id})
        return httpx.Response(404, json={"msg": "not found"})


def make_service(fake: FakeSupabaseAdmin) -> BootstrapService:
    client = httpx.AsyncClient(transport=httpx.MockTransport(fake.handler))
    return BootstrapService(client=client)


def run(coro):
    return asyncio.run(coro)


def test_first_run_creates_admin():
    fake = FakeSupabaseAdmin()
    result = run(make_service(fake).bootstrap("admin@example.com", "S3curePassw0rd!", None, None))
    assert result["role"] == "admin"
    assert result["user_id"] == "created-admin-id"
    created = fake.creates[0]
    assert created["email"] == "admin@example.com"
    assert created["email_confirm"] is True
    assert created["app_metadata"]["role"] == "admin"


def test_existing_admin_blocks_bootstrap():
    existing = {"id": "existing", "email": "root@advancedcodegarage.dev", "app_metadata": {"role": "admin"}}
    service = make_service(FakeSupabaseAdmin(users=[existing]))
    with raises_bootstrap(409):
        run(service.bootstrap("other@example.com", "S3curePassw0rd!", None, None))


def test_adopts_existing_unconfirmed_user():
    fake = FakeSupabaseAdmin(
        users=[{"id": "stale-id", "email": "admin@example.com", "app_metadata": {"role": None}}]
    )
    result = run(make_service(fake).bootstrap("admin@example.com", "S3curePassw0rd!", "Admin", None))
    assert result["user_id"] == "stale-id"
    assert result["role"] == "admin"
    assert fake.updates[0][0] == "stale-id"
    assert fake.updates[0][1]["app_metadata"]["role"] == "admin"
    assert fake.updates[0][1]["email_confirm"] is True


def test_token_guard(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        "app.services.auth_bootstrap.get_settings",
        lambda: SimpleNamespace(
            supabase_url="http://sb",
            supabase_service_role_key="key",
            app_bootstrap_token="boot-token",
        ),
    )
    service = make_service(FakeSupabaseAdmin())
    with raises_bootstrap(401):
        run(service.bootstrap("a@b.com", "S3curePassw0rd!", None, token="wrong"))
    result = run(service.bootstrap("a@b.com", "S3curePassw0rd!", None, token="boot-token"))
    assert result["role"] == "admin"


def test_missing_service_role_key_is_config_error(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        "app.services.auth_bootstrap.get_settings",
        lambda: SimpleNamespace(supabase_url="http://sb", supabase_service_role_key="", app_bootstrap_token=""),
    )
    with raises_bootstrap(503):
        run(make_service(FakeSupabaseAdmin()).bootstrap("a@b.com", "S3curePassw0rd!", None, None))


def test_api_bootstrap_route_with_mocked_backend():
    fake = FakeSupabaseAdmin()
    client = TestClient(app)
    app.dependency_overrides[get_bootstrap_service] = lambda: make_service(fake)
    try:
        response = client.post(
            "/api/v1/auth/bootstrap",
            json={"email": "admin@example.com", "password": "S3curePassw0rd!", "name": "Admin"},
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "admin"
    assert payload["user_id"] == "created-admin-id"


def test_api_bootstrap_validation_errors():
    client = TestClient(app)
    app.dependency_overrides[get_bootstrap_service] = lambda: make_service(FakeSupabaseAdmin())
    try:
        bad_email = client.post(
            "/api/v1/auth/bootstrap", json={"email": "not-an-email", "password": "S3curePassw0rd!"}
        )
        short_pass = client.post(
            "/api/v1/auth/bootstrap", json={"email": "admin@example.com", "password": "short"}
        )
    finally:
        app.dependency_overrides.clear()
    assert bad_email.status_code == 422
    assert short_pass.status_code == 422