"""Route-level feature toggle enforcement (503 when a toggle is off)."""

import pytest

from app.core.auth import require_admin
from app.main import app


def _set_toggle(fakes, name: str) -> None:
    fakes["admin"].state["toggles"][name] = False


@pytest.mark.parametrize(
    ("toggle", "method", "path", "body"),
    [
        ("swarm", "post", "/api/v1/projects/", {"name": "Disabled"}),
        ("ai_routing", "get", "/api/v1/ai/keys", None),
        ("telemetry", "get", "/api/v1/logs/", None),
        (
            "signups",
            "post",
            "/api/v1/auth/bootstrap",
            {"email": "admin@example.com", "password": "password123"},
        ),
    ],
)
def test_toggle_disables_its_routes(client, fakes, toggle, method, path, body):
    _set_toggle(fakes, toggle)
    res = getattr(client, method)(path, json=body) if body else getattr(client, method)(path)
    assert res.status_code == 503
    assert toggle.replace("_", " ") in res.json()["detail"]


def test_sentinel_toggle_disables_sentinel_admin_routes(client, fakes):
    _set_toggle(fakes, "sentinel")
    app.dependency_overrides[require_admin] = lambda: {
        "sub": "admin-user",
        "role": "authenticated",
        "email": "admin@example.com",
        "app_metadata": {"role": "admin"},
    }
    res = client.get("/api/v1/admin/sentinel/events")
    assert res.status_code == 503
    assert "sentinel" in res.json()["detail"]


def test_reserved_toggles_do_not_disable_routes(client, fakes):
    _set_toggle(fakes, "git_ops")
    _set_toggle(fakes, "deployments")
    res = client.get("/api/v1/ai/catalog")
    assert res.status_code == 200
