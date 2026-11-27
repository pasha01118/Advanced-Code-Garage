import hashlib
import hmac
import logging
import time
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import HTTPException, status
from jose import jwt

from app.core.config import get_settings
from app.repositories.github import GitHubRepository

logger = logging.getLogger(__name__)

GITHUB_API_VERSION = "2022-11-28"
# Leave a safety margin so a token is never used in its final seconds.
TOKEN_EXPIRY_MARGIN_SECONDS = 60


class GitHubNotConfigured(RuntimeError):
    pass


class GitHubAppService:
    """GitHub App client: installation sync, webhook ingestion and a shared
    request helper for repository operations.

    Installation tokens are minted on demand from the App private key; no long
    lived personal access token is ever stored in the database or browser.
    """

    def __init__(self, repo: GitHubRepository | None = None) -> None:
        self.repo = repo or GitHubRepository()
        self._tokens: dict[int, tuple[str, float]] = {}

    @property
    def settings(self):
        return get_settings()

    @property
    def api_base(self) -> str:
        return self.settings.github_api_base_url.rstrip("/")

    def webhook_is_configured(self) -> bool:
        return bool(self.settings.github_app_webhook_secret)

    def verify_webhook(self, body: bytes, signature: str | None) -> bool:
        secret = self.settings.github_app_webhook_secret
        if not secret or not signature:
            return False
        expected = "sha256=" + hmac.new(
            secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    async def _app_jwt(self) -> str:
        settings = self.settings
        if not settings.github_app_id or not settings.github_app_private_key:
            raise GitHubNotConfigured("GitHub App is not configured")
        now = int(time.time())
        key = settings.github_app_private_key.replace("\\n", "\n")
        return jwt.encode(
            {"iat": now - 60, "exp": now + 540, "iss": settings.github_app_id},
            key,
            algorithm="RS256",
        )

    @staticmethod
    def path_segment(value: str) -> str:
        """Quote a single path segment without allowing it to alter the path."""
        return quote(str(value), safe="")

    async def get_installation_token(self, installation_id: int) -> str:
        cached = self._tokens.get(installation_id)
        if cached and cached[1] > time.time() + TOKEN_EXPIRY_MARGIN_SECONDS:
            return cached[0]
        app_jwt = await self._app_jwt()
        async with httpx.AsyncClient(base_url=self.api_base, timeout=20.0) as client:
            response = await client.post(
                f"/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {app_jwt}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": GITHUB_API_VERSION,
                },
            )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub installation not found")
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail="Could not obtain an installation token")
        payload = response.json()
        token = str(payload["token"])
        expires_at = time.time() + max(60, int(payload.get("expires_in", 3600)))
        self._tokens[installation_id] = (token, expires_at)
        return token

    async def request(
        self,
        installation_id: int,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> Any:
        """Call the GitHub API with a short-lived installation token.

        Returns parsed JSON (or {} for empty responses). A single 401 retry
        covers races with token expiry. Errors are sanitised: tokens and raw
        upstream response bodies are never returned to the client.
        """
        for attempt in range(2):
            token = await self.get_installation_token(installation_id)
            async with httpx.AsyncClient(base_url=self.api_base, timeout=30.0) as client:
                response = await client.request(
                    method,
                    path,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": GITHUB_API_VERSION,
                    },
                    params=params,
                    json=json_body,
                )
            if response.status_code == 401 and attempt == 0:
                self._tokens.pop(installation_id, None)
                continue
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="GitHub resource not found")
            if response.status_code == 422:
                raise HTTPException(
                    status_code=422, detail="GitHub rejected this change (422)"
                )
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=502, detail=f"GitHub request failed ({response.status_code})"
                )
            if not response.content:
                return {}
            try:
                return response.json()
            except ValueError:
                return {}
        raise HTTPException(status_code=502, detail="GitHub request failed")

    async def sync_installation(self, installation_id: int, actor: str | None = None) -> dict:
        repos = await self.request(
            installation_id, "GET", "/installation/repositories", params={"per_page": 100}
        )
        repositories = repos.get("repositories", []) if isinstance(repos, dict) else []

        added = 0
        updated = 0
        for repo in repositories:
            existing = await self.repo.get_repository_by_external_id(
                installation_id, int(repo["id"])
            )
            row = await self.repo.upsert_repository(installation_id, repo)
            if actor:
                await self.repo.grant_permission(
                    str(row.get("id") or ""), actor, "owner", actor
                )
            if existing:
                updated += 1
            else:
                added += 1
        return {
            "installation_id": installation_id,
            "repositories_added": added,
            "repositories_updated": updated,
            "total": len(repositories),
        }

    async def handle_webhook(self, payload: dict, event: str, delivery_id: str = "") -> None:
        installation = payload.get("installation") or {}
        installation_id = installation.get("id")
        account = installation.get("account") or {}
        if installation_id and account.get("login"):
            await self.repo.upsert_installation(
                int(installation_id),
                str(account["login"]),
                account_type=str(account.get("type") or ""),
                suspended=bool(installation.get("suspended", False)),
            )

        repositories: list[dict] = []
        if event == "installation_repositories":
            repositories = payload.get("repositories_added") or []
        elif payload.get("repository"):
            repositories = [payload["repository"]]

        for repo in repositories:
            if installation_id and repo.get("id"):
                await self.repo.upsert_repository(int(installation_id), repo)

        repo_full_name = (payload.get("repository") or {}).get("full_name") or ""
        if delivery_id and not await self.repo.has_delivery(delivery_id):
            try:
                await self.repo.record_webhook(
                    delivery_id,
                    event,
                    str(payload.get("action") or ""),
                    int(installation_id) if installation_id else None,
                    repo_full_name,
                    payload,
                )
            except Exception:
                # A duplicate delivery can race another instance; that is safe.
                logger.debug("Duplicate GitHub webhook delivery", exc_info=True)


def get_github_app_service() -> GitHubAppService:
    return GitHubAppService()
