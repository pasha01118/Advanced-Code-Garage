"""Curated catalog of free-tier / open-weight AI inference providers.

Every OpenAI-compatible entry exposes a Bearer-authenticated `GET <models>`
endpoint that doubles as the cheap "first API call" used to validate a key.
Google uses its `/v1beta/models` REST resource with `?key=`, and Ollama is a
local/self-hosted engine with a key-less `/api/tags` endpoint.

Data points below were researched (Sep 2026) and are best-effort: free tiers
change often, so the catalog is guidance, not a contract with the providers.
"""

from dataclasses import dataclass

# kind:
#   "openai"   - OpenAI-compatible, Authorization: Bearer <key>, GET {base}/{models_path}
#   "google"   - Google AI Studio REST, GET {base}/models?key=<key>
#   "ollama"   - key-less, GET {base}/api/tags


@dataclass(frozen=True)
class ProviderCatalogEntry:
    id: str
    name: str
    tagline: str
    description: str
    free_tier: str
    signup_url: str
    kind: str
    requires_key: bool
    base_url: str | None = None
    models_path: str = "/models"


CATALOG: list[ProviderCatalogEntry] = [
    ProviderCatalogEntry(
        id="google",
        name="Google AI Studio",
        tagline="Gemini flash models",
        description="Google's Gemini flash-class models, free with a Google account. "
        "Daily quotas are model-specific and reset at midnight Pacific.",
        free_tier="Flash models ~15 RPM / 1,500 RPD free; no card required. "
        "Some accounts see a strict per-model daily cap.",
        signup_url="https://aistudio.google.com/apikey",
        kind="google",
        requires_key=True,
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ),
    ProviderCatalogEntry(
        id="openrouter",
        name="OpenRouter",
        tagline="Unified gateway to 250+ models",
        description="One API key for hundreds of open models. `:free` variants are "
        "served at $0 and ideal for prototyping.",
        free_tier="`:free` models, 20 req/min; 50 req/day until lifetime credits "
        "exceed $10, then 1,000 req/day.",
        signup_url="https://openrouter.ai/keys",
        kind="openai",
        requires_key=True,
        base_url="https://openrouter.ai/api/v1",
    ),
    ProviderCatalogEntry(
        id="groq",
        name="Groq",
        tagline="Fastest LPU inference",
        description="GroqCloud serves open-weight models (Llama, Qwen, GPT-OSS) on "
        "custom LPUs at exceptional speed.",
        free_tier="30 req/min, 1K req/day per model; 8K TPM / 200K TPD; no card.",
        signup_url="https://console.groq.com/keys",
        kind="openai",
        requires_key=True,
        base_url="https://api.groq.com/openai/v1",
    ),
    ProviderCatalogEntry(
        id="sambanova",
        name="SambaNova Cloud",
        tagline="Ultra-fast RDU inference",
        description="Open-weights models served on RDU hardware with a "
        "genuinely forever-free tier.",
        free_tier="Forever-free: 200K tokens/day, 20 req/min; no card.",
        signup_url="https://cloud.sambanova.ai/apis",
        kind="openai",
        requires_key=True,
        base_url="https://api.sambanova.ai/v1",
    ),
    ProviderCatalogEntry(
        id="cerebras",
        name="Cerebras",
        tagline="Wafer-scale speed",
        description="Cloud inference on Cerebras wafer-scale engines; "
        "OpenAI-compatible API.",
        free_tier="$5 free trial credits on signup; a 1M tokens/day free tier has "
        "been reported.",
        signup_url="https://cloud.cerebras.ai/",
        kind="openai",
        requires_key=True,
        base_url="https://api.cerebras.ai/v1",
    ),
    ProviderCatalogEntry(
        id="deepseek",
        name="DeepSeek",
        tagline="Cheap open-weight reasoning",
        description="DeepSeek's reasoning-focused open models at market-leading "
        "prices via an OpenAI-compatible API.",
        free_tier="~5M signup tokens (granted balance), then pay-as-you-go; "
        "consumer chat is fully free.",
        signup_url="https://platform.deepseek.com/",
        kind="openai",
        requires_key=True,
        base_url="https://api.deepseek.com",
        models_path="/models",
    ),
    ProviderCatalogEntry(
        id="qwen",
        name="Qwen (Alibaba Model Studio)",
        tagline="Alibaba open LLMs",
        description="Alibaba's Qwen family via the DashScope OpenAI-compatible "
        "endpoint, with free quotas per model after activation.",
        free_tier="Per-model free quotas (e.g. 1M tokens) valid 30-180 days after "
        "activation.",
        signup_url="https://bailian.console.aliyun.com/",
        kind="openai",
        requires_key=True,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    ),
    ProviderCatalogEntry(
        id="mistral",
        name="Mistral La Plateforme",
        tagline="EU open-weights models",
        description="Mistral's open-weights models (incl. Codestral) from a "
        "GDPR-friendly European provider.",
        free_tier="Experiment tier: rate-limited free API access; a ~1B "
        "tokens/month cap has been reported.",
        signup_url="https://console.mistral.ai/",
        kind="openai",
        requires_key=True,
        base_url="https://api.mistral.ai/v1",
    ),
    ProviderCatalogEntry(
        id="cohere",
        name="Cohere",
        tagline="Command models + embeddings",
        description="Command chat models and embeddings with a monthly free "
        "allotment, no credit card.",
        free_tier="~1,000 free requests/month on the free developer tier.",
        signup_url="https://dashboard.cohere.com/api-keys",
        kind="openai",
        requires_key=True,
        base_url="https://api.cohere.ai/v1",
    ),
    ProviderCatalogEntry(
        id="xai",
        name="xAI Grok",
        tagline="Grok models",
        description="Grok family APIs from xAI via an OpenAI-compatible endpoint; "
        "mostly paid with promotional trial credits.",
        free_tier="$25 trial credits on signup (30-day expiry); a data-sharing "
        "promo has offered up to $150/mo.",
        signup_url="https://console.x.ai/",
        kind="openai",
        requires_key=True,
        base_url="https://api.x.ai/v1",
    ),
    ProviderCatalogEntry(
        id="ollama",
        name="Ollama",
        tagline="Local & private models",
        description="Self-hosted engine for running any open model on your own "
        "hardware or a private cloud endpoint.",
        free_tier="Self-hosted: unlimited, no rate limits, no card - needs your "
        "own hardware.",
        signup_url="https://ollama.com/download",
        kind="ollama",
        requires_key=False,
        base_url=None,
    ),
]

_BY_ID: dict[str, ProviderCatalogEntry] = {entry.id: entry for entry in CATALOG}


def get_catalog_entry(provider_id: str) -> ProviderCatalogEntry | None:
    return _BY_ID.get(provider_id)


def catalog_ids() -> list[str]:
    return [entry.id for entry in CATALOG]


def list_catalog() -> list[dict]:
    return [
        {
            "id": entry.id,
            "name": entry.name,
            "tagline": entry.tagline,
            "description": entry.description,
            "free_tier": entry.free_tier,
            "signup_url": entry.signup_url,
            "kind": entry.kind,
            "requires_key": entry.requires_key,
        }
        for entry in CATALOG
    ]