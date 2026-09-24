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

```
+---------------------------------------------------------------------------------------------------+
|                                 CLIENT / EDGE PRESENTATION LAYER                                  |
|  Cloudflare Edge CDN / Cloudflare Pages                                                            |
|  - Vite + React 19 + TypeScript + Tailwind CSS                                                    |
|  - Real-Time WebSockets (Terminal Logs) & WebRTC Data/Audio Engine (Git-Sir HUD)                   |
+---------------------------------------------------------------------------------------------------+
                    │ HTTPS / WSS                  │ REST / Auth
                    ▼                              ▼
+----------------------------------------------------+  +-------------------------------------------+
|          APPLICATION CORE / ORCHESTRATION          |  |       PERSISTENCE & STATE LAYER           |
|  FastAPI Engine (Outbound Cloudflare Tunnel)       |  |  Supabase Managed PostgreSQL 15+          |
|  - Master Finite State Machine Orchestration       |  |  - Row Level Security (RLS) Enforced      |
|  - Inbound Git Webhook Verification (HMAC-SHA256)  |  |  - pgvector Workspace Embeddings          |
|  - AST Exception Safety & Sentinel Repair Loop     |  |  - AES-256-GCM Vault Credentials          |
+----------------------------------------------------+  +-------------------------------------------+
                    │                                                      │
                    ▼ Isolation / Sandboxing                               ▼ Model Allocation
+----------------------------------------------------+  +-------------------------------------------+
|             ISOLATED RUNTIME RUNNER                |  |            AI INFERENCE DISPATCH          |
|  POSIX Micro-Sandbox Worker (/tmp/acg_sandboxes)   |  |  Local Hardware Probing + BYOK Cloud      |
|  - Chroot directory isolation & hard memory caps   |  |  - Tier 0-2: Ollama (0.5B to 30B models)  |
|  - Multi-Cloud: Cloudflare, Vercel, Docker, Local  |  |  - Tier 3: Google AI Studio (Gemini Pro)  |
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
      <td><code>Cloudflare Pages</code> + <code>React 19</code></td>
      <td>Unmetered bandwidth, automated CDN caching, real-time split-diff terminal displays, and low-latency bidirectional WebRTC voice streaming via <b>Git-Sir</b>.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Async Core Engine</b></td>
      <td><code>FastAPI</code> + <code>Python 3.11+</code></td>
      <td>Finite State Machine (FSM) event bus managing directional transitions: <i>Intake &rarr; Research &rarr; Architecture &rarr; Synthesis &rarr; Audit &rarr; Delivery</i>.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Ingress & Tunnels</b></td>
      <td><code>Cloudflare Tunnel</code> (<code>cloudflared</code>)</td>
      <td>Outbound-only ingress eliminating static IP costs, open firewall ports, and middle-tier reverse proxies.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Persistence & Identity</b></td>
      <td><code>Supabase</code> (PostgreSQL 15+)</td>
      <td>Row Level Security (RLS), multi-tenant session isolation, and <code>pgvector</code> embeddings for architectural code grounding.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Cryptographic Vault</b></td>
      <td><code>AES-256-GCM</code> Envelope Encryption</td>
      <td>User BYOK credentials encrypted at rest; accessed strictly via short-lived ephemeral tokens. Raw keys never touch logs or Git histories.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Micro-Sandbox Isolation</b></td>
      <td><code>POSIX Jail</code> (<code>/tmp/acg_sandboxes</code>)</td>
      <td>Compilation, linting, and package installations run inside disposable working trees with strict CPU, thread, and memory quotas.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Self-Healing Sentinel</b></td>
      <td><code>AST Engine</code> + <code>CI/CD Webhooks</code></td>
      <td>Extracts stack traces from failed builds, synthesizes AST fixes with try/catch boundaries, and re-triggers tests automatically.</td>
    </tr>
    <tr>
      <td style="color: #39ff14;"><b>Dynamic Model Router</b></td>
      <td><code>Gemini 3.6 Flash</code> + <code>Ollama</code></td>
      <td>Hardware-aware routing: direct Google AI Studio calls or a first-party Vercel proxy (shared-secret, secret-redacted), falling back to local Ollama and finally a staged simulated mode.</td>
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
│       ├── ci.yml                    # Backend pytest + contract drift + frontend lint/typecheck/build
│       └── keep-awake.yml            # Render free-tier keep-alive (every 10 min)
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py               # FastAPI entrypoint, CORS
│   │   │   ├── core/
│   │   │   │   ├── config.py         # pydantic-settings (typed env config)
│   │   │   │   ├── supabase.py       # service-role-first Supabase client
│   │   │   │   ├── auth.py           # ES256/RS256 JWT verification (Supabase JWKS)
│   │   │   │   ├── crypto.py         # Fernet encrypt/decrypt for user provider keys
│   │   │   │   └── event_bus.py      # in-process async pub/sub for SSE
│   │   │   ├── repositories/         # Supabase data access (projects/modes/audit/logs/ai_keys)
│   │   │   ├── services/             # mode, project (pipeline), audit, model_router, ai_integration, ai_catalog
│   │   │   ├── routers/              # /api/v1/agents (swarm + mode)
│   │   │   └── api/v1/               # /api/v1/projects, /api/v1/logs (SSE), /api/v1/ai (catalog/keys/models)
│   │   ├── schemas/                  # Pydantic response/request models
│   │   ├── sql/0001_init.sql         # Tables + RLS policies (idempotent migrations)
│   │   ├── sql/0002_ai_keys.sql      # user_ai_keys (encrypted BYOK vault) + RLS
│   │   ├── scripts/apply_migrations.py # psycopg migration runner
│   │   ├── tests/                    # pytest + TestClient with in-memory fakes
│   │   ├── render.yaml               # Render blueprint (secrets dashboard-managed)
│   │   └── requirements.txt
│   └── frontend/
│       ├── app/                      # Next.js App Router (dashboard, terminal, projects, ai-integration, admin, login, genai)
│       ├── components/               # LiveTerminal etc.
│       ├── lib/                      # api.ts, types.ts (@acg/contract), supabaseClient.ts, hooks
│       ├── vercel.json               # /api/* → Render rewrite
│       └── package.json
├── packages/
│   └── contract/
│       ├── openapi.json              # Live FastAPI contract (source of truth)
│       ├── generated/api.ts          # openapi-typescript output (drift-checked in CI)
│       └── src/index.ts              # @acg/contract typed re-exports
├── pnpm-workspace.yaml               # pnpm monorepo apps/* + packages/*
├── package.json                      # workspace root (packageManager: pnpm@12.6.0)
├── pnpm-lock.yaml
├── Development.md                    # Phased execution plan
├── Development_Roadmap.md            # Feature roadmap by phase
└── README.md
```

