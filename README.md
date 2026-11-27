<div align="center">

  <!-- ==================== HERO SECTION ==================== -->
  <br />

  <h1 style="
    font-size: 52px;
    font-weight: 900;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #c47d3d;
    background: linear-gradient(180deg, #d88b48 0%, #a25e24 45%, #592e10 75%, #3d1c08 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow:
      0 1px 0 #e8a264,
      0 2px 0 #b36b2d,
      0 3px 0 #8f501b,
      0 4px 0 #6e3a10,
      0 6px 1px rgba(0,0,0,0.6),
      0 10px 15px rgba(0,0,0,0.9);
    margin-bottom: 0px;
    display: inline-block;
  ">
    ADVANCED CODE GARAGE
  </h1>

  <!-- Heavy Rustic Underline Bar -->
  <div style="
    width: 68%;
    height: 6px;
    background: linear-gradient(90deg, transparent, #8f501b, #d88b48, #e8a264, #d88b48, #8f501b, transparent);
    border-radius: 4px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.8), 0 0 8px rgba(216, 139, 72, 0.4);
    margin-top: 4px;
    margin-bottom: 14px;
  "></div>

  <!-- Tagline -->
  <p style="
    font-size: 19px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #39ff14;
    text-shadow: 0 0 10px rgba(57, 255, 20, 0.4);
    margin-top: 0px;
    margin-bottom: 25px;
  ">
    🛡️ TOTAL GIT CONTRIBUTING SECURITY SYSTEM 🛡️
  </p>

  <!-- Badges -->
  <p>
    <img src="https://img.shields.io/badge/Security-Zero--Trust%20Gate-39ff14?style=for-the-badge&logo=shield&logoColor=000&labelColor=161b22" alt="Security Shield" />
    <img src="https://img.shields.io/badge/Architecture-FSM%20Swarm-39ff14?style=for-the-badge&logo=diagram-next&logoColor=000&labelColor=161b22" alt="Architecture" />
    <img src="https://img.shields.io/badge/Inference-Dynamic%20Router-39ff14?style=for-the-badge&logo=cpu&logoColor=000&labelColor=161b22" alt="Inference Engine" />
    <img src="https://img.shields.io/badge/Infra-Zero--Dollar%20Baseline-39ff14?style=for-the-badge&logo=serverless&logoColor=000&labelColor=161b22" alt="Zero Budget" />
  </p>

</div>

---

### 🌐 Architectural Overview

```text
+---------------------------------------------------------------------------------------------------+
|                              CLIENT / EDGE LAYER (Vercel)                                          |
|  Next.js 16 App Router + React 19 + TypeScript + Tailwind CSS                                     |
|  - Authenticated SSE streams (terminal logs + Sentinel feed), fetch-based client                  |
+---------------------------------------------------------------------------------------------------+
                    │ HTTPS / REST + SSE        │ Supabase Auth (ES256/RS256 JWT)
                    ▼                           ▼
+----------------------------------------------------+  +-------------------------------------------+
|          APPLICATION CORE / ORCHESTRATION          |  |       PERSISTENCE & STATE LAYER           |
|  FastAPI on Render                                 |  |  Supabase Managed PostgreSQL 15+          |
|  - Project pipeline stages on an in-process bus    |  |  - Row Level Security (RLS) Enforced      |
|  - Sentinel monitor: provider/error scan + heal    |  |  - pgvector embeddings: not provisioned   |
|  - Persisted execution modes and audit trail       |  |  - Fernet-encrypted BYOK credentials      |
+----------------------------------------------------+  +-------------------------------------------+
                    │                                                      │
                    ▼ Model Allocation                                     ▼ Admin
+----------------------------------------------------+  +-------------------------------------------+
|            AI INFERENCE DISPATCH                   |  |  /admin: app_state, provider_metrics,      |
|  Google AI Studio direct or Vercel proxy (BYOK)    |  |  sentinel_events, sentinel_discussion    |
|  -> Ollama fallback -> staged simulated output     |  |  (route-level feature toggles enforced)    |
+----------------------------------------------------+  +-------------------------------------------+
```

---

<h2 style="color: #39ff14; text-shadow: 0 0 8px rgba(57, 255, 20, 0.4);">
  ⚡ Complete Architecture Details Summary
</h2>

<details open>
<summary style="
  font-size: 16px;
  font-weight: bold;
  color: #39ff14;
  cursor: pointer;
  padding: 8px 14px;
  background-color: #0d1117;
  border: 1px solid #39ff14;
  border-radius: 6px;
">
  <b>Expand / Collapse Architectural Systems Specification</b>
</summary>

<br />

<table>
  <thead>
    <tr style="border-bottom: 2px solid #39ff14; background-color: #161b22; color: #39ff14;">
      <th align="left">Component Layer</th>
      <th align="left">Underlying Technology</th>
      <th align="left">Architectural Function & Security Envelopes</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="color: #39ff14;"><b>Edge Presentation</b></td>
      <td><code>Next.js 16 App Router</code> + <code>React 19</code> on Vercel</td>
      <td>App Router dashboard with Tailwind CSS; authenticated SSE streams for terminal logs and Sentinel telemetry. No WebSockets, WebRTC or voice transport.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Async Core Engine</b></td>
      <td><code>FastAPI</code> + <code>Python 3.11+</code></td>
      <td>Project pipeline stages on an in-process async event bus feeding SSE subscribers; execution modes persisted in Supabase.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Deployment / Ingress</b></td>
      <td><code>Vercel</code> + <code>Render</code></td>
      <td>Vercel <code>/api/*</code> rewrite to the Render-hosted FastAPI service; no static IP or outbound tunnel is required.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Persistence & Identity</b></td>
      <td><code>Supabase</code> (PostgreSQL 15+)</td>
      <td>Row Level Security, Supabase Auth (ES256/RS256 JWT) and an admin allowlist. <code>pgvector</code> embeddings are not yet provisioned.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Cryptographic Vault</b></td>
      <td><code>Fernet</code> symmetric encryption</td>
      <td>Per-user BYOK provider keys encrypted at rest in <code>user_ai_keys</code> (RLS). Uses <code>USER_KEY_ENCRYPTION_KEY</code> when set, otherwise <code>SECRET_KEY</code>.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Micro-Sandbox Isolation</b> <i>(future work)</i></td>
      <td><code>POSIX Jail</code> <i>(planned)</i></td>
      <td>Disposable working trees with CPU/memory limits are planned; no sandbox runner is wired today.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Sentinel Monitor</b></td>
      <td><code>SentinelService</code> + Supabase</td>
      <td>Live: scheduled provider/error scan, cache-flush heal and AI-engineer discussion in <code>sentinel_events</code>/<code>sentinel_discussion</code>. AST auto-fix on CI webhooks is future work.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Dynamic Model Router</b></td>
      <td><code>Gemini 3.6 Flash</code> + <code>Ollama</code></td>
      <td>Hardware-aware routing: Google AI Studio direct or via a first-party Vercel proxy (shared-secret, secret-redacted), falling back to local Ollama and finally staged simulated mode.</td>
    </tr>
  </tbody>
</table>

</details>

---

### 👥 The 12-Agent Swarm Directorate

<div align="center">

| Phase | Leadership & Personas | Primary Operational Mandate |
| :--- | :--- | :--- |
| **Command** | **Mr. Azeem Prem** (*"Mr. Git-Hit"*), **Mr. Sami** | Master systems orchestration, voice gateway, and RBAC admin kill-switches. |
| **Strategy** | **Mr. Ravish Kumar**, **Ms. Priya Nair** | Market viability mapping and open-source dependency registry scanning. |
| **Assembly** | **Ms. Sumati Madam**, **Mr. Arman Ali Khan**, **Mr. Khaleel** | Phased roadmaps, resilient full-stack code synthesis, and UI design token implementation. |
| **Gatekeepers**| **Mr. Sadath Ali Khan**, **Ms. Kulsum**, **Ms. Avni**, **Ms. Ananya Joshi** | Cryptographic security audit stamps, AST token stripping, and database migrations. |

</div>

---

<!-- ==================== TRI-MODE GOVERNANCE ==================== -->
<h2 style="color: #39ff14; text-shadow: 0 0 8px rgba(57, 255, 20, 0.4);">
  🎛️ Tri-Mode Operational Spectrum
</h2>

<p>ACG balances high-speed autonomy with zero-trust developer oversight across three dynamic operational states:</p>

<p><i>Modes are persisted, and feature toggles are enforced at the route level (see the status section below). The matrix below describes the intended operating model.</i></p>

<table>
  <thead>
    <tr style="border-bottom: 2px solid #39ff14; background-color: #161b22; color: #39ff14;">
      <th align="left">Dimension</th>
      <th align="left">1. Fully Autonomous Mode</th>
      <th align="left">2. AI-Man (Copilot) Mode</th>
      <th align="left">3. Manual Command Mode</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="color: #39ff14;"><b>Repo Sync</b></td>
      <td>Continuous background polling (every 60s)</td>
      <td>Continuous polling; shows change alerts</td>
      <td>Manual synchronization only</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Dependency Updates</b></td>
      <td>Auto-updates minor/patch, tests, & PRs</td>
      <td>Generates PR diff; pauses for 1-click approval</td>
      <td>Advisory only; touches zero files</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Git & Branching</b></td>
      <td>Direct push to isolated <code>acg/*</code> branches</td>
      <td>Interactive review of commit diffs & messages</td>
      <td>Developer controls all Git actions</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Deployment Clear</b></td>
      <td>Auto-ships to staging on certified audit</td>
      <td>Mandatory 1-click human staging sign-off</td>
      <td>Manual deployment triggers only</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Sentinel Healer</b></td>
      <td>Active; auto-patches runtime and CI errors</td>
      <td>Prompts developer with 1-click AST fix proposal</td>
      <td>Inactive; outputs raw terminal logs</td>
    </tr>
  </tbody>
</table>

---

<!-- ==================== MODEL INFERENCE MATRIX ==================== -->
<h2 style="color: #39ff14; text-shadow: 0 0 8px rgba(57, 255, 20, 0.4);">
  🧠 Hardware Scanner & Model Routing Tiers
</h2>

<table>
  <thead>
    <tr style="border-bottom: 2px solid #39ff14; background-color: #161b22; color: #39ff14;">
      <th align="left">Tier Level</th>
      <th align="left">System Hardware Gate</th>
      <th align="left">Assigned Model Engine</th>
      <th align="left">Operational Task Scope</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="color: #39ff14;"><b>Tier 0: Ultra-Light</b></td>
      <td>&le; 8 GB RAM / Shared VRAM</td>
      <td>Ollama (<code>Qwen-2.5-Coder-0.5B</code>, <code>DeepSeek-1.3B</code>)</td>
      <td>Syntax validation, AST formatting, docstrings, and simple linting.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Tier 1: Mid-Local</b></td>
      <td>16 GB RAM / 4–8 GB VRAM</td>
      <td>Ollama (<code>Llama-3.2-3B</code>, <code>Qwen-2.5-Coder-7B</code>)</td>
      <td>Unit test synthesis, single-file refactoring, static audits.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Tier 2: Heavy-Local</b></td>
      <td>32 GB+ RAM / 12 GB+ VRAM</td>
      <td>Ollama (<code>DeepSeek-Coder-V2-16B</code> to <code>30B</code>)</td>
      <td>Multi-file code synthesis, schema migrations, deep security scans.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Tier 3: Cloud BYOK</b></td>
      <td>Network Connected (BYOK Key)</td>
      <td>Google AI Studio (<code>gemini-3.6-flash</code>)</td>
      <td>High-context orchestration, enterprise architecture, market research. Free tier caps at ~20 requests/day; wire <code>GOOGLE_AI_STUDIO_PROXY</code>/<code>_TOKEN</code> to route via the first-party Vercel proxy when provider egress is throttled.</td>
    </tr>
  </tbody>
</table>

---

<!-- ==================== REPOSITORY TREE ==================== -->
<h2 style="color: #39ff14; text-shadow: 0 0 8px rgba(57, 255, 20, 0.4);">
  📂 Repository File Structure
</h2>

```text
advanced-code-garage/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Backend pytest + OpenAPI/contract drift + frontend lint/typecheck/build
│       └── keep-awake.yml            # Render free-tier keep-alive (every 10 min)
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py               # FastAPI entrypoint, CORS, lifespan sentinel loop
│   │   │   ├── core/
│   │   │   │   ├── config.py         # pydantic-settings (typed env config)
│   │   │   │   ├── supabase.py       # service-role-first Supabase client
│   │   │   │   ├── auth.py           # ES256/RS256 JWT + require_admin/require_service deps
│   │   │   │   ├── crypto.py         # Fernet encrypt/decrypt for user provider keys
│   │   │   │   └── event_bus.py      # in-process async pub/sub for SSE
│   │   │   ├── repositories/         # Supabase data access (projects/modes/audit/logs/ai_keys/admin)
│   │   │   ├── services/             # mode, project (pipeline), audit, model_router, ai_integration,
│   │   │   │                         # ai_catalog, ops_state, sentinel, admin_users, auth_bootstrap
│   │   │   ├── routers/              # /api/v1/agents (swarm + mode)
│   │   │   └── api/v1/               # /api/v1/projects, /api/v1/logs (SSE), /api/v1/ai, /api/v1/admin, /api/v1/auth
│   │   ├── schemas/                  # Pydantic response/request models (incl. admin + auth)
│   │   ├── sql/0001_init.sql         # Tables + RLS policies (idempotent migrations)
│   │   ├── sql/0002_ai_keys.sql      # user_ai_keys (encrypted BYOK vault) + RLS
│   │   ├── sql/0003_admin.sql        # app_state, sentinel_events/discussion, provider_metrics + RLS
│   │   ├── scripts/apply_migrations.py # psycopg migration runner
│   │   ├── scripts/dump_openapi.py   # emits live FastAPI schema for CI drift check
│   │   ├── tests/                    # pytest + TestClient with in-memory fakes
│   │   ├── render.yaml               # Render blueprint (secrets dashboard-managed)
│   │   ├── .env.example              # backend env var template
│   │   └── requirements.txt
│   └── frontend/
│       ├── app/                      # Next.js App Router (dashboard, terminal, projects, ai-integration, admin, login, genai)
│       ├── components/               # LiveTerminal, SystemBanner, BannerWrapper etc.
│       ├── lib/                      # api.ts, types.ts (@acg/contract), stream-sse.ts, supabaseClient.ts, hooks
│       ├── vercel.json               # /api/* → Render rewrite
│       └── package.json
├── packages/
│   └── contract/
│       ├── openapi.json              # Live FastAPI contract (source of truth)
│       ├── generated/api.ts          # openapi-typescript output (drift-checked in CI)
│       ├── src/index.ts              # @acg/contract typed re-exports
│       └── package.json              # gen:api script (openapi-typescript)
├── pnpm-workspace.yaml               # pnpm monorepo apps/* + packages/*
├── package.json                      # workspace root (packageManager: pnpm@12.6.0)
├── pnpm-lock.yaml
├── Development.md                    # Phased execution plan
├── Development_Roadmap.md            # Feature roadmap by phase
└── README.md
```

> The Sentinel *monitor* is live (provider/error scan, cache-flush heal, AI-engineer discussion in
> `sentinel_events`/`sentinel_discussion` on a scheduled loop); AST auto-fix (`sentinel_healer.py`),
> CI-webhook triggers, ChatOps, sandboxing/isolated runners, Docker deployment and voice/Git-Sir are
> future work. `pgvector` embeddings are not provisioned.
>
> The current backend provides Supabase persistence, ES256/RS256 auth, mode routing, a model router
> (Gemini direct or via the first-party Vercel proxy, falling back to Ollama/simulated), the project
> pipeline, and two authenticated SSE streams (terminal logs and Sentinel feed) consumed by a
> fetch-based client. An AI Integration vault covers 11 free-tier providers (OpenRouter, Groq,
> SambaNova, Cerebras, DeepSeek, Qwen, Mistral, Cohere, xAI, Ollama, plus Google): per-user keys are
> Fernet-encrypted at rest in `user_ai_keys` (RLS) and validated on first connect via a models-list
> call, with live model lists on `/ai-integration`.
>
> The admin panel (`/admin`, admin-only) exposes app state (running/maintenance/shutdown), stored
> feature toggles, `provider_metrics`, Sentinel telemetry (`sentinel_events`, `sentinel_discussion`,
> live SSE, click-to-run cycle), user suspend/reactivate, and account settings. **Five toggles are
> enforced at the route level**: `swarm` (agent swarm, mode, project creation), `ai_routing` (AI
> endpoints), `telemetry` (log stream), `sentinel` (Sentinel admin endpoints and SSE), and `signups`
> (first-run admin bootstrap) return 503 when off; `git_ops` and `deployments` remain stored-only.
> First-run admin sign-up requires `APP_BOOTSTRAP_TOKEN`; a global banner
> appears during maintenance/shutdown. The free-tier Google key caps Gemini at ~20 requests/day on
> `gemini-3.6-flash`; pipeline then degrades gracefully to staged simulated output.

---

<!-- ==================== REMOTE BOT CHATOPS ==================== -->
<h2 style="color: #39ff14; text-shadow: 0 0 8px rgba(57, 255, 20, 0.4);">
  🤖 Remote ChatOps Integration (Planned)
</h2>

<p><b>Future work — not implemented.</b> Planned Telegram/Discord slash commands (design below):</p>

| Command | Parameters | Description | Responding Agent |
| :--- | :--- | :--- | :--- |
| `/acg status` | None | System health, active sandbox count, and hardware metrics. | Mr. Sami |
| `/acg audit` | `[repo-url]` | Displays critical blockers, high risks, and certification seal. | Mr. Sadath Ali Khan |
| `/acg mode` | `[auto \| copilot \| manual]` | Updates runtime autonomy tier across the workspace. | Mr. Git-Hit |
| `/acg approve` | `[pr-id]` | Grants 1-click human sign-off to execute pending staging deployment. | Ms. Sumati Madam |
| `/acg token` | None | Returns tokens consumed and percentage optimized by context pruning. | Ms. Kulsum |

---

### 🚀 Getting Started

```bash
# 1. Clone repository securely
git clone https://github.com/your-username/advanced-code-garage.git
cd advanced-code-garage

# 2. Install workspace dependencies (pnpm 12.6.0)
corepack enable && corepack prepare pnpm@12.6.0 --activate
pnpm install

# 3. Configure credentials (see apps/backend/.env.example)
#   - apps/backend/.env: SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY (or SUPABASE_ANON_KEY),
#     SUPABASE_SERVICE_ROLE_KEY, SECRET_KEY, APP_BOOTSTRAP_TOKEN (required for first admin),
#     optional USER_KEY_ENCRYPTION_KEY (defaults to SECRET_KEY), ADMIN_RESET_TOKEN,
#     ADMIN_USER_IDS, SENTINEL_INTERVAL_SECONDS, GOOGLE_AI_STUDIO_KEY,
#     GOOGLE_AI_STUDIO_PROXY/_TOKEN, OLLAMA_BASE_URL, FRONTEND_URLS, ENVIRONMENT
#   - apps/frontend/.env.local: NEXT_PUBLIC_SUPABASE_URL,
#     NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, NEXT_PUBLIC_API_URL=http://localhost:8000
#     (omit NEXT_PUBLIC_API_URL on Vercel; vercel.json rewrites /api)

# 4. Run backend & UI
cd apps/backend && python -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cd apps/backend && ./.venv/bin/uvicorn app.main:app --reload --port 8000
cd apps/frontend && pnpm dev
```

---

<div align="center">
<sub>Advanced Code Garage © Enterprise Systems Engineering Directorate. Zero-Trust Autonomous Architecture.</sub>
</div>
