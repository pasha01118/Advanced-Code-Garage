-- Advanced Code Garage (ACG) — 0006_github_vault.sql
-- GitHub App foundation + versioned repository secrets vault.
-- Application secrets are encrypted by the backend; clients only ever receive
-- metadata (name, scope, fingerprint, version, timestamps).

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- GitHub App installations
-- ---------------------------------------------------------------------------
create table if not exists public.github_installations (
    installation_id bigint primary key,
    account_login   text not null,
    account_type    text not null default '',
    suspended       boolean not null default false,
    linked_by       uuid references auth.users(id) on delete set null,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

alter table public.github_installations enable row level security;
drop policy if exists "github_installations_admin_read" on public.github_installations;
create policy "github_installations_admin_read" on public.github_installations
    for select to authenticated
    using ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

-- ---------------------------------------------------------------------------
-- Repositories visible to this installation
-- ---------------------------------------------------------------------------
create table if not exists public.github_repositories (
    id              uuid primary key default gen_random_uuid(),
    installation_id bigint not null
                    references public.github_installations(installation_id) on delete cascade,
    external_id     bigint not null,
    full_name       text not null,
    name            text not null,
    owner_login     text not null,
    private         boolean not null default false,
    default_branch  text not null default 'main',
    html_url        text not null default '',
    archived        boolean not null default false,
    disabled        boolean not null default false,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    unique (installation_id, external_id)
);

create index if not exists github_repositories_full_name_idx
    on public.github_repositories (full_name);

alter table public.github_repositories enable row level security;
drop policy if exists "github_repositories_all_read" on public.github_repositories;
create policy "github_repositories_all_read" on public.github_repositories
    for select to authenticated using (true);

-- ---------------------------------------------------------------------------
-- Idempotent webhook deliveries
-- ---------------------------------------------------------------------------
create table if not exists public.github_webhook_events (
    id                   uuid primary key default gen_random_uuid(),
    delivery_id          text not null unique,
    event                text not null,
    action               text not null default '',
    installation_id      bigint,
    repository_full_name text not null default '',
    payload              jsonb not null default '{}'::jsonb,
    created_at           timestamptz not null default now()
);

alter table public.github_webhook_events enable row level security;
drop policy if exists "github_webhook_events_admin_read" on public.github_webhook_events;
create policy "github_webhook_events_admin_read" on public.github_webhook_events
    for select to authenticated
    using ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

-- ---------------------------------------------------------------------------
-- Secrets: metadata plus current encrypted payload pointer
-- ---------------------------------------------------------------------------
create table if not exists public.repository_secrets (
    id            uuid primary key default gen_random_uuid(),
    owner_id      uuid not null references auth.users(id) on delete cascade,
    name          text not null check (name ~ '^[A-Za-z0-9_]+$'),
    scope         text not null default 'repository'
                  check (scope in ('user', 'repository', 'environment')),
    repository_id uuid references public.github_repositories(id) on delete cascade,
    environment   text,
    description   text not null default '',
    ciphertext    text not null,
    fingerprint   text not null,
    version       integer not null default 1 check (version > 0),
    created_by    uuid references auth.users(id) on delete set null,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now(),
    revoked_at    timestamptz
);

create unique index if not exists repository_secrets_active_key
    on public.repository_secrets (
        owner_id,
        name,
        coalesce(repository_id, '00000000-0000-0000-0000-000000000000'::uuid),
        coalesce(environment, '')
    )
    where revoked_at is null;

create index if not exists repository_secrets_owner_repo_idx
    on public.repository_secrets (owner_id, repository_id, name);

alter table public.repository_secrets enable row level security;
revoke all on public.repository_secrets from anon, authenticated;
grant select (
    id, owner_id, name, scope, repository_id, environment, description,
    fingerprint, version, created_by, created_at, updated_at, revoked_at
) on public.repository_secrets to authenticated;
drop policy if exists "repository_secrets_owner_read" on public.repository_secrets;
create policy "repository_secrets_owner_read" on public.repository_secrets
    for select to authenticated
    using (auth.uid() = owner_id);

-- ---------------------------------------------------------------------------
-- Secret versions: ciphertext and wrapped data keys stay backend-only
-- ---------------------------------------------------------------------------
create table if not exists public.secret_versions (
    id           uuid primary key default gen_random_uuid(),
    secret_id    uuid not null
                 references public.repository_secrets(id) on delete cascade,
    version      integer not null check (version > 0),
    ciphertext   text not null,
    fingerprint  text not null,
    created_by   uuid references auth.users(id) on delete set null,
    created_at   timestamptz not null default now(),
    unique (secret_id, version)
);

alter table public.secret_versions enable row level security;
revoke all on public.secret_versions from anon, authenticated;

-- ---------------------------------------------------------------------------
-- Secret access audit: every write and internal reveal is recorded
-- ---------------------------------------------------------------------------
create table if not exists public.secret_access_audit (
    id          uuid primary key default gen_random_uuid(),
    secret_id   uuid not null
                references public.repository_secrets(id) on delete cascade,
    actor       uuid references auth.users(id) on delete set null,
    action      text not null check (action in ('create', 'rotate', 'reveal', 'revoke')),
    purpose     text not null default '',
    request_id  text not null default '',
    created_at  timestamptz not null default now()
);

create index if not exists secret_access_audit_secret_idx
    on public.secret_access_audit (secret_id, created_at desc);

alter table public.secret_access_audit enable row level security;
drop policy if exists "secret_access_audit_owner_read" on public.secret_access_audit;
create policy "secret_access_audit_owner_read" on public.secret_access_audit
    for select to authenticated
    using (
        exists (
            select 1 from public.repository_secrets s
            where s.id = secret_id and s.owner_id = auth.uid()
        )
    );
