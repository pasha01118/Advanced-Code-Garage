-- Advanced Code Garage (ACG) — 0003_admin.sql
-- Operational state + toggles, provider usage metrics, sentinel (self-healing)
-- event log and agent discussion thread. All admin tables are RLS-gated to the
-- ADMIN role claim; the backend writes via the service-role key.

-- Lookup helper: is the caller an admin (JWT app_metadata.role == 'admin')?
create or replace function public.is_admin()
returns boolean
language sql
stable
as $$
  select coalesce((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin', false);
$$;

-- ---------------------------------------------------------------------------
-- App operational state (single row: id = 1) + feature toggles
-- ---------------------------------------------------------------------------
create table if not exists public.app_state (
    id         int primary key default 1 check (id = 1),
    status     text not null default 'running'
               check (status in ('running', 'maintenance', 'shutdown')),
    message    text not null default '',
    toggles    jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

insert into public.app_state (id, status, message)
values (1, 'running', '')
on conflict (id) do nothing;

alter table public.app_state enable row level security;

create policy "app_state_select_any_authed" on public.app_state
    for select to authenticated using (true);

create policy "app_state_admin_write" on public.app_state
    for update to authenticated using (public.is_admin()) with check (public.is_admin());

-- ---------------------------------------------------------------------------
-- Provider usage metrics (populated by the Sentinel scan)
-- ---------------------------------------------------------------------------
create table if not exists public.provider_metrics (
    provider         text primary key,
    status           text not null default 'untested',
    message          text default '',
    model_count      int not null default 0,
    tokens_used      bigint not null default 0,
    balance_available numeric,
    checked_at       timestamptz not null default now()
);

alter table public.provider_metrics enable row level security;

create policy "provider_metrics_admin_all" on public.provider_metrics
    for all to authenticated using (public.is_admin()) with check (public.is_admin());

-- ---------------------------------------------------------------------------
-- Sentinel events (real findings + AI-agent analysis)
-- ---------------------------------------------------------------------------
create table if not exists public.sentinel_events (
    id              uuid primary key default gen_random_uuid(),
    created_at      timestamptz not null default now(),
    severity        text not null default 'info'
                    check (severity in ('info', 'warn', 'error')),
    scope           text not null default 'system',
    agent           text not null default 'Sentinel',
    title           text not null,
    message         text not null default '',
    status          text not null default 'open'
                    check (status in ('open', 'resolved', 'auto_fixed')),
    suggested_fix   text not null default '',
    auto_fix_report text not null default '',
    resolved_at     timestamptz
);

create index if not exists sentinel_events_created_idx on public.sentinel_events (created_at desc);
alter table public.sentinel_events enable row level security;

create policy "sentinel_events_admin_all" on public.sentinel_events
    for all to authenticated using (public.is_admin()) with check (public.is_admin());

-- ---------------------------------------------------------------------------
-- Sentinel agent discussion thread (live telemetry chat)
-- ---------------------------------------------------------------------------
create table if not exists public.sentinel_discussion (
    id         bigint generated always as identity primary key,
    created_at timestamptz not null default now(),
    agent      text not null default 'Sentinel',
    message    text not null
);

alter table public.sentinel_discussion enable row level security;

create policy "sentinel_discussion_admin_all" on public.sentinel_discussion
    for all to authenticated using (public.is_admin()) with check (public.is_admin());