> **Note:** `orchestration_kernel.py`, `sentinel_healer.py`, `security_vault.py`,
> sandboxing, voice, ChatOps, and CI-webhook modules remain future work.
> The current backend provides real persistence (Supabase), ES256 auth, mode
> routing, a real model router (Google Gemini direct or via a first-party Vercel
> proxy, falling back to Ollama/simulated), the project pipeline, the SSE log
> stream the UI consumes, and an AI Integration vault: 11 free-tier providers
> (OpenRouter, Groq, SambaNova, Cerebras, DeepSeek, Qwen, Mistral, Cohere, xAI,
> Ollama, plus Google) whose per-user API keys are Fernet-encrypted at rest
> (`user_ai_keys`, RLS) and validated on first connect via a cheap models-list
> call, with live model lists (session-cached) surfaced on the `/ai-integration`
> dashboard. The free-tier Google key caps Gemini at ~20 requests/day
> on `gemini-3.6-flash`; when that quota is exhausted the pipeline degrades
> gracefully to staged simulated output.

---

<!-- ==================== REMOTE BOT CHATOPS ==================== -->
<h2 style="color: #39ff14; text-shadow: 0 0 8px rgba(57, 255, 20, 0.4);">
  🤖 Remote ChatOps Integration
</h2>

<p>Developers can monitor and govern the platform remotely via Telegram and Discord slash commands authenticated through Supabase HMAC-backed webhooks:</p>

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

# 3. Configure credentials
#   - apps/backend/.env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SECRET_KEY,
#     GOOGLE_AI_STUDIO_KEY, optional GOOGLE_AI_STUDIO_PROXY/_TOKEN,
#     USER_KEY_ENCRYPTION_KEY (defaults to SECRET_KEY), OLLAMA_BASE_URL
#   - apps/frontend/.env.local: NEXT_PUBLIC_SUPABASE_URL,
#     NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY

# 4. Run backend & UI
cd apps/backend && ./.venv/bin/uvicorn app.main:app --reload --port 8000
cd apps/frontend && pnpm dev
```

---

<div align="center">
<sub>Advanced Code Garage © Enterprise Systems Engineering Directorate. Zero-Trust Autonomous Architecture.</sub>
</div>
