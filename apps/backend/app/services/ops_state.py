import time

from fastapi import Depends, HTTPException, status

from app.repositories.admin_repo import AdminRepository

CACHE_TTL_SECONDS = 2.0

MESSAGES = {
    "running": "",
    "maintenance": "The servers are under maintenance.",
    "shutdown": "The service has been shutdown.",
}


def get_ops_service() -> "OpsStateService":
    return OpsStateService()


def require_service(feature: str | None = None):
    """FastAPI dependency: rejects calls while the app is not running or a
    feature toggle is off (503 with the admin-facing message)."""

    async def _gate(ops: OpsStateService = Depends(get_ops_service)) -> None:
        await ops.ensure_available(feature)

    return _gate


class OpsStateService:
    """App operational state (running / maintenance / shutdown) and feature
    toggles, cached briefly so per-request reads stay cheap."""

    def __init__(self, repo: AdminRepository | None = None) -> None:
        self.repo = repo or AdminRepository()
        self._cache: tuple[float, dict] | None = None

    async def get_state(self) -> dict:
        now = time.time()
        if self._cache is not None and (now - self._cache[0]) < CACHE_TTL_SECONDS:
            return dict(self._cache[1])
        state = await self.repo.get_state()
        self._cache = (now, state)
        return dict(state)

    async def set_status(self, *, status: str, message: str = "") -> dict:
        self._cache = None
        final_message = message or MESSAGES.get(status, "")
        state = await self.repo.set_state(status=status, message=final_message)
        if state.get("message") == "" and status in MESSAGES:
            state["message"] = MESSAGES[status]
        self._cache = (time.time(), state)
        return state

    async def set_toggle(self, name: str, enabled: bool) -> dict:
        self._cache = None
        state = await self.repo.set_toggle(name, enabled)
        self._cache = (time.time(), state)
        return state

    async def ensure_available(self, feature: str | None = None) -> None:
        state = await self.get_state()
        if state.get("status") != "running":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=state.get("message") or MESSAGES.get(state.get("status"), "Service unavailable."),
            )
        if feature:
            toggles = state.get("toggles") or {}
            if toggles.get(feature, True) is False:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"The {feature.replace('_', ' ')} feature is currently disabled by the admin.",
                )