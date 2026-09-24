# Advanced Code Garage (ACG) Development Roadmap

*Note: This roadmap is structured by logical dependency and feature completion. No time, day, date, or week markers are assigned.*

## Phase 1: Core Infrastructure & Foundation
- [x] Initialize repository structure (FastAPI backend, Next.js/React frontend).
- [x] Configure Supabase (PostgreSQL, RLS) — NOTE: pgvector embeddings not yet provisioned.
- [x] Implement secure authentication (Supabase client auth; backend RS256 JWT verification).
- [ ] Implement the encrypted BYOK (Bring Your Own Key) vault.
- [ ] Establish baseline Docker environment.

## Phase 2: AI Orchestration & Routing Engine
- [ ] Build `model_router.py`: Hardware-aware inference adapter (Ollama/Cloud).
- [ ] Build `context_compressor.py`: Token-hygiene logic to strip bloat.
- [ ] Develop `orchestration_kernel.py`: Async event bus for state transitions.

## Phase 3: Secure Git Operations & Sandboxing
- [ ] Develop `git_worker.py`: Automated, safe Git operations and conventional commits.
- [ ] Enforce strict branch taxonomy (`acg/feature-*`, etc.) preventing direct pushes to `main`.
- [ ] Implement ephemeral sandbox environments.

## Phase 4: Multi-Agent Swarm Implementation
- [ ] **Mr. Ravish Kumar (Research)**: Market/stack feasibility analysis.
- [ ] **Mr. Arman Ali Khan (Engineering)**: Boilerplate and component logic synthesis.
- [ ] **Mr. Sadath Ali Khan (Auditor)**: Zero-tolerance static analysis and security gate.
- [ ] **Git-Sir (Orchestrator)**: Central UI-facing agent for mode switching.

## Phase 5: Deployment Pipeline & External Integrations
- [ ] Integrate drivers for Cloudflare, Vercel, and Docker.
- [ ] Build webhook listeners for build logs and self-healing.
- [ ] Develop Telegram/Discord bot gateways.

## Phase 6: Frontend Dashboard & Admin Control
- [x] Build Agent Playground UI and real-time terminal (SSE).
- [x] Implement 3 Execution Mode toggles (Autonomous, AI-Man, Manual) — persisted in Supabase.
- [x] Develop Secret Admin Control Panel (RBAC, kill switches).

## Phase 7: Hardening, Resilience & Testing
- [ ] Implement `offline_cache.py` for WAN resilience.
- [ ] Execute `test_benchmarks.py` for performance validation.
- [ ] Conduct end-to-end penetration testing.
