import hashlib
import hmac
import logging
import time
from typing import Any

import httpx
from fastapi import HTTPException, status
from jose import jwt

from app.core.config import get_settings
from app.repositories.github import GitHubRepository

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"


class GitHubNotConfigured(RuntimeError):
    pass


class GitHubAppService:
    """GitHub App installation sync and verified webhook ingestion.

    Installation tokens are minted on demand from the App private key; no long
    lived personal access token is ever stored in the database or browser.
    """

    def __init__(self, repo: GitHubRepository | None = None) -> None:
        self.repo = repo or GitHubRepository()

    @property
    def settings(self):
        return get_settings()

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

    async def sync_installation(self, installation_id: int) -> dict:
        app_jwt = await self._app_jwt()
        headers = {
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        async with httpx.AsyncClient(base_url=GITHUB_API, timeout=20.0) as client:
            token_response = await client.post(
                f"/app/installations/{installation_id}/access_tokens", headers=headers
            )
            if token_response.status_code == 404:
                raise HTTPException(status_code=404, detail="GitHub installation not found")
            token_response.raise_for_status()
            token = token_response.json()["token"]

            repos_response = await client.get(
                "/installation/repositories",
                params={"per_page": 100},
                headers={
                    **headers,
                    "Authorization": f"Bearer {token}",
                },
            )
            repos_response.raise_for_status()
            repos = repos_response.json().get("repositories", [])

        added = 0
        updated = 0
        for repo in repos:
            existing = await self.repo.get_repository_by_external_id(
                installation_id, int(repo["id"])
            )
            await self.repo.upsert_repository(installation_id, repo)
            if existing:
                updated += 1
            else:
                added += 1
        return {
            "installation_id": installation_id,
            "repositories_added": added,
            "repositories_updated": updated,
            "total": len(repos),
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
