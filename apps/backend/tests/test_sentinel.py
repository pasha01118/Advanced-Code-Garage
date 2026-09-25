import pytest

from app.services.ops_state import OpsStateService
from app.services.sentinel import SentinelService, PROVIDER_SUGGESTIONS

from tests.fakes import (
    FakeAdminRepository,
    FakeAIKeysRepository,
    FakeAgentLogsRepository,
)


@pytest.fixture()
def sentinel_fakes():
    return {
        "admin_repo": FakeAdminRepository(),
        "ai_keys": FakeAIKeysRepository(),
        "agent_logs": FakeAgentLogsRepository(),
    }


@pytest.fixture()
def sentinel_service(sentinel_fakes):
    return SentinelService(
        repo=sentinel_fakes["admin_repo"],
        ai_keys=sentinel_fakes["ai_keys"],
        logs=sentinel_fakes["agent_logs"],
        ops=OpsStateService(repo=sentinel_fakes["admin_repo"]),
    )


class TestSentinelService:
    @pytest.mark.asyncio
    async def test_scan_providers_healthy(self, sentinel_service, sentinel_fakes):
        sentinel_fakes["ai_keys"].rows[("owner1", "openrouter")] = {
            "owner_id": "owner1", "provider": "openrouter", "status": "active", "model_count": 5
        }
        result = await sentinel_service.run_cycle()
        assert result["events_added"] == 0
        metrics = await sentinel_fakes["admin_repo"].list_provider_metrics()
        openrouter = next(m for m in metrics if m["provider"] == "openrouter")
        assert openrouter["status"] == "active"

    @pytest.mark.asyncio
    async def test_scan_providers_quota(self, sentinel_service, sentinel_fakes):
        sentinel_fakes["ai_keys"].rows[("owner1", "google")] = {
            "owner_id": "owner1", "provider": "google", "status": "quota", "model_count": 3
        }
        result = await sentinel_service.run_cycle()
        assert result["events_added"] >= 1
        events = await sentinel_fakes["admin_repo"].list_events()
        quota_events = [e for e in events if e["status"] == "open" and "quota" in e["suggested_fix"].lower()]
        assert len(quota_events) >= 1
        assert "quota" in quota_events[0]["suggested_fix"].lower()

    @pytest.mark.asyncio
    async def test_scan_providers_error(self, sentinel_service, sentinel_fakes):
        sentinel_fakes["ai_keys"].rows[("owner1", "ollama")] = {
            "owner_id": "owner1", "provider": "ollama", "status": "error", "model_count": 0
        }
        result = await sentinel_service.run_cycle()
        assert result["events_added"] >= 1
        events = await sentinel_fakes["admin_repo"].list_events()
        error_events = [e for e in events if e["status"] == "open" and "rejected" in e["suggested_fix"].lower()]
        assert len(error_events) >= 1

    @pytest.mark.asyncio
    async def test_scan_logs_errors(self, sentinel_service, sentinel_fakes):
        await sentinel_fakes["agent_logs"].add("error", "TestAgent", "Something failed")
        await sentinel_fakes["agent_logs"].add("info", "TestAgent", "Normal log")
        result = await sentinel_service.run_cycle()
        assert result["events_added"] >= 1
        events = await sentinel_fakes["admin_repo"].list_events()
        log_events = [e for e in events if "log" in e["title"].lower()]
        assert len(log_events) >= 1

    @pytest.mark.asyncio
    async def test_auto_heal_flush_cache(self, sentinel_service, sentinel_fakes):
        event = await sentinel_fakes["admin_repo"].insert_event({
            "severity": "warn", "scope": "system", "agent": "Test",
            "title": "Cache issue", "message": "Stale cache",
            "status": "open", "suggested_fix": "flush_cache", "auto_fix_report": ""
        })
        result = await sentinel_service.run_cycle()
        assert result["discussion_added"] >= 1
        events = await sentinel_fakes["admin_repo"].list_events()
        healed = [e for e in events if e["id"] == event["id"] and e["status"] == "auto_fixed"]
        assert len(healed) == 1
        assert "flushed" in healed[0]["auto_fix_report"].lower()

    @pytest.mark.asyncio
    async def test_discussion_composed(self, sentinel_service, sentinel_fakes):
        sentinel_fakes["ai_keys"].rows[("owner1", "google")] = {
            "owner_id": "owner1", "provider": "google", "status": "quota", "model_count": 3
        }
        result = await sentinel_service.run_cycle()
        assert result["discussion_added"] >= 1
        discussion = await sentinel_fakes["admin_repo"].list_discussion()
        assert len(discussion) >= 1
        agents = {d["agent"] for d in discussion}
        assert "Mr. Arman Ali Khan" in agents
        assert "Mr. Sadath Ali Khan" in agents
        assert "Git-Sir" in agents


class TestProviderSuggestions:
    def test_suggestions_exist(self):
        assert PROVIDER_SUGGESTIONS["active"] == "Healthy — no action needed."
        assert "Replace" in PROVIDER_SUGGESTIONS["quota"]
        assert "Replace" in PROVIDER_SUGGESTIONS["error"]
        assert "Not configured" in PROVIDER_SUGGESTIONS["untested"]