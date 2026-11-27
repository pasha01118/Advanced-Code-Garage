-- Advanced Code Garage (ACG) — 0007_repo_ops.sql
-- Repository operations hardening: explicit per-repository roles, an append-only
-- operation audit trail, and idempotency keys for retried commits/PRs.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- Per-repository roles
-- ---------------------------------------------------------------------------
create table if not exists public.repo_permissions (
    id            uuid primary key default gen_random_uuid(),
    repository_id uuid not null
                  references public.github_repositories(id) on delete cascade,
    user_id       uuid not null references auth.users(id) on delete cascade,
    role          text not null check (role in ('owner', 'write', 'read')),
    granted_by    uuid references auth.users(id) on delete set null,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now(),
    unique (repository_id, user_id)
);

create index if not exists repo_permissions_user_idx
    on public.repo_permissions (user_id);

alter table public.repo_permissions enable row level security;
drop policy if exists "repo_permissions_admin_read" on public.repo_permissions;
create policy "repo_permissions_admin_read" on public.repo_permissions
    for select to authenticated
    using ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists "repo_permissions_self_read" on public.repo_permissions;
create policy "repo_permissions_self_read" on public.repo_permissions
    for select to authenticated
    using (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- Operation audit (append-only from the client's perspective)
-- ---------------------------------------------------------------------------
create table if not exists public.repo_audit_events (
    id            uuid primary key default gen_random_uuid(),
    repository_id uuid not null
                  references public.github_repositories(id) on delete cascade,
    actor         uuid references auth.users(id) on delete set null,
    action        text not null,
    target        text not null default '',
    detail        jsonb not null default '{}'::jsonb,
    request_id    text not null default '',
    created_at    timestamptz not null default now()
);

create index if not exists repo_audit_events_repo_idx
    on public.repo_audit_events (repository_id, created_at desc);

alter table public.repo_audit_events enable row level security;
revoke all on public.repo_audit_events from anon, authenticated;
drop policy if exists "repo_audit_events_admin_read" on public.repo_audit_events;
create policy "repo_audit_events_admin_read" on public.repo_audit_events
    for select to authenticated
    using ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

-- ---------------------------------------------------------------------------
-- Idempotency ledger: replaying a key returns the original result
-- ---------------------------------------------------------------------------
create table if not exists public.repo_idempotency (
    key           text primary key,
    actor         uuid references auth.users(id) on delete set null,
    repository_id uuid references public.github_repositories(id) on delete cascade,
    action        text not null,
    result        jsonb not null default '{}'::jsonb,
    created_at    timestamptz not null default now()
);

alter table public.repo_idempotency enable row level security;
revoke all on public.repo_idempotency from anon, authenticated;
