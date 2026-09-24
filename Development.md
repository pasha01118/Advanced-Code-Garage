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
- [x] Frontend lib/api.ts attaches `Authorization: Bearer <supabase session>`
- [x] Replace datetime.utcnow() with timezone-aware datetimes everywhere
- [x] Add proper response models to all endpoints (feeds Phase 2)
- [x] Add backend/tests/ (pytest + TestClient, in-memory fake repos, no network) — 10 passing
- [ ] Replace datetime.utcnow() with timezone-aware datetimes everywhere
- [ ] Add proper response models to all endpoints (feeds Phase 2)
- [ ] Add backend/tests/ (pytest + TestClient, in-memory fake repos, no network)
- [ ] Validate: pip install (fallback py_compile) -> push -> Render auto-deploy -> curl live;
      PROOF: mode survives a redeploy (kill-switch persistence)

## Phase 2 — Contract-First
- [x] Dump FastAPI openapi.json -> backend/openapi.json (committed)
- [x] Frontend: openapi-typescript v7 + gen:api script -> typed client (lib/generated/api.ts)
- [x] Retire hand-duplicated lib/types.ts (now re-exports generated types; LogEntry kept for SSE)
- [ ] GATED — pnpm workspaces (apps/frontend, apps/backend, packages/contract).
      Moves Vercel rootDirectory + Render build paths. PAUSE and confirm before doing.

## Phase 3 — CI + Secret Scrub
- [x] Add .github/workflows/ci.yml: backend pytest; frontend eslint + tsc --noEmit + build
- [ ] Rotate Supabase anon key (Management API / dashboard regenerate)
- [ ] Remove hardcoded JWT from render.yaml (secrets -> sync:false, dashboard-managed)
- [ ] Update backend/.env, frontend/.env.local, Vercel + Render env vars with rotated key
- [ ] Scrub history: git filter-repo --replace-text over the 7 JWT-bearing commits,
      git gc --prune, force-push
- [ ] Verify: `git log --all -S <old-jwt>` returns nothing

## Phase 4 — Deploy Verification & Docs
- [ ] Full live sweep: routes, SSE, mode toggle, project create, persistence proof
- [ ] Update README.md architecture + Development_Roadmap.md checkboxes to match reality
- [ ] Final summary: commit log + what changed + remaining follow-ups