from __future__ import annotations

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


class CompletionProvider(Protocol):
    name: str

    async def complete(self, prompt: str) -> str: ...


class GeminiProvider:
    """Google AI Studio (REST). Mirrors the README Tier-3 inference target."""

    name = "gemini"

    def __init__(self, api_key: str, model: str = GEMINI_MODEL) -> None:
        self.api_key = api_key
        self.model = model

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
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.post(url, params={"key": self.api_key}, json=payload)
            res.raise_for_status()
            data = res.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Gemini returned no usable text: {data.get('error', data)}") from exc
        if not text:
            raise RuntimeError("Gemini returned an empty completion")
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
            logger.warning("Model route %s failed: %s; falling back to simulated", provider.name, exc)
        return await SimulatedProvider().complete(prompt), "simulated"