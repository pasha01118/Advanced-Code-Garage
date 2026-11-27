"""Regression tests for the auth/authz gaps found in review."""

import asyncio
import re

import httpx
import pytest

from app.core.config import get_settings
from app.services.ai_integration import AIIntegrationService, SessionModelCache
from tests.fakes import FakeAIKeysRepository


def test_projects_are_owner_scoped(client, fakes):
    created = client.post(
        "/api/v1/projects/",
        json={"name": "Mine", "description": "owned by test-user"},
    )
    assert created.status_code == 200
    mine = created.json()["id"]

    other = asyncio.run(fakes["projects"].create("Theirs", owner_id="someone-else"))

    response = client.get(f"/api/v1/projects/{other['id']}")
    assert response.status_code == 404

    listing = client.get("/api/v1/projects/")
    assert listing.status_code == 200
    ids = [p["id"] for p in listing.json()["projects"]]
    assert mine in ids
    assert other["id"] not in ids


def test_log_stream_requires_auth(bare_client):
    assert bare_client.get("/api/v1/logs/stream").status_code == 401


def test_admin_state_requires_auth(bare_client):
    assert bare_client.get("/api/v1/admin/state").status_code == 401


def test_auth_me_exposes_backend_admin_decision(client, monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        "app.core.auth.get_settings",
        lambda: SimpleNamespace(admin_user_ids="test-user"),
    )
    assert client.get("/api/v1/auth/me").json()["is_admin"] is True

    monkeypatch.setattr(
        "app.core.auth.get_settings",
        lambda: SimpleNamespace(admin_user_ids=""),
    )
    assert client.get("/api/v1/auth/me").json()["is_admin"] is False


def test_cors_regex_is_anchored():
    pattern = re.compile(get_settings().frontend_origin_regex)
    assert pattern.match("https://preview-1.vercel.app")
    assert not pattern.match("https://preview.vercel.app.attacker.tld")


@pytest.mark.asyncio
async def test_failed_validation_is_not_cached(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "bad key"})

    monkeypatch.setattr(
        "app.services.ai_integration.httpx.AsyncClient",
        lambda *a, **kw: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    service = AIIntegrationService(repo=FakeAIKeysRepository())
    result = await service.save_and_validate("u1", "groq", "bad-key", None)
    assert result.status == "error"
    assert SessionModelCache.get("u1:groq") is None
