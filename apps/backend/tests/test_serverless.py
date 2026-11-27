from fastapi.testclient import TestClient

from app import main as main_module
from app.core.config import Settings
from app.main import app


class _Sentinel:
    def __init__(self):
        self.calls = 0

    async def run_cycle(self):
        self.calls += 1
        return {"events_added": 2, "discussion_added": 1}


def test_is_serverless_detects_vercel(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    assert Settings().is_serverless is False

    monkeypatch.setenv("VERCEL", "1")
    assert Settings().is_serverless is True


def test_cron_requires_configured_secret(monkeypatch):
    monkeypatch.setattr(main_module.settings, "cron_secret", "")
    resp = TestClient(app).get("/api/cron/sentinel")
    assert resp.status_code == 503


def test_cron_rejects_wrong_token(monkeypatch):
    monkeypatch.setattr(main_module.settings, "cron_secret", "correct-secret")
    client = TestClient(app)
    assert client.get("/api/cron/sentinel").status_code == 401
    assert (
        client.get(
            "/api/cron/sentinel", headers={"Authorization": "Bearer wrong-secret"}
        ).status_code
        == 401
    )


def test_cron_runs_one_cycle_with_valid_token(monkeypatch):
    sentinel = _Sentinel()
    monkeypatch.setattr(main_module.settings, "cron_secret", "correct-secret")
    monkeypatch.setattr(main_module, "get_sentinel_service", lambda: sentinel)

    resp = TestClient(app).get(
        "/api/cron/sentinel", headers={"Authorization": "Bearer correct-secret"}
    )
    assert resp.status_code == 200
    assert resp.json() == {
        "status": "ok",
        "events_added": 2,
        "discussion_added": 1,
    }
    assert sentinel.calls == 1
