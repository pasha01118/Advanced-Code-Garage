from urllib.parse import quote

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.services.auth_bootstrap import BootstrapService


class AdminUsersService:
    """Reads and updates Supabase auth users via the admin API (service role)."""

    def __init__(self, bootstrap: BootstrapService | None = None) -> None:
        self._bootstrap = bootstrap or BootstrapService()

    async def list_users(self) -> list[dict]:
        users = await self._bootstrap._list_users()
        rows = []
        for user in users:
            app_metadata = user.get("app_metadata") or {}
            rows.append(
                {
                    "id": user.get("id"),
                    "email": user.get("email", ""),
                    "created_at": user.get("created_at"),
                    "confirmed": user.get("email_confirmed_at") is not None,
                    "banned_until": user.get("banned_until"),
                    "admin": app_metadata.get("role") == "admin",
                    "last_sign_in_at": user.get("last_sign_in_at"),
                }
            )
        return rows

    async def _admin_request(self, method: str, path: str, payload: dict | None = None) -> dict:
        settings = get_settings()
        client = self._bootstrap._new_client()
        try:
            response = await client.request(
                method,
                f"{settings.supabase_url.rstrip('/')}/auth/v1/admin{path}",
                headers=self._bootstrap._headers(),
                json=payload,
            )
        finally:
            if self._bootstrap._client is None:
                await client.aclose()
        if response.status_code >= 300:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Supabase user update failed ({response.status_code}).",
            )
        return response.json()

    async def get_user(self, user_id: str) -> dict:
        """Fetch the current auth user so long-lived streams can re-check admin status."""
        return await self._admin_request("GET", self._user_path(user_id))

    @staticmethod
    def _user_path(user_id: str) -> str:
        if not user_id or "/" in user_id or "?" in user_id or "#" in user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id.")
        return f"/users/{quote(user_id, safe='')}"

    async def set_identity(self, user_id: str, *, email: str | None = None, new_password: str | None = None) -> dict:
        payload: dict = {}
        if email:
            payload = {"email": email, "email_confirm": True}
        if new_password:
            if payload:
                payload = {**payload, "password": new_password}
            else:
                payload = {"password": new_password}
        if not payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nothing to update.")
        await self._admin_request("PUT", self._user_path(user_id), payload)
        return payload

    async def suspend(self, user_id: str, duration_minutes: int) -> None:
        duration = f"{max(1, duration_minutes)}m"
        await self._admin_request("PUT", f"{self._user_path(user_id)}/ban", {"ban_duration": duration})

    async def reactivate(self, user_id: str) -> None:
        await self._admin_request("PUT", f"{self._user_path(user_id)}/unban", {})
