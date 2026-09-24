"""Tests for the AI Integration feature: catalog, encrypted key store,
auto first-call validation, LED status mapping, and live+session model lists.
"""

import httpx
import pytest

from app.core.crypto import decrypt_secret, encrypt_secret
from app.services.ai_integration import SessionModelCache

HTTPXTARGET = "app.services.ai_integration.httpx.AsyncClient"


def _patch_httpx(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        return real_client(transport=transport, timeout=kwargs.get("timeout"))

    monkeypatch.setattr(HTTPXTARGET, factory)
    return transport


OPENAI_MODELS = {
    "data": [
        {"id": "qwen/qwen3.6-27b:free", "owned_by": "qwen", "context_length": 131072},
        {"id": "meta-llama/llama-3.3-70b:free", "owned_by": "meta", "context_length": 131072},
    ]
}

GOOGLE_MODELS = {
    "models": [
        {"name": "models/gemini-3.6-flash", "context_length": 1048576},
        {"name": "models/gemini-2.0-flash", "context_length": 1048576},
    ]
}

OLLAMA_TAGS = {"models": [{"name": "llama3.2", "model": "llama3.2", "size": 4947510457}]}


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


def test_catalog_lists_curated_providers(client):
    res = client.get("/api/v1/ai/catalog")
    assert res.status_code == 200
    providers = res.json()["providers"]
    ids = {p["id"] for p in providers}
    assert {"google", "openrouter", "groq", "sambanova", "cerebras", "deepseek", "qwen", "mistral", "cohere", "xai", "ollama"} <= ids
    ollama = next(p for p in providers if p["id"] == "ollama")
    assert ollama["requires_key"] is False
    assert all(p["free_tier"] and p["signup_url"] for p in providers)


# ---------------------------------------------------------------------------
# Save + auto first-call validation -> LED status
# ---------------------------------------------------------------------------


def test_save_google_key_validates_via_models_call(client, fakes, monkeypatch):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, json=GOOGLE_MODELS)

    _patch_httpx(monkeypatch, handler)

    res = client.post("/api/v1/ai/keys", json={"provider": "google", "api_key": "secret-key-abc"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "active"
    assert body["model_count"] == 2
    assert {m["id"] for m in body["models"]} == {"gemini-3.6-flash", "gemini-2.0-flash"}
    assert "key" in calls[0]

    stored = fakes["ai_keys"].rows[("test-user", "google")]
    assert stored["key_ciphertext"] != "secret-key-abc"
    assert decrypt_secret(stored["key_ciphertext"]) == "secret-key-abc"


def test_save_google_requires_key(client):
    res = client.post("/api/v1/ai/keys", json={"provider": "google"})
    assert res.status_code == 400


def test_invalid_key_maps_to_red_status(client, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "API key not valid"}})

    _patch_httpx(monkeypatch, handler)
    res = client.post("/api/v1/ai/keys", json={"provider": "openrouter", "api_key": "bad"})
    assert res.status_code == 200
    assert res.json()["status"] == "error"


def test_quota_maps_to_yellow_status(client, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota exceeded, limit 20"}},
        )

    _patch_httpx(monkeypatch, handler)
    res = client.post("/api/v1/ai/keys", json={"provider": "google", "api_key": "kw"})
    assert res.status_code == 200
    assert res.json()["status"] == "quota"


def test_unknown_provider_404(client):
    res = client.post("/api/v1/ai/keys", json={"provider": "nope", "api_key": "x"})
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------------


def test_ollama_connect_hits_tags_endpoint(client, fakes, monkeypatch):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json=OLLAMA_TAGS)

    _patch_httpx(monkeypatch, handler)
    res = client.post("/api/v1/ai/keys", json={"provider": "ollama", "ollama_base_url": "http://host:11434"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "active"
    assert body["models"][0]["id"] == "llama3.2"
    assert seen == ["http://host:11434/api/tags"]


def test_ollama_requires_base_url(client):
    res = client.post("/api/v1/ai/keys", json={"provider": "ollama"})
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# Key status listing (no ciphertext leak) + delete
# ---------------------------------------------------------------------------


def test_list_keys_reveals_no_ciphertext(client, monkeypatch):
    _patch_httpx(
        monkeypatch,
        lambda request: httpx.Response(200, json=OPENAI_MODELS),
    )
    client.post("/api/v1/ai/keys", json={"provider": "groq", "api_key": "g-key"})

    res = client.get("/api/v1/ai/keys")
    assert res.status_code == 200
    body = res.text
    assert "g-key" not in body
    entries = res.json()["entries"]
    assert any(e["provider"] == "groq" and e["has_key"] is True and e["status"] == "active" for e in entries)


def test_delete_key_clears_config(client, fakes, monkeypatch):
    _patch_httpx(
        monkeypatch,
        lambda request: httpx.Response(200, json=OPENAI_MODELS),
    )
    client.post("/api/v1/ai/keys", json={"provider": "groq", "api_key": "g-key"})
    res = client.delete("/api/v1/ai/keys/groq")
    assert res.status_code == 200
    assert res.json()["deleted"] is True
    assert client.get("/api/v1/ai/keys").json()["entries"] == []


# ---------------------------------------------------------------------------
# Live + session-cached model lists
# ---------------------------------------------------------------------------


def test_models_endpoint_live_then_session_cached(client, monkeypatch):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=OPENAI_MODELS)

    _patch_httpx(monkeypatch, handler)
    client.post("/api/v1/ai/keys", json={"provider": "openrouter", "api_key": "or-key"})

    cached = client.get("/api/v1/ai/keys/openrouter/models")
    assert cached.status_code == 200
    assert cached.json()["cached"] is True
    assert len(cached.json()["models"]) == 2
    assert calls["n"] == 1, "save already populated the cache; no extra upstream call"

    SessionModelCache.pop(f"test-user:openrouter")
    live = client.get("/api/v1/ai/keys/openrouter/models")
    assert live.status_code == 200
    assert live.json()["cached"] is False
    assert calls["n"] == 2


def test_models_endpoint_without_key_404(client):
    res = client.get("/api/v1/ai/keys/groq/models")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Key detail is truly encrypted at rest (fernet round trip)
# ---------------------------------------------------------------------------


def test_fernet_round_trip():
    secret = "very-sensitive-key"
    assert decrypt_secret(encrypt_secret(secret)) == secret