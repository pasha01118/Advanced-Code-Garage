"""AI Integration service: provider key lifecycle + live model discovery.

Key storage is server-side and encrypted (Fernet). When a key is saved, the
service immediately performs a cheap first upstream call - the provider's
`GET /models` (or `/api/tags` for Ollama) - both validating the key and
returning the live model list. Status is classified onto a 3-state LED signal:

  active (green)  - upstream 200, key accepted, models listed
  quota  (yellow) - upstream 429 / credits / rate-limit exhausted
  error  (red)    - key rejected, 5xx, timeout, or connection failure

Loose "session cache": model lists are held in-process for our instance and
refreshed on demand within 10 minutes.
"""

import asyncio
import ipaddress
import json
import logging
import socket
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx

from app.core.config import get_settings
from app.core.crypto import decrypt_secret, encrypt_secret
from app.repositories.ai_keys import AIKeysRepository
from app.schemas.ai import AIKeyStatus, AIKeyStatusListOut, AIModelInfo, AIModelListOut, AIValidateOut
from app.services.ai_catalog import get_catalog_entry

logger = logging.getLogger(__name__)

VALIDATION_TIMEOUT_SECONDS = 20.0
DNS_LOOKUP_TIMEOUT_SECONDS = 5.0
VALID_KEYS_FIELD = "key_ciphertext"

_TAG_MARKERS = (
    (":free", "free"),
    (":fr", "free"),
    ("/free", "free"),
    ("preview", "preview"),
    ("-latest", "latest"),
)


def _redact(text: str, secret: str | None) -> str:
    if secret:
        text = text.replace(secret, "***")
    return text


@dataclass(frozen=True)
class OllamaTarget:
    """A validated Ollama base URL plus the exact address to connect to."""

    original_url: str
    request_url: str
    headers: dict[str, str]
    extensions: dict[str, Any]


