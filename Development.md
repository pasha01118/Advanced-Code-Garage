# Advanced Code Garage — Development Execution Plan

Phased execution order for the "Real System, Contract-First" refactor.
Work happens on `main` in incremental commits; the app stays deployed and functional throughout.
Git-history secret scrub runs LAST.

## Phase 0 — Safety Baseline
- [x] Snapshot live state: curl /health, /api/v1/agents/swarm, /api/v1/agents/mode, SSE stream
- [x] Record `git rev-parse HEAD` = c49cd7c and Render deploy dep-daqdv25ckfvc738kaab0 live
- [x] Backup backend/.env and frontend/.env.local to /tmp/opencode

## Phase 1 — Backend Becomes a Real System
- [x] Add backend/app/core/config.py (pydantic-settings): unified env names, typed CORS config
- [x] Update main.py + core/supabase.py to consume config (SUPABASE_ANON_KEY, not SUPABASE_KEY)
- [x] Add backend/sql/0001_init.sql: projects, execution_modes, audit_log, agent_logs + RLS
- [x] Apply migration to Supabase (scripts/apply_migrations.py) — tables + RLS seeded
- [x] Add repository layer (projects/modes/audit/logs) behind testable abstract base
- [x] Add service layer: project_service, mode_service (persistent mode), audit_service
- [x] Add core/event_bus.py: async subscribers; logs route subscribes + persists
- [x] Replace simulated random log stream with real event-bus + persistence
- [x] Add core/auth.py: RS256 JWT verify via Supabase JWKS; protect /mode + /projects
- [x] Expand auth to verify **ES256** JWTs (Supabase now signs ES256; ES256/RS256 both accepted)
- [x] Frontend lib/api.ts attaches `Authorization: Bearer <supabase session>`
- [x] Replace datetime.utcnow() with timezone-aware datetimes everywhere
- [x] Add proper response models to all endpoints (feeds Phase 2)
- [x] Add backend/tests/ (pytest + TestClient, in-memory fake repos, no network) — 28 passing
- [x] Validate: pip install (fallback py_compile) -> push -> Render auto-deploy -> curl live;
      PROOF: mode survives a redeploy (kill-switch persistence)

## Phase 2 — Contract-First
- [x] Dump FastAPI openapi.json -> (packages/contract/openapi.json, committed)
- [x] Frontend: openapi-typescript v7 + gen:api script -> typed client (packages/contract/generated/api.ts)
- [x] Retire hand-duplicated lib/types.ts (re-exports @acg/contract; LogEntry kept for SSE)
- [x] **pnpm monorepo** (pnpm@12.6.0): apps/frontend, apps/backend, packages/contract; Vercel
      rootDirectory + Render rootDir + CI updated; contract-drift gate in CI. DONE live.
- [x] **Real model router** (app/services/model_router.py): Gemini REST direct or via first-party
      Vercel proxy (shared-secret, secret-redacted logs), Ollama fallback, staged simulated mode;
      retries + quota fast-fail (Google free tier ~20 req/day on gemini-3.6-flash); pipeline
      publishes real LLM text per stage; E2E verified end to end (fallback path live on free tier).

## Phase 3 — CI + Secret Scrub
- [x] Add .github/workflows/ci.yml: backend pytest; frontend eslint + tsc --noEmit + build
- [x] Rotate Supabase anon key -> publishable key (sb_publishable_*); wired to Vercel + .env + client
- [x] Remove hardcoded JWT from render.yaml (now sync:false, dashboard-managed)
- [x] Scrub history + force-push: JWT purged from all 48 commits (verified via fresh clone, `-S` = 0)
- [x] Verify: `git log --all -S <old-jwt>` returns nothing

## Phase 4 — Deploy Verification & Docs
- [x] Full live sweep: routes, 401 gates, SSE, DB-backed mode persistence proven (flip at SQL level)
- [x] **E2E pressure-test**: authed create -> pipeline -> delivered; fixed live only-if-found bugs
      (supabase-py 2.9 sync SDK has no `.maybe_single()` — now `limit(1)` + row normalizer)
- [x] Update README.md architecture + Development_Roadmap.md checkboxes to match reality
- [x] Update README repository tree to pnpm monorepo layout (apps/ + packages/)
- [ ] Final summary: commit log + what changed + remaining follow-ups