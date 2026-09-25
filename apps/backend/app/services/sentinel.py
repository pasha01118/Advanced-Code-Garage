from datetime import datetime, timezone

from app.core.event_bus import EventBus
from app.repositories.admin_repo import AdminRepository
from app.repositories.agent_logs import AgentLogsRepository
from app.repositories.ai_keys import AIKeysRepository
from app.services.ai_catalog import list_catalog
from app.services.ai_integration import SessionModelCache
from app.services.ops_state import OpsStateService

sentinel_bus = EventBus()

PROVIDER_SUGGESTIONS = {
    "active": "Healthy — no action needed.",
    "quota": "Replace — quota exhausted. Switch provider or plan.",
    "error": "Replace — key rejected by the provider.",
    "untested": "Not configured — add a key to enable.",
}


class SentinelService:
    """Sentinel self-healing system.

    Runs real checks (provider key health, error-log scan, operational state),
    has its AI engineer personas analyse the findings into an auditable
    discussion thread, applies safe automatic fixes, and streams a live
    telemetry feed over the sentinel event bus.
    """

    def __init__(
        self,
        repo: AdminRepository | None = None,
        ops: OpsStateService | None = None,
        ai_keys: AIKeysRepository | None = None,
        logs: AgentLogsRepository | None = None,
        bus: EventBus | None = None,
    ) -> None:
        self.repo = repo or AdminRepository()
        self.ops = ops or OpsStateService()
        self.ai_keys = ai_keys or AIKeysRepository()
        self.logs = logs or AgentLogsRepository()
        self.bus = bus or sentinel_bus
        self.running = False
        self.last_run_at: datetime | None = None

    async def _open_titles(self) -> set[str]:
        events = await self.repo.list_events(limit=200)
        return {e["title"] for e in events if e.get("status") == "open"}

    async def run_cycle(self) -> dict:
        self.running = True
        self.last_run_at = datetime.now(timezone.utc)
        try:
            state = await self.ops.get_state()
            findings = await self._scan_providers() + await self._scan_logs()
            added = 0
            open_titles = await self._open_titles()
            for event in findings:
                if event["title"] in open_titles:
                    continue
                try:
                    await self.repo.insert_event(event)
                    added += 1
                except Exception:
                    continue
                await self.bus.publish({"type": "event", "data": event})

            healed = await self._heal(state)
            discussion = self._compose_discussion(findings, healed, state)
            for agent, message in discussion:
                row = await self.repo.append_discussion(agent=agent, message=message)
                if row:
                    await self.bus.publish({"type": "discussion", "data": row})
            return {"events_added": added, "discussion_added": len(discussion)}
        finally:
            self.running = False

    async def _scan_providers(self) -> list[dict]:
        catalog_ids = {p["id"] for p in list_catalog()}
        aggregates = {a["provider"]: a for a in await self.ai_keys.aggregate_providers()}
        findings: list[dict] = []
        for provider in sorted(catalog_ids):
            agg = aggregates.get(provider) or {
                "provider": provider, "configured": 0, "active": 0, "error": 0,
                "quota": 0, "models": 0, "messages": [],
            }
            if agg["configured"] == 0:
                status_label, message = "untested", "Not configured by any user."
            elif agg["active"] > 0:
                status_label, message = "active", "Healthy."
            elif agg["quota"] > 0:
                status_label, message = "quota", "Quota exhausted for connected keys."
            else:
                status_label, message = "error", "Connected keys are failing."
            await self.repo.upsert_provider_metrics(
                provider=provider,
                status=status_label,
                message=message,
                model_count=agg["models"],
                tokens_used=0,
                balance_available=None,
            )
            if status_label in ("error", "quota"):
                findings.append(
                    {
                        "severity": "error" if status_label == "error" else "warn",
                        "scope": "provider",
                        "agent": "Sentinel-Scan",
                        "title": f"Provider {provider} needs attention",
                        "message": f"{provider}: {message}",
                        "status": "open",
                        "suggested_fix": PROVIDER_SUGGESTIONS[status_label],
                        "auto_fix_report": "",
                    }
                )
        return findings

    async def _scan_logs(self) -> list[dict]:
        recent = await self.logs.recent(limit=100)
        errors = [entry for entry in recent if (entry.get("level") or "").lower() == "error"]
        if not errors:
            return []
        samples = "; ".join((e.get("message") or "")[:80] for e in errors[:3])
        return [
            {
                "severity": "warn",
                "scope": "system",
                "agent": "Sadath-Audit",
                "title": f"{len(errors)} error(s) in recent agent logs",
                "message": f"Latest samples: {samples}",
                "status": "open",
                "suggested_fix": "flush_cache",
                "auto_fix_report": "",
            }
        ]

    async def _heal(self, state: dict) -> list[dict]:
        healed: list[dict] = []
        events = await self.repo.list_events(limit=200)
        for event in events:
            if event.get("status") != "open":
                continue
            fix = event.get("suggested_fix") or ""
            report = ""
            if fix == "flush_cache":
                SessionModelCache.clear()
                report = "Sentinel flushed the stale model cache (safe auto-fix)."
            if report:
                await self.repo.mark_event(event["id"], status="auto_fixed", report=report)
                healed.append({"id": event["id"], "title": event["title"], "report": report})
                await self.bus.publish(
                    {"type": "heal", "data": {"id": event["id"], "title": event["title"], "report": report}}
                )
        return healed

    def _compose_discussion(self, findings: list[dict], healed: list[dict], state: dict) -> list[tuple[str, str]]:
        n_issues = len(findings)
        n_healed = len(healed)
        status_label = state.get("status", "running")
        messages: list[tuple[str, str]] = [
            (
                "Mr. Arman Ali Khan",
                f"Cycle complete: surveyed {len(list_catalog())} providers and recent agent logs. "
                f"{n_issues} issue(s) surfaced for analysis.",
            )
        ]
        if n_issues:
            messages.append(
                (
                    "Mr. Sadath Ali Khan",
                    f"Security gate review: {n_issues} finding(s) open. "
                    + " ".join(f"- {f['agent']}: {f['title']}" for f in findings[:4])
                    + " Recommended fixes logged; no destructive action auto-approved.",
                )
            )
        if n_healed:
            messages.append(
                (
                    "Git-Sir",
                    f"Self-healing executed {n_healed} safe fix(es): "
                    + "; ".join(h["title"] for h in healed)
                    + ". Reports appended.",
                )
            )
        messages.append(
            (
                "Git-Sir",
                f"Operational state is '{status_label}'. Sentinel idle, standing by for the next cycle.",
            )
        )
        return messages[:4]