async def _resolve_host(host: str, port: int) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Resolve on the event loop with a deadline so the worker cannot stall."""
    infos = await asyncio.wait_for(
        asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM),
        timeout=DNS_LOOKUP_TIMEOUT_SECONDS,
    )
    return [ipaddress.ip_address(info[4][0]) for info in infos]


def _host_header(host: str, port: int | None) -> str:
    rendered = f"[{host}]" if ":" in host else host
    return f"{rendered}:{port}" if port else rendered


async def _safe_ollama_url(url: str) -> OllamaTarget:
    """Validate a user-supplied Ollama URL and pin the connection to the answer.

    The outbound request uses the validated IP literal, while the original
    hostname is preserved in the Host header and TLS SNI/certificate check.
    This prevents DNS rebinding between validation and connection.
    """
    parsed = urlparse(url)
    host = parsed.hostname
    if (
        parsed.scheme not in {"http", "https"}
        or not host
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Invalid Ollama base URL; use http(s)://host[:port]")

    lowered = host.lower()
    local_dev = lowered == "localhost" or lowered.endswith(".localhost")
    if local_dev and get_settings().is_production:
        raise ValueError("Loopback Ollama URLs are not allowed in production")

    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None

    if literal is not None:
        if not literal.is_global and not local_dev:
            raise ValueError("Private or reserved Ollama URLs are not allowed")
        resolved = [literal]
    else:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        try:
            resolved = await _resolve_host(host, port)
        except (asyncio.TimeoutError, OSError, ValueError) as exc:
            raise ValueError("Ollama hostname could not be resolved") from exc
        if not resolved:
            raise ValueError("Ollama hostname could not be resolved")
        if not local_dev and any(not ip.is_global for ip in resolved):
            raise ValueError("Ollama hostname resolves to a private or reserved address")
        literal = resolved[0]

    pinned = str(literal)
    if literal.version == 6:
        pinned = f"[{pinned}]"
    netloc = pinned + (f":{parsed.port}" if parsed.port else "")
    request_url = urlunparse((parsed.scheme, netloc, "", "", "", ""))
    return OllamaTarget(
        original_url=url.rstrip("/"),
        request_url=request_url,
        headers={"Host": _host_header(host, parsed.port)},
        extensions={"sni_hostname": host} if parsed.scheme == "https" else {},
    )


def _model_tags(model_id: str) -> list[str] | None:
    low = model_id.lower()
    tags: list[str] = []
    for marker, label in _TAG_MARKERS:
        if marker in low and label not in tags:
            tags.append(label)
    return tags or None


class SessionModelCache:
    """Per-process TTL cache keyed by `{owner}:{provider}`."""

    _store: dict[str, tuple[float, list[dict]]] = {}
    ttl_seconds: float = 600.0

    @classmethod
    def get(cls, key: str) -> list[dict] | None:
        hit = cls._store.get(key)
        if hit is None:
            return None
        fetched_at, models = hit
        if time.monotonic() - fetched_at > cls.ttl_seconds:
            cls._store.pop(key, None)
            return None
        return models

    @classmethod
    def set(cls, key: str, models: list[dict]) -> None:
        # Simple bounded store: expiry alone let deleted users/providers
        # accumulate entries for the life of the worker.
        if key not in cls._store and len(cls._store) >= 500:
            oldest = next(iter(cls._store))
            cls._store.pop(oldest, None)
        cls._store[key] = (time.monotonic(), models)

    @classmethod
    def pop(cls, key: str) -> None:
        cls._store.pop(key, None)

    @classmethod
    def clear(cls) -> None:
        cls._store.clear()


class AIIntegrationService:
    def __init__(self, repo: AIKeysRepository | None = None, settings=None) -> None:
        self.repo = repo or AIKeysRepository()
        self.settings = settings

    # -- HTTP -----------------------------------------------------------------

    @staticmethod
    def _endpoint(entry, api_key: str | None, base_url: str | None):
        if entry.kind == "google":
            return f"{entry.base_url}/models", {}, {"key": api_key}, {}
        return (
            f"{base_url.rstrip('/')}/{entry.models_path.lstrip('/')}",
            {"Authorization": f"Bearer {api_key}"},
            None,
            {},
        )

    @staticmethod
    def _brief(code: int, body: str, secret: str | None) -> str:
        snippet = ""
        try:
            data = json.loads(body)
            if isinstance(data, dict) and "error" in data:
                err = data["error"]
                if isinstance(err, dict):
                    snippet = err.get("message") or err.get("code") or ""
                elif isinstance(err, str):
                    snippet = err
            if not snippet and isinstance(data, dict):
                snippet = data.get("message") or ""
        except (ValueError, TypeError):
            pass
        if not snippet:
            snippet = (body or "").replace("\n", " ")[:120]
        return _redact(snippet, secret)[:140] or f"Provider error ({code})"

    @staticmethod
    def _classify(provider_id: str, code: int, body: str, secret: str | None) -> tuple[str, str]:
        low = _redact(body or "", secret).lower()
        if code == 429 or any(
            token in low
            for token in ("quota", "rate limit", "rate_limit", "insufficient", "out of credits", "exhausted", "credits")
        ):
            return "quota", f"{provider_id}: quota or rate limit hit - {AIIntegrationService._brief(code, body, secret)}"
        if code in (401, 403):
            return "error", f"Key rejected by provider ({code})"
        return "error", f"{provider_id}: {AIIntegrationService._brief(code, body, secret)}"

    @staticmethod
    def _extract_models(kind: str, data) -> list[dict]:
        models: list[dict] = []
        if kind == "google":
            raw = data.get("models", []) if isinstance(data, dict) else []
            for m in raw:
                mid = m.get("name") or ""
                if mid.startswith("models/"):
                    mid = mid[len("models/"):]
                if mid:
                    models.append(
                        {
                            "id": mid,
                            "context_length": m.get("context_length"),
                            "owned_by": None,
                            "tags": _model_tags(mid),
                        }
                    )
        elif kind == "ollama":
            raw = data.get("models", []) if isinstance(data, dict) else []
            for m in raw:
                mid = m.get("model") or m.get("name") or ""
                if mid:
                    models.append(
                        {
                            "id": mid,
                            "context_length": m.get("context_length"),
                            "owned_by": "ollama",
                            "tags": _model_tags(mid),
                        }
                    )
        else:
            raw = data.get("data", []) if isinstance(data, dict) else []
            for m in raw:
                mid = m.get("id")
                if mid:
                    models.append(
                        {
                            "id": mid,
                            "context_length": m.get("context_length"),
                            "owned_by": m.get("owned_by"),
                            "tags": _model_tags(mid),
                        }
                    )
        models.sort(key=lambda x: x["id"].lower())
        return models

    async def _run_validation(
        self,
        entry,
        api_key: str | None,
        base_url: str | None,
        target: OllamaTarget | None = None,
    ) -> AIValidateOut:
        if entry.kind == "ollama":
            if target is None:
                target = await _safe_ollama_url(base_url or "")
            url = f"{target.request_url}/api/tags"
            headers = dict(target.headers)
            params = None
            extensions = dict(target.extensions)
        else:
            url, headers, params, extensions = self._endpoint(entry, api_key, base_url)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(VALIDATION_TIMEOUT_SECONDS)) as client:
                res = await client.get(url, headers=headers, params=params, extensions=extensions)
                body = res.text
        except httpx.TimeoutException:
            logger.warning("ai validation %s: timeout", entry.id)
            return AIValidateOut(provider=entry.id, status="error", message="Request timed out", models=[])
        except httpx.HTTPError as exc:
            logger.warning("ai validation %s: connection error: %s", entry.id, type(exc).__name__)
            return AIValidateOut(
                provider=entry.id,
                status="error",
                message=_redact(f"Connection error: {exc}", api_key),
                models=[],
            )
        except Exception as exc:  # noqa: BLE001 - surface a red LED instead of crashing
            logger.warning("ai validation %s: unexpected error: %s", entry.id, type(exc).__name__)
            return AIValidateOut(
                provider=entry.id,
                status="error",
                message=_redact(f"{type(exc).__name__}: {exc}", api_key),
                models=[],
            )

        if res.status_code == 200:
            try:
                models = self._extract_models(entry.kind, res.json())
                return AIValidateOut(
                    provider=entry.id,
                    status="active",
                    message=f"Connected - {len(models)} model(s) available",
                    model_count=len(models),
                    models=models,
                )
            except ValueError:
                return AIValidateOut(
                    provider=entry.id,
                    status="error",
                    message="Provider returned an unexpected (non-JSON) response",
                    models=[],
                )

        status, message = self._classify(entry.id, res.status_code, body, api_key)
        logger.warning("ai validation %s: http %s -> %s", entry.id, res.status_code, status)
        return AIValidateOut(provider=entry.id, status=status, message=message, models=[])

    async def _persist_validation(self, owner_id: str, provider: str, result: AIValidateOut) -> None:
        await self.repo.update_status(
            owner_id,
            provider,
            status=result.status,
            message=result.message,
            model_count=result.model_count,
        )
        cache_key = f"{owner_id}:{provider}"
        if result.status == "active":
            SessionModelCache.set(cache_key, [m.model_dump() for m in result.models])
        else:
            # Never cache a failed validation: it would hide recovery for the
            # whole TTL and break the provider LED until the cache expires.
            SessionModelCache.pop(cache_key)

    # -- Public API ------------------------------------------------------------

    async def statuses(self, owner_id: str) -> AIKeyStatusListOut:
        rows = await self.repo.list_by_owner(owner_id)
        entries = [
            AIKeyStatus(
                provider=row.get("provider", ""),
                has_key=True,
                status=row.get("status") or "untested",
                message=row.get("message") or "",
                model_count=int(row.get("model_count") or 0),
                last_validated_at=row.get("last_validated_at"),
            )
            for row in rows
            if row.get("provider")
        ]
        entries.sort(key=lambda e: e.provider)
        return AIKeyStatusListOut(entries=entries)

    async def save_and_validate(
        self,
        owner_id: str,
        provider: str,
        api_key: str | None,
        ollama_base_url: str | None,
    ) -> AIValidateOut:
        entry = get_catalog_entry(provider)
        if entry is None:
            raise LookupError(f"Unknown provider: {provider}")

        if entry.requires_key and not (api_key or "").strip():
            raise ValueError(f"{provider} requires an API key")
        if provider == "ollama" and not (ollama_base_url or "").strip():
            raise ValueError("Ollama requires a base URL (e.g. http://localhost:11434)")

        key = api_key.strip() if api_key else ""
        url = ollama_base_url.strip() if ollama_base_url else None
        target: OllamaTarget | None = None
        if provider == "ollama" and url:
            # Validate before persisting, and reuse the pinned target below so
            # the connection uses the exact address that passed validation.
            target = await _safe_ollama_url(url)
            url = target.original_url

        await self.repo.upsert(
            owner_id,
            provider,
            key_ciphertext=encrypt_secret(key) if key else None,
            ollama_base_url=url,
            status="untested",
            message="Validating...",
        )

        result = await self._run_validation(
            entry, key if entry.requires_key else None, url or entry.base_url, target=target
        )
        await self._persist_validation(owner_id, provider, result)
        return result

    async def validate(self, owner_id: str, provider: str) -> AIValidateOut:
        entry = get_catalog_entry(provider)
        if entry is None:
            raise LookupError(f"Unknown provider: {provider}")

        row = await self.repo.get(owner_id, provider)
        if row is None:
            raise LookupError(f"No key configured for {provider}")
        if entry.requires_key and not row.get(VALID_KEYS_FIELD):
            raise LookupError(f"No key configured for {provider}")

        key = decrypt_secret(row.get(VALID_KEYS_FIELD)) if entry.requires_key else None
        url = row.get("ollama_base_url") or entry.base_url
        target = await _safe_ollama_url(url) if entry.kind == "ollama" else None

        result = await self._run_validation(entry, key, url, target=target)
        await self._persist_validation(owner_id, provider, result)
        return result

    async def models(self, owner_id: str, provider: str) -> AIModelListOut:
        entry = get_catalog_entry(provider)
        if entry is None:
            raise LookupError(f"Unknown provider: {provider}")

        cache_key = f"{owner_id}:{provider}"
        cached = SessionModelCache.get(cache_key)
        if cached is not None:
            return AIModelListOut(provider=provider, cached=True, models=cached)

        row = await self.repo.get(owner_id, provider)
        if row is None:
            raise LookupError(f"No key configured for {provider}")

        key = decrypt_secret(row.get(VALID_KEYS_FIELD)) if entry.requires_key else None
        url = row.get("ollama_base_url") or entry.base_url
        target = await _safe_ollama_url(url) if entry.kind == "ollama" else None

        result = await self._run_validation(entry, key, url, target=target)
        await self._persist_validation(owner_id, provider, result)
        return AIModelListOut(provider=provider, cached=False, models=[m.model_dump() for m in result.models])

    async def delete(self, owner_id: str, provider: str) -> bool:
        SessionModelCache.pop(f"{owner_id}:{provider}")
        return await self.repo.delete(owner_id, provider)