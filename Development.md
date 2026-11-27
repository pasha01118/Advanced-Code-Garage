# Advanced Code Garage — Development Execution Plan

Phased execution order for the "Real System, Contract-First" refactor.
Work happens on `main` in incremental commits; the app stays deployed and functional throughout.
Git-history secret scrub runs LAST.

Current stack: FastAPI (backend), Next.js 16 App Router (frontend), Supabase/PostgreSQL, authenticated SSE streams, Fernet-encrypted BYOK keys. Copy `apps/backend/.env.example` to `apps/backend/.env` (see that file for the full variable list, including `APP_BOOTSTRAP_TOKEN` for first admin sign-up) and set `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` in `apps/frontend/.env.local`.

## Phase 0 — Safety Baseline
- [x] Snapshot live state: curl /health, /api/v1/agents/swarm, /api/v1/agents/mode, SSE stream
- [x] Record `git rev-parse HEAD` = c49cd7c and Render deploy dep-daqdv25ckfvc738kaab0 live
- [x] Backup backend/.env and frontend/.env.local to /tmp/opencode

## Phase 1 — Backend Becomes a Real System
- [x] Add backend/app/core/config.py (pydantic-settings): unified env names, typed CORS config
- [x] Update main.py + core/supabase.py to consume config (SUPABASE_PUBLISHABLE_KEY / SUPABASE_ANON_KEY, not SUPABASE_KEY)
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
- [x] Add backend/tests/ (pytest + TestClient, in-memory fake repos, no network)
- [x] Validate: pip install (fallback py_compile) -> push -> Render auto-deploy -> curl live;
      PROOF: mode survives a redeploy (kill-switch persistence)

## Phase 2 — Contract-First
- [x] Dump FastAPI openapi.json (scripts/dump_openapi.py) -> committed packages/contract/openapi.json
- [x] Frontend: openapi-typescript v7 + gen:api script -> typed client (packages/contract/generated/api.ts)
- [x] Retire hand-duplicated lib/types.ts (re-exports @acg/contract; LogEntry kept for SSE)
- [x] **pnpm monorepo** (pnpm@12.6.0): apps/frontend, apps/backend, packages/contract; Vercel
      rootDirectory + Render rootDir + CI updated; contract-drift gate in CI. DONE live.
- [x] **Real model router** (app/services/model_router.py): Gemini REST direct or via first-party
      Vercel proxy (shared-secret, secret-redacted logs), Ollama fallback, staged simulated mode;
      retries + quota fast-fail (Google free tier ~20 req/day on gemini-3.6-flash); pipeline
      publishes real LLM text per stage; E2E verified end to end (fallback path live on free tier).

## Phase 3 — CI + Secret Scrub
- [x] Add .github/workflows/ci.yml: backend pytest + live OpenAPI drift check; frontend eslint + tsc --noEmit + build + generated-contract drift check
- [x] Rotate Supabase anon key -> publishable key (sb_publishable_*); wired to Vercel + .env + client
- [x] Remove hardcoded JWT from render.yaml (now sync:false, dashboard-managed)
- [x] Scrub history + force-push: JWT purged from all 48 commits (verified via fresh clone, `-S` = 0)
- [x] Verify: `git log --all -S <old-jwt>` returns nothing

## Phase 4 — Deploy Verification & Docs
- [x] Full live sweep: routes, 401 gates, both authenticated SSE streams (fetch-based client), DB-backed mode persistence proven (flip at SQL level)
- [x] **E2E pressure-test**: authed create -> pipeline -> delivered; fixed live only-if-found bugs
      (supabase-py 2.9 sync SDK has no `.maybe_single()` — now `limit(1)` + row normalizer)
- [x] Update README.md architecture + Development_Roadmap.md checkboxes to match reality
- [x] Update README repository tree to pnpm monorepo layout (apps/ + packages/)
- [ ] Final summary: commit log + what changed + remaining follow-ups

## Phase 5 — Admin Panel & Self-Healing Sentinel
- [x] Migration `sql/0003_admin.sql`: `app_state` (single running/maintenance/shutdown row + 7
      feature toggles), `sentinel_events` + `sentinel_discussion` (RLS service-role), `provider_metrics`;
      admin JWT `sub` allowlist via `ADMIN_USER_IDS` env var; applied to Supabase
- [x] Core config additions: `admin_reset_token`, `sentinel_interval_seconds`,
      `require_admin` dependency (app_metadata.role == "admin" OR sub in `ADMIN_USER_IDS` OR service role)
- [x] `app/services/ops_state.py`: cached state service + `require_service(feature)` gating dependency;
      five toggles are enforced at the route level (503 when off): `swarm` (/agents/swarm,
      /agents/mode, POST /projects), `ai_routing` (/ai/*), `telemetry` (/logs/*), `sentinel`
      (/admin/sentinel* incl. SSE) and `signups` (POST /auth/bootstrap); `git_ops` and `deployments`
      are stored but reserved (not yet wired)
- [x] `app/services/sentinel.py`: SentinelService.run_cycle — provider health scan
      (aggregate_providers + catalog), error-log scan (agent_logs), auto-heal (flush_cache),
      AI-engineer discussion personas; background loop via FastAPI lifespan
- [x] `app/services/admin_users.py`: Supabase Admin API client (list, set identity/email, ban/unban)
- [x] `app/api/v1/admin/route.py`: /state (GET any-authed, POST admin), /toggles/{name},
      /providers/usage, /sentinel/events + /discussion + /snapshot + /run + /stream (SSE),
      /users, /users/{id}/suspend + /reactivate, /account; mounted at /api/v1/admin
- [x] `POST /api/v1/auth/admin/forgot-password`: token-based (ADMIN_RESET_TOKEN) admin password reset;
      first-run admin sign-up requires `APP_BOOTSTRAP_TOKEN`
- [x] Backend tests: admin, sentinel, auth/bootstrap and config coverage; full suite passing
- [x] Contract regen: openapi.json rewritten + gen:api regenerated
- [x] Frontend: tabbed /admin dashboard (Overview / Providers / Sentinel / Users / Account),
      SystemBanner maintenance/shutdown banner, RBAC nav enforcement, admin API client + types
- [x] Verify: backend pytest 68 pass, frontend lint/typecheck/build clean, health + /admin/state live