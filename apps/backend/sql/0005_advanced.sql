-- Advanced Code Garage (ACG) — 0005_advanced.sql
-- Workspace/UX storage: appearance preferences, terminal snippets + history,
-- notifications, project templates/tags and owner-scoped audit history.
-- The backend uses the service-role key (bypasses RLS); the policies below
-- grant signed-in clients only access to their own rows.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- Appearance preferences (one row per user)
-- ---------------------------------------------------------------------------
create table if not exists public.user_preferences (
    owner_id       uuid primary key references auth.users(id) on delete cascade,
    theme          text not null default 'dark'
                   check (theme in ('dark', 'light')),
    accent         text not null default 'blue'
                   check (accent in ('blue', 'emerald', 'violet', 'amber')),
    density        text not null default 'comfortable'
                   check (density in ('comfortable', 'compact')),
    reduced_motion boolean not null default false,
    updated_at     timestamptz not null default now()
);

alter table public.user_preferences enable row level security;
drop policy if exists "user_preferences_all_own" on public.user_preferences;
create policy "user_preferences_all_own" on public.user_preferences
    for all to authenticated
    using (auth.uid() = owner_id)
    with check (auth.uid() = owner_id);

-- ---------------------------------------------------------------------------
-- Terminal snippets (saved commands)
-- ---------------------------------------------------------------------------
create table if not exists public.terminal_snippets (
    id          uuid primary key default gen_random_uuid(),
    owner_id    uuid not null references auth.users(id) on delete cascade,
    name        text not null,
    command     text not null,
    description text not null default '',
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

create index if not exists terminal_snippets_owner_idx
    on public.terminal_snippets (owner_id, updated_at desc);
alter table public.terminal_snippets enable row level security;
drop policy if exists "terminal_snippets_all_own" on public.terminal_snippets;
create policy "terminal_snippets_all_own" on public.terminal_snippets
    for all to authenticated
    using (auth.uid() = owner_id)
    with check (auth.uid() = owner_id);

-- ---------------------------------------------------------------------------
-- Terminal command history
-- ---------------------------------------------------------------------------
create table if not exists public.terminal_history (
    id         bigint generated always as identity primary key,
    owner_id   uuid not null references auth.users(id) on delete cascade,
    command    text not null,
    created_at timestamptz not null default now()
);

create index if not exists terminal_history_owner_idx
    on public.terminal_history (owner_id, created_at desc);
alter table public.terminal_history enable row level security;
drop policy if exists "terminal_history_all_own" on public.terminal_history;
create policy "terminal_history_all_own" on public.terminal_history
    for all to authenticated
    using (auth.uid() = owner_id)
    with check (auth.uid() = owner_id);

-- ---------------------------------------------------------------------------
-- Notification centre
-- ---------------------------------------------------------------------------
create table if not exists public.notifications (
    id         uuid primary key default gen_random_uuid(),
    owner_id   uuid not null references auth.users(id) on delete cascade,
    type       text not null default 'info'
               check (type in ('info', 'success', 'warn', 'error')),
    title      text not null,
    body       text not null default '',
    source     text not null default 'system',
    source_id  text,
    read_at    timestamptz,
    metadata   jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists notifications_owner_idx
    on public.notifications (owner_id, created_at desc);
create unique index if not exists notifications_owner_source_idx
    on public.notifications (owner_id, source, source_id)
    where source_id is not null;
alter table public.notifications enable row level security;
drop policy if exists "notifications_all_own" on public.notifications;
create policy "notifications_all_own" on public.notifications
    for all to authenticated
    using (auth.uid() = owner_id)
    with check (auth.uid() = owner_id);

-- ---------------------------------------------------------------------------
-- Project templates + tags
-- ---------------------------------------------------------------------------
create table if not exists public.project_templates (
    id                 text primary key,
    name               text not null,
    description        text not null default '',
    default_description text not null default '',
    default_status     text not null default 'queued',
    tags               text[] not null default '{}',
    sort_order         int not null default 0
);

insert into public.project_templates
    (id, name, description, default_description, default_status, tags, sort_order)
values
    ('blank', 'Blank project', 'Start from an empty workspace.', '', 'queued', '{}', 0),
    ('web-app', 'Web application', 'Frontend + API scaffold for a product UI.', 'Build a responsive web application with an authenticated API.', 'queued', '{web,frontend}', 10),
    ('api-service', 'API service', 'Service-first scaffold with health checks.', 'Implement a documented, observable HTTP API service.', 'queued', '{backend,api}', 20),
    ('agent-pipeline', 'Agent pipeline', 'Multi-agent automation workflow.', 'Coordinate a multi-agent pipeline with review and verification stages.', 'queued', '{agents,automation}', 30)
on conflict (id) do nothing;

alter table public.project_templates enable row level security;
drop policy if exists "project_templates_read" on public.project_templates;
create policy "project_templates_read" on public.project_templates
    for select to authenticated using (true);

alter table public.projects add column if not exists tags text[] not null default '{}';
alter table public.projects add column if not exists template_id text;
alter table public.projects add column if not exists pinned boolean not null default false;
create index if not exists projects_owner_updated_idx
    on public.projects (owner_id, updated_at desc);
create index if not exists projects_tags_idx on public.projects using gin (tags);

-- ---------------------------------------------------------------------------
-- Owner-scoped audit history (the legacy audit_log table had no owner column)
-- ---------------------------------------------------------------------------
alter table public.audit_log add column if not exists owner_id uuid
    references auth.users(id) on delete cascade;
create index if not exists audit_log_owner_idx
    on public.audit_log (owner_id, created_at desc);
drop policy if exists "audit_log_select_own" on public.audit_log;
create policy "audit_log_select_own" on public.audit_log
    for select to authenticated
    using (auth.uid() = owner_id);
