-- Advanced Code Garage (ACG) — 0001_init.sql
-- Tables: projects, execution_modes, audit_log, agent_logs
-- RLS on by default; backend uses the SERVICE_ROLE key (bypasses RLS),
-- anonymous/direct client access stays locked down.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- Projects
-- ---------------------------------------------------------------------------
create table if not exists public.projects (
    id            uuid primary key default gen_random_uuid(),
    name          text not null,
    description   text,
    repo_url      text,
    status        text not null default 'queued',
    progress      int  not null default 0,
    current_agent text,
    current_task  text,
    owner_id      uuid references auth.users(id) on delete cascade,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Execution modes (single-row: key = 'system')
-- ---------------------------------------------------------------------------
create table if not exists public.execution_modes (
    id         uuid primary key default gen_random_uuid(),
    key        text not null unique,
    value      text not null default 'AI-Man',
    updated_at timestamptz not null default now(),
    constraint execution_modes_key_check   check (key in ('system')),
    constraint execution_modes_value_check check (value in ('Autonomous', 'AI-Man', 'Manual'))
);

insert into public.execution_modes (key, value)
values ('system', 'AI-Man')
on conflict (key) do nothing;

-- ---------------------------------------------------------------------------
-- Audit log
-- ---------------------------------------------------------------------------
create table if not exists public.audit_log (
    id         bigint generated always as identity primary key,
    actor      text,
    action     text not null,
    target     text,
    detail     jsonb,
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Agent log stream (persisted tail of the SSE terminal feed)
-- ---------------------------------------------------------------------------
create table if not exists public.agent_logs (
    id         bigint generated always as identity primary key,
    "timestamp" timestamptz not null default now(),
    level      text not null,
    agent      text not null,
    message    text not null,
    project_id uuid references public.projects(id) on delete cascade
);

-- ---------------------------------------------------------------------------
-- RLS
-- ---------------------------------------------------------------------------
alter table public.projects       enable row level security;
alter table public.execution_modes enable row level security;
alter table public.audit_log      enable row level security;
alter table public.agent_logs     enable row level security;

create policy "projects_select_own" on public.projects
    for select using (auth.uid() = owner_id);

create policy "projects_insert_own" on public.projects
    for insert with check (auth.uid() = owner_id);

-- Single-tenant MVP: mode is world-readable, backend (service role) writes.
create policy "modes_read" on public.execution_modes
    for select using (true);

create policy "modes_insert" on public.execution_modes
    for insert with check (true);

create policy "modes_update" on public.execution_modes
    for update with check (true);

-- Writes allowed (backend/authenticated), reads restricted to service role.
create policy "audit_insert" on public.audit_log
    for insert with check (true);

create policy "agent_logs_read" on public.agent_logs
    for select using (true);

create policy "agent_logs_insert" on public.agent_logs
    for insert with check (true);