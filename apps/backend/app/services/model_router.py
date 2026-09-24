from __future__ import annotations

import asyncio
import logging
from typing import Protocol

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-3.6-flash"
OLLAMA_MODEL = "llama3.2"
GEMINI_TIMEOUT_SECONDS = 12.0
OLLAMA_TIMEOUT_SECONDS = 20.0
MAX_COMPLETION_TOKENS = 512
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = (1.0, 3.0)


class CompletionProvider(Protocol):
    name: str

    async def complete(self, prompt: str) -> str: ...


def _redact(text: str, secret: str | None) -> str:
    """Strip a secret out of an exception/message before logging."""
    if secret:
        text = text.replace(secret, "***")
    return text


class GeminiProvider:
    """Google AI Studio (REST). Mirrors the README Tier-3 inference target."""

    name = "gemini"

    def __init__(self, api_key: str, model: str = GEMINI_MODEL, retries: int = RETRY_ATTEMPTS) -> None:
        self.api_key = api_key
        self.model = model
        self.retries = max(1, retries)

    async def complete(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": MAX_COMPLETION_TOKENS,
            },
        }
        timeout = httpx.Timeout(GEMINI_TIMEOUT_SECONDS)
        last_exc: Exception | None = None
        for attempt in range(self.retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    res = await client.post(url, params={"key": self.api_key}, json=payload)
                    res.raise_for_status()
                    data = res.json()
                break
            except Exception as exc:  # noqa: BLE001 - retry any transient provider failure
                last_exc = exc
                if attempt < self.retries - 1:
                    backoff = RETRY_BACKOFF_SECONDS[min(attempt, len(RETRY_BACKOFF_SECONDS) - 1)]
                    logger.warning(
                        "gemini attempt %d/%d failed (%s); retrying in %.1fs",
                        attempt + 1,
                        self.retries,
                        _redact(str(exc), self.api_key),
                        backoff,
                    )
                    await asyncio.sleep(backoff)
        else:
            raise RuntimeError(
                f"Gemini request failed after {self.retries} attempts: {_redact(str(last_exc), self.api_key)}"
            ) from last_exc
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Gemini returned no usable text: {data.get('error', data)}") from exc
        if not text:
            raise RuntimeError("Gemini returned an empty completion")
        return text


class GeminiProxyProvider:
    """Gemini via a first-party serverless proxy (e.g. a Vercel route handler) to
    dodge egress/rate-limit issues on hosting platforms that Google throttles.

    Requires a shared-secret bearer token between caller and proxy.
    """

    name = "gemini"

    def __init__(
        self,
        base_url: str,
        token: str,
        model: str = GEMINI_MODEL,
        retries: int = RETRY_ATTEMPTS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.model = model
        self.retries = max(1, retries)

    async def complete(self, prompt: str) -> str:
        url = f"{self.base_url}/genai/complete"
        timeout = httpx.Timeout(GEMINI_TIMEOUT_SECONDS * 3)
        last_exc: Exception | None = None
        for attempt in range(self.retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    res = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {self.token}"},
                        json={"prompt": prompt, "model": self.model},
                    )
                    res.raise_for_status()
                    data = res.json()
                break
            except Exception as exc:  # noqa: BLE001 - retry any transient proxy failure
                last_exc = exc
                if attempt < self.retries - 1:
                    backoff = RETRY_BACKOFF_SECONDS[min(attempt, len(RETRY_BACKOFF_SECONDS) - 1)]
                    logger.warning(
                        "gemini-proxy attempt %d/%d failed (%s); retrying in %.1fs",
                        attempt + 1,
                        self.retries,
                        _redact(str(exc), self.token),
                        backoff,
                    )
                    await asyncio.sleep(backoff)
        else:
            raise RuntimeError(
                f"Gemini proxy request failed after {self.retries} attempts: {_redact(str(last_exc), self.token)}"
            ) from last_exc
        text = (data.get("text") or "").strip() if isinstance(data, dict) else ""
        if not text:
            raise RuntimeError("Gemini proxy returned an empty completion")
        return text


class OllamaProvider:
    """Local Ollama /api/generate endpoint (README Tier-2 hardware-aware target)."""

    name = "ollama"

    def __init__(self, base_url: str, model: str = OLLAMA_MODEL) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def complete(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        timeout = httpx.Timeout(OLLAMA_TIMEOUT_SECONDS)
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
        text = (data.get("response") or "").strip()
        if not text:
            raise RuntimeError("Ollama returned an empty response")
        return text


class SimulatedProvider:
    """Deterministic offline fallback so the pipeline never hard-fails."""

    name = "simulated"

    async def complete(self, prompt: str) -> str:
        first_line = prompt.strip().splitlines()[0] if prompt.strip() else "task"
        return (
            f"[offline] {first_line} — completed with staged planning output. "
            "Connect GOOGLE_AI_STUDIO_KEY or Ollama to enable real inference."
        )


class ModelRouter:
    """Routes completion requests: Gemini (Tier 3) -> Ollama (Tier 2) -> simulated."""

    def __init__(self, settings=None) -> None:
        self.settings = settings or get_settings()

    def resolve(self) -> CompletionProvider:
        if self.settings.google_ai_studio_key and self.settings.google_ai_studio_proxy:
            return GeminiProxyProvider(
                self.settings.google_ai_studio_proxy,
                self.settings.google_ai_studio_proxy_token,
            )
        if self.settings.google_ai_studio_key:
            return GeminiProvider(self.settings.google_ai_studio_key)
        if self.settings.ollama_base_url and self.settings.ollama_base_url != "":
            return OllamaProvider(self.settings.ollama_base_url)
        return SimulatedProvider()

    async def complete(self, prompt: str) -> tuple[str, str]:
        """Returns (text, provider_name); falls back to simulated on any failure."""
        provider = self.resolve()
        try:
            text = await provider.complete(prompt)
            return text, provider.name
        except Exception as exc:
            redacted = _redact(str(exc), self.settings.google_ai_studio_key)
            redacted = _redact(redacted, self.settings.google_ai_studio_proxy_token)
            logger.warning("Model route %s failed: %s; falling back to simulated", provider.name, redacted)
        return await SimulatedProvider().complete(prompt), "simulated"