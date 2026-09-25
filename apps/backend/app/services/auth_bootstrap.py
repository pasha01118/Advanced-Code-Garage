import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

ADMIN_ROLE = "admin"


class BootstrapError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BootstrapService:
    """App-level admin bootstrap.

    Creates the platform's admin account directly in Supabase with
    ``email_confirm`` so it works without a confirmation email (no SMTP
    required). It only succeeds while no admin exists yet (first-run
    bootstrap); afterwards it refuses, since membership is e-mail confirmed
    via a future server-side integration.
    """

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    def _settings(self):
        return get_settings()

    def _new_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=20.0)

    @property
    def _admin_api(self) -> str:
        return f"{self._settings().supabase_url.rstrip('/')}/auth/v1/admin"

    def _headers(self) -> dict:
        settings = self._settings()
        key = settings.supabase_service_role_key
        if not key:
            raise BootstrapError(
                "Admin bootstrap requires SUPABASE_SERVICE_ROLE_KEY.", status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    async def _list_users(self) -> list[dict]:
        client = self._new_client()
        try:
            response = await client.get(f"{self._admin_api}/users", headers=self._headers())
        finally:
            if self._client is None:
                await client.aclose()
        if response.status_code >= 300:
            raise BootstrapError(
                f"Supabase user lookup failed ({response.status_code}).", status.HTTP_502_BAD_GATEWAY
            )
        return response.json().get("users", [])

    async def _create_user(self, email: str, password: str, name: str | None) -> dict:
        payload = {
            "email": email,
            "password": password,
            "email_confirm": True,
            "app_metadata": {"role": ADMIN_ROLE},
            "user_metadata": {"name": name or ""},
        }
        client = self._new_client()
        try:
            response = await client.post(f"{self._admin_api}/users", headers=self._headers(), json=payload)
        finally:
            if self._client is None:
                await client.aclose()
        return response

    async def _adopt_existing_user(self, user_id: str) -> None:
        payload = {
            "app_metadata": {"role": ADMIN_ROLE},
            "email_confirm": True,
        }
        client = self._new_client()
        try:
            response = await client.put(
                f"{self._admin_api}/users/{user_id}", headers=self._headers(), json=payload
            )
        finally:
            if self._client is None:
                await client.aclose()
        if response.status_code >= 300:
            raise BootstrapError(
                f"Could not upgrade existing user '{user_id}' to admin ({response.status_code}).",
                status.HTTP_502_BAD_GATEWAY,
            )

    @staticmethod
    def _user_is_admin(user: dict) -> bool:
        app_metadata = user.get("app_metadata") or {}
        return app_metadata.get("role") == ADMIN_ROLE

    async def bootstrap(self, email: str, password: str, name: str | None, token: str | None) -> dict:
        settings = self._settings()

        expected = settings.app_bootstrap_token
        if expected and token != expected:
            raise BootstrapError(
                "Invalid bootstrap token. APP_BOOTSTRAP_TOKEN is configured.", status.HTTP_401_UNAUTHORIZED
            )

        users = await self._list_users()
        existing_admin = next((u for u in users if self._user_is_admin(u)), None)
        if existing_admin is not None:
            raise BootstrapError(
                "Admin already bootstrapped. Sign in with the existing account instead.",
                status.HTTP_409_CONFLICT,
            )

        if any(u.get("email", "").lower() == email.lower() for u in users):
            target = next(u for u in users if u.get("email", "").lower() == email.lower())
            await self._adopt_existing_user(target["id"])
            return {
                "user_id": target["id"],
                "email": email,
                "role": ADMIN_ROLE,
                "message": "Existing account upgraded to ADMIN (email confirmation bypassed).",
            }

        response = await self._create_user(email, password, name)
        if response.status_code >= 300:
            raise BootstrapError(
                f"Admin account creation failed ({response.status_code}).",
                status.HTTP_400_BAD_REQUEST,
            )
        created = response.json()
        return {
            "user_id": created.get("id"),
            "email": email,
            "role": ADMIN_ROLE,
            "message": "Admin account created (confirmation email bypassed).",
        }