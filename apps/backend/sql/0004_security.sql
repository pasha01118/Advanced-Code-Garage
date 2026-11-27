-- Advanced Code Garage (ACG) — 0004_security.sql
-- Closes policies that previously granted the anon/public role write or read
-- access, and adds metadata needed for scoped Sentinel auto-fixes.

-- 0001_init.sql originally granted these to PUBLIC (which includes `anon`).
-- The backend uses the service-role key and does not need any of them.
drop policy if exists "modes_insert" on public.execution_modes;
drop policy if exists "modes_update" on public.execution_modes;
drop policy if exists "audit_insert" on public.audit_log;
drop policy if exists "agent_logs_insert" on public.agent_logs;
drop policy if exists "agent_logs_read" on public.agent_logs;

drop policy if exists "agent_logs_read_own" on public.agent_logs;
create policy "agent_logs_read_own" on public.agent_logs
    for select to authenticated
    using (
        exists (
            select 1 from public.projects p
            where p.id = agent_logs.project_id and p.owner_id = auth.uid()
        )
    );

drop policy if exists "projects_select_own" on public.projects;
create policy "projects_select_own" on public.projects
    for select to authenticated using (auth.uid() = owner_id);

drop policy if exists "projects_insert_own" on public.projects;
create policy "projects_insert_own" on public.projects
    for insert to authenticated with check (auth.uid() = owner_id);

drop policy if exists "modes_read" on public.execution_modes;
create policy "modes_read" on public.execution_modes
    for select to authenticated using (true);

-- Sentinel auto-heal needs owner/provider metadata so a model-cache flush can
-- be scoped to one user instead of every user.
alter table public.sentinel_events add column if not exists owner_id uuid;
alter table public.sentinel_events add column if not exists provider text;
