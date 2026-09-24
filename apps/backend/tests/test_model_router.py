import asyncio

import httpx

from app.core.config import Settings
from app.services.model_router import (
    GeminiProvider,
    GeminiProxyProvider,
    ModelRouter,
    OllamaProvider,
    SimulatedProvider,
)
from app.services.project import ProjectService, STAGES
from tests.fakes import FakeAuditRepository, FakeLogsRepository, FakeProjectsRepository


def _settings(**kw) -> Settings:
    overrides = {
        "supabase_url": "https://example.supabase.co",
        "supabase_anon_key": "key",
        "supabase_service_role_key": "role",
        "secret_key": "test",
    }
    overrides.update(kw)
    return Settings(_env_file=None, **overrides)


def test_router_prefers_gemini_when_key_set():
    router = ModelRouter(_settings(google_ai_studio_key="abc"))
    provider = router.resolve()
    assert isinstance(provider, GeminiProvider)


def test_router_prefers_proxy_when_key_and_proxy_set():
    router = ModelRouter(
        _settings(
            google_ai_studio_key="abc",
            google_ai_studio_proxy="https://fe.vercel.app/",
            google_ai_studio_proxy_token="tok",
        )
    )
    provider = router.resolve()
    assert isinstance(provider, GeminiProxyProvider)
    assert provider.base_url == "https://fe.vercel.app"


def test_router_uses_gemini_direct_without_proxy():
    router = ModelRouter(_settings(google_ai_studio_key="abc", google_ai_studio_proxy=""))
    assert isinstance(router.resolve(), GeminiProvider)


def test_router_uses_ollama_when_no_gemini_key():
    router = ModelRouter(_settings(google_ai_studio_key="", ollama_base_url="http://l:11434"))
    provider = router.resolve()
    assert isinstance(provider, OllamaProvider)


def test_router_falls_back_to_simulated():
    router = ModelRouter(_settings(google_ai_studio_key="", ollama_base_url=""))
    provider = router.resolve()
    assert isinstance(provider, SimulatedProvider)


def _patch_httpx(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        return real_client(transport=transport, timeout=kwargs.get("timeout"))

    monkeypatch.setattr("app.services.model_router.httpx.AsyncClient", factory)
    return transport


def test_gemini_parses_candidate_text(monkeypatch):
    _patch_httpx(
        monkeypatch,
        lambda request: httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "  Hello Gemini  "}]}}]},
        ),
    )
    provider = GeminiProvider("dummy-key")
    assert asyncio.run(provider.complete("hi")) == "Hello Gemini"


def test_gemini_error_cascades_in_router(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "overloaded"})

    _patch_httpx(monkeypatch, handler)

    class FailingGeminiProvider(GeminiProvider):
        name = "gemini"

        async def complete(self, prompt: str) -> str:
            raise RuntimeError("boom")

    router = ModelRouter(_settings(google_ai_studio_key="abc"))
    router.resolve = lambda: FailingGeminiProvider("k")
    text, provider = asyncio.run(router.complete("hello"))
    assert provider == "simulated"
    assert text.startswith("[offline]")


def test_gemini_proxy_parses_and_sends_auth(monkeypatch):
    _patch_httpx(
        monkeypatch,
        lambda request: httpx.Response(200, json={"text": " proxied text "}),
    )
    provider = GeminiProxyProvider("https://fe.example.com/", "secret-tok")
    assert asyncio.run(provider.complete("do it")) == "proxied text"


def test_ollama_parses_response(monkeypatch):
    _patch_httpx(
        monkeypatch,
        lambda request: httpx.Response(200, json={"response": "\n  Ollama says hi  "}),
    )
    provider = OllamaProvider("http://localhost:11434", model="qwen")
    assert asyncio.run(provider.complete("hi")) == "Ollama says hi"


def test_simulated_provider_is_deterministic():
    text = asyncio.run(SimulatedProvider().complete("Analyze market for X."))
    assert isinstance(text, str) and text


class FakeRouter:
    def __init__(self, text: str, provider: str = "gemini") -> None:
        self.calls: list[str] = []
        self.text = text
        self.provider = provider

    async def complete(self, prompt: str) -> tuple[str, str]:
        self.calls.append(prompt)
        return self.text, self.provider


def test_pipeline_publishes_real_llm_text():
    fakes = {
        "projects": FakeProjectsRepository(),
        "logs": FakeLogsRepository(),
        "audit": FakeAuditRepository(),
    }
    svc = ProjectService(
        projects=fakes["projects"],
        logs=fakes["logs"],
        audit=fakes["audit"],
        router=FakeRouter("REAL-LLM-OUTPUT"),
    )
    project = asyncio.run(fakes["projects"].create("Demo", "Build a thing", None, "user-1"))
    pid = str(project["id"])
    asyncio.run(svc._run_pipeline(pid))

    messages = [e["message"] for e in fakes["logs"].entries]
    assert messages.count("REAL-LLM-OUTPUT") == len(STAGES)
    updated = asyncio.run(fakes["projects"].get(pid))
    assert updated["status"] == "delivered"
    assert updated["progress"] == 100