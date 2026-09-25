# Advanced Code Garage (ACG) Development Roadmap

*Note: This roadmap is structured by logical dependency and feature completion. No time, day, date, or week markers are assigned.*

## Phase 1: Core Infrastructure & Foundation
- [x] Initialize repository structure (pnpm monorepo: FastAPI backend, Next.js frontend, packages/contract).
- [x] Configure Supabase (PostgreSQL, RLS) — NOTE: pgvector embeddings not yet provisioned.
- [x] Implement secure authentication (Supabase client auth; backend ES256/RS256 JWT verification).
- [x] Implement the encrypted BYOK (Bring Your Own Key) vault
      (Fernet-encrypted per-user provider keys in `user_ai_keys` + RLS; live `sql/0002_ai_keys.sql`).
- [ ] Establish baseline Docker environment.

## Phase 2: AI Orchestration & Routing Engine
- [x] Build `model_router.py`: Hardware/provider-aware inference adapter
      (Gemini 3.6 Flash direct or via Vercel proxy -> Ollama -> staged simulated). Live.
- [ ] Build `context_compressor.py`: Token-hygiene logic to strip bloat.
- [ ] Develop `orchestration_kernel.py`: Async event bus for state transitions.

## Phase 3: Secure Git Operations & Sandboxing
- [ ] Develop `git_worker.py`: Automated, safe Git operations and conventional commits.
- [ ] Enforce strict branch taxonomy (`acg/feature-*`, etc.) preventing direct pushes to `main`.
- [ ] Implement ephemeral sandbox environments.

## Phase 4: Multi-Agent Swarm Implementation
- [x] **Mr. Ravish Kumar (Research)**: Market/stack feasibility phase implemented (pipeline stage).
- [x] **Mr. Arman Ali Khan (Engineering)**: Boilerplate and component logic synthesis (pipeline stage).
- [x] **Mr. Sadath Ali Khan (Auditor)**: Zero-tolerance static analysis and security gate (pipeline stage).
- [x] **Git-Sir (Orchestrator)**: Delivery orchestration + mode switching (pipeline stage + mode service).

## Phase 5: Deployment Pipeline & External Integrations
- [ ] Integrate drivers for Cloudflare, Vercel, and Docker.
- [ ] Build webhook listeners for build logs and self-healing.
- [ ] Develop Telegram/Discord bot gateways.

## Phase 6: Frontend Dashboard & Admin Control
- [x] Build Agent Playground UI and real-time terminal (SSE).
- [x] Implement 3 Execution Mode toggles (Autonomous, AI-Man, Manual) — persisted in Supabase.
- [x] Develop Secret Admin Control Panel (RBAC, kill switches).
- [x] Build AI Integration dashboard (11-provider catalog, connect keys, live model lists,
      LED connectivity status, Ollama modal).
- [x] Build full Admin Panel: operational state (running/maintenance/shutdown), feature toggles,
      provider usage metrics, Sentinel telemetry (events/discussion/live SSE), user management
      (suspend/reactivate), and admin account settings.
- [x] Add global maintenance/shutdown banner + RBAC nav enforcement for non-admins.

## Phase 7: Hardening, Resilience & Testing
- [x] Implement self-healing Sentinel service (provider + error-log scan, auto flush-cache heal,
      AI-engineer discussion, background loop on FastAPI lifespan).
- [ ] Implement `offline_cache.py` for WAN resilience.
- [ ] Execute `test_benchmarks.py` for performance validation.
- [ ] Conduct end-to-end penetration testing.
