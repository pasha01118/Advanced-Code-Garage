-- Advanced Code Garage (ACG) — 0002_ai_keys.sql
-- Per-user AI provider keys (encrypted at rest with Fernet via the backend).
-- Plaintext never touches Postgres: the backend encrypts before writing.

create table if not exists public.user_ai_keys (
    id                uuid primary key default gen_random_uuid(),
    owner_id          uuid references auth.users(id) on delete cascade,
    provider          text not null,
    key_ciphertext    text,
    ollama_base_url   text,
    status            text not null default 'untested',
    message           text,
    model_count       int  not null default 0,
    last_validated_at timestamptz,
    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now(),
    constraint user_ai_keys_owner_provider_unique unique (owner_id, provider),
    constraint user_ai_keys_status_check check (status in ('untested', 'active', 'quota', 'error'))
);

alter table public.user_ai_keys enable row level security;

-- Owner-only access (backend reads via the service-role key, which bypasses RLS).
create policy "user_ai_keys_select_own" on public.user_ai_keys
    for select using (auth.uid() = owner_id);

create policy "user_ai_keys_insert_own" on public.user_ai_keys
    for insert with check (auth.uid() = owner_id);

create policy "user_ai_keys_update_own" on public.user_ai_keys
    for update using (auth.uid() = owner_id);

create policy "user_ai_keys_delete_own" on public.user_ai_keys
    for delete using (auth.uid() = owner_id);