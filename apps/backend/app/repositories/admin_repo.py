from datetime import datetime, timezone

from app.repositories.base import SupabaseRepository

STATE_TABLENAME = "app_state"
METRICS_TABLENAME = "provider_metrics"
EVENTS_TABLENAME = "sentinel_events"
DISCUSSION_TABLENAME = "sentinel_discussion"

DEFAULT_TOGGLES: dict[str, bool] = {
    "swarm": True,
    "git_ops": True,
    "deployments": True,
    "ai_routing": True,
    "sentinel": True,
    "signups": True,
    "telemetry": True,
}


class AdminRepository(SupabaseRepository):
    """Operational state, feature toggles, provider usage metrics, and the
    Sentinel (self-healing) event/discussion store."""

    # -- app state -----------------------------------------------------------

    async def get_state(self) -> dict:
        res = await self._run(
            self.db.table(STATE_TABLENAME).select("*").eq("id", 1).limit(1).execute
        )
        row = self._row(res)
        if row is None:
            return {
                "id": 1,
                "status": "running",
                "message": "",
                "toggles": dict(DEFAULT_TOGGLES),
                # Signals "no persisted row yet" to conditional writers.
                "updated_at": None,
            }
        toggles = {**DEFAULT_TOGGLES, **(row.get("toggles") or {})}
        row["toggles"] = toggles
        row.pop("id", None)
        return row

    async def set_state(self, *, status: str, message: str = "") -> dict:
        payload = {
            "status": status,
            "message": message,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        # Upsert: an environment without the seeded row must not silently
        # discard an admin's state change.
        await self._run(
            self.db.table(STATE_TABLENAME)
            .upsert({"id": 1, **payload}, on_conflict="id")
            .execute
        )
        return await self.get_state()

    async def set_toggle(self, name: str, enabled: bool) -> dict:
        # Optimistic concurrency control: without the updated_at predicate two
        # admins toggling at once silently overwrite each other's change.
        for _ in range(3):
            current = await self.get_state()
            toggles = dict(current["toggles"])
            toggles[name] = enabled
            payload = {
                "toggles": toggles,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            previous = current.get("updated_at")
            if not previous:
                # No persisted row: seed it now rather than no-oping forever.
                await self._run(
                    self.db.table(STATE_TABLENAME)
                    .upsert({"id": 1, **payload}, on_conflict="id")
                    .execute
                )
                return await self.get_state()
            query = (
                self.db.table(STATE_TABLENAME)
                .update(payload)
                .eq("id", 1)
                .eq("updated_at", previous)
            )
            res = await self._run(query.execute)
            row = self._row(res)
            if row is not None:
                return self._normalise(row)
        raise RuntimeError("Concurrent admin-toggle update; please retry")

    @staticmethod
    def _normalise(row: dict) -> dict:
        toggles = {**DEFAULT_TOGGLES, **(row.get("toggles") or {})}
        row = dict(row)
        row["toggles"] = toggles
        row.pop("id", None)
        return row

    # -- provider metrics ----------------------------------------------------

    async def upsert_provider_metrics(
        self,
        *,
        provider: str,
        status: str,
        message: str = "",
        model_count: int = 0,
        tokens_used: int = 0,
        balance_available: float | None = None,
    ) -> None:
        payload = {
            "provider": provider,
            "status": status,
            "message": message,
            "model_count": model_count,
            "tokens_used": tokens_used,
            "balance_available": balance_available,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._run(
            self.db.table(METRICS_TABLENAME).upsert(payload, on_conflict="provider").execute
        )

    async def list_provider_metrics(self) -> list[dict]:
        res = await self._run(
            self.db.table(METRICS_TABLENAME).select("*").order("provider").execute
        )
        return res.data or []

    # -- sentinel events -----------------------------------------------------

    async def insert_event(self, event: dict) -> dict | None:
        res = await self._run(self.db.table(EVENTS_TABLENAME).insert(event).execute)
        return self._row(res)

    async def list_events(self, limit: int = 100) -> list[dict]:
        res = await self._run(
            self.db.table(EVENTS_TABLENAME)
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute
        )
        return res.data or []

    async def mark_event(self, event_id: str, *, status: str, report: str = "") -> None:
        await self._run(
            self.db.table(EVENTS_TABLENAME)
            .update(
                {
                    "status": status,
                    "auto_fix_report": report,
                    "resolved_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", event_id)
            .execute
        )

    # -- sentinel discussion -------------------------------------------------

    async def append_discussion(self, *, agent: str, message: str) -> dict | None:
        res = await self._run(
            self.db.table(DISCUSSION_TABLENAME)
            .insert({"agent": agent, "message": message})
            .execute
        )
        return self._row(res)

    async def list_discussion(self, limit: int = 100) -> list[dict]:
        res = await self._run(
            self.db.table(DISCUSSION_TABLENAME)
            .select("*")
            .order("id", desc=True)
            .limit(limit)
            .execute
        )
        return list(reversed(res.data or []))