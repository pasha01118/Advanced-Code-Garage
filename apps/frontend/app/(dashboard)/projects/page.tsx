"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  FolderGit2,
  GitBranch,
  Loader2,
  Pin,
  Plus,
  RefreshCw,
  Search,
  Tag,
} from "lucide-react";
import {
  bulkProjectAction,
  getProjectStatus,
  initializeProject,
  listProjectTemplates,
  listProjects,
  updateProjectMeta,
} from "@/lib/api";
import type {
  BulkProjectRequest,
  ProjectOut,
  ProjectTemplateOut,
} from "@/lib/types";

const STATUSES = ["queued", "analyzing", "delivered", "failed"] as const;

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectOut[]>([]);
  const [templates, setTemplates] = useState<ProjectTemplateOut[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [expanded, setExpanded] = useState<string | null>(null);
  const [tagDraft, setTagDraft] = useState("");
  const [bulkValue, setBulkValue] = useState("");
  const [checkingId, setCheckingId] = useState<string | null>(null);
  const [statusErrors, setStatusErrors] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // New-project form.
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [templateId, setTemplateId] = useState("");
  const [createTags, setCreateTags] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await listProjects({
        status: statusFilter || undefined,
        tag: tagFilter.trim() || undefined,
        search: search.trim() || undefined,
      });
      setProjects(result.projects ?? []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, tagFilter, search]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 150);
    return () => window.clearTimeout(timer);
  }, [load]);

  useEffect(() => {
    void listProjectTemplates()
      .then((data) => setTemplates(data.templates))
      .catch(() => {
        // Templates are optional; the create form still works without them.
      });
  }, []);

  const applyTemplate = (id: string) => {
    setTemplateId(id);
    const template = templates.find((item) => item.id === id);
    if (template) {
      setDescription((current) => current || template.default_description);
      setCreateTags((current) => current || template.tags.join(", "));
    }
  };

  const parseTags = (value: string): string[] =>
    value.split(",").map((tag) => tag.trim()).filter(Boolean).slice(0, 20);

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await initializeProject({
        name: name.trim(),
        description: description.trim() || undefined,
        repo_url: repoUrl.trim() || undefined,
        template_id: templateId || undefined,
        tags: parseTags(createTags),
      });
      setName("");
      setDescription("");
      setRepoUrl("");
      setTemplateId("");
      setCreateTags("");
      setNotice("Project initialized. The swarm is dispatching.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to initialize project");
    } finally {
      setBusy(false);
    }
  };

  const handleCheck = async (projectId: string) => {
    setCheckingId(projectId);
    try {
      const status = await getProjectStatus(projectId);
      setProjects((prev) => prev.map((p) => (p.id === projectId ? status : p)));
      setStatusErrors((prev) => {
        const next = new Set(prev);
        next.delete(projectId);
        return next;
      });
    } catch {
      setStatusErrors((prev) => new Set(prev).add(projectId));
    } finally {
      setCheckingId(null);
    }
  };

  const toggleSelected = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const runBulk = async (action: BulkProjectRequest["action"], value?: string) => {
    if (selected.size === 0) return;
    if (action === "delete" && !window.confirm(`Delete ${selected.size} project(s)? This cannot be undone.`)) {
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const result = await bulkProjectAction({ ids: [...selected], action, value });
      setNotice(`${result.affected} project(s) updated (${result.action}).`);
      setSelected(new Set());
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bulk action failed");
    } finally {
      setBusy(false);
    }
  };

  const updateMeta = async (id: string, patch: { tags?: string[]; pinned?: boolean }) => {
    setBusy(true);
    setError(null);
    try {
      await updateProjectMeta(id, patch);
      setNotice("Project updated.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update project");
    } finally {
      setBusy(false);
    }
  };

  const openDetails = (project: ProjectOut) => {
    setExpanded((current) => (current === project.id ? null : project.id));
    setTagDraft((project.tags ?? []).join(", "));
  };

  const allVisibleSelected = projects.length > 0 && projects.every((p) => selected.has(p.id));

  const bulkButtons = useMemo(() => [
    { action: "pin" as const, label: "Pin", needsValue: false },
    { action: "unpin" as const, label: "Unpin", needsValue: false },
    { action: "tag" as const, label: "Tag", needsValue: true },
    { action: "untag" as const, label: "Untag", needsValue: true },
    { action: "status" as const, label: "Set status", needsValue: true },
    { action: "delete" as const, label: "Delete", needsValue: false },
  ], []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FolderGit2 className="w-6 h-6 text-blue-400" /> Projects
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Initialize projects, organize them with tags and templates, and dispatch the agent swarm.
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-950/40 border border-red-800/40 rounded-xl text-sm text-red-300">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}
      {notice && (
        <div className="rounded-xl border border-emerald-800/40 bg-emerald-950/30 px-4 py-2.5 text-sm text-emerald-300">
          {notice}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 lg:col-span-1 self-start">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Plus className="w-5 h-5 text-blue-400" /> New Project
          </h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Project Name *</label>
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                required
                placeholder="e.g. acg-ecommerce"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            {templates.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Template</label>
                <select
                  value={templateId}
                  onChange={(event) => applyTemplate(event.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">None — start from scratch</option>
                  {templates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Description</label>
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={3}
                placeholder="What should the swarm build?"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Repository URL (optional)
              </label>
              <input
                value={repoUrl}
                onChange={(event) => setRepoUrl(event.target.value)}
                placeholder="https://github.com/..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Tags <span className="text-slate-500 font-normal">(comma separated)</span>
              </label>
              <input
                value={createTags}
                onChange={(event) => setCreateTags(event.target.value)}
                placeholder="frontend, api"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={busy || !name.trim()}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition"
            >
              {busy ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Dispatching Swarm...</>
              ) : (
                <><Plus className="w-4 h-4" /> Initialize Project</>
              )}
            </button>
          </form>
        </section>

        <section className="lg:col-span-2 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-semibold flex items-center gap-2 mr-auto">
              <GitBranch className="w-5 h-5 text-purple-400" /> Active Projects
              {loading && <Loader2 className="w-4 h-4 animate-spin text-slate-500" />}
            </h2>
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search projects"
                aria-label="Search projects"
                className="w-40 rounded-lg border border-slate-800 bg-slate-950 pl-8 pr-2 py-1.5 text-xs text-slate-200 outline-none focus:border-blue-600"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              aria-label="Filter by status"
              className="rounded-lg border border-slate-800 bg-slate-950 px-2 py-1.5 text-xs text-slate-300 outline-none focus:border-blue-600"
            >
              <option value="">All statuses</option>
              {STATUSES.map((status) => <option key={status} value={status}>{status}</option>)}
            </select>
            <input
              value={tagFilter}
              onChange={(event) => setTagFilter(event.target.value)}
              placeholder="Filter by tag"
              aria-label="Filter by tag"
              className="w-28 rounded-lg border border-slate-800 bg-slate-950 px-2 py-1.5 text-xs text-slate-200 outline-none focus:border-blue-600"
            />
          </div>

          {selected.size > 0 && (
            <div className="flex flex-wrap items-center gap-2 rounded-xl border border-blue-800/50 bg-blue-950/25 p-3">
              <span className="text-xs text-blue-200 mr-1">{selected.size} selected</span>
              <input
                value={bulkValue}
                onChange={(event) => setBulkValue(event.target.value)}
                placeholder="Value (tag / status)"
                aria-label="Bulk action value"
                className="w-32 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-[11px] text-slate-200 outline-none focus:border-blue-600"
              />
              {bulkButtons.map((button) => (
                <button
                  key={button.action}
                  type="button"
                  disabled={busy || (button.needsValue && !bulkValue.trim())}
                  onClick={() => void runBulk(button.action, bulkValue.trim() || undefined)}
                  className={`rounded px-2 py-1 text-[11px] disabled:opacity-40 ${
                    button.action === "delete"
                      ? "bg-red-900/40 text-red-300 hover:bg-red-900/70"
                      : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                  }`}
                >
                  {button.label}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setSelected(new Set())}
                className="ml-auto text-[11px] text-slate-400 hover:text-slate-200"
              >
                Clear
              </button>
            </div>
          )}

          <label className="flex items-center gap-2 text-[11px] text-slate-500 px-1">
            <input
              type="checkbox"
              checked={allVisibleSelected}
              onChange={(event) =>
                setSelected(event.target.checked ? new Set(projects.map((p) => p.id)) : new Set())
              }
              className="w-3.5 h-3.5 accent-blue-600"
            />
            Select all visible
          </label>

          {projects.length === 0 && !loading ? (
            <div className="bg-slate-900 border border-slate-800 border-dashed rounded-xl p-8 text-center text-sm text-slate-500">
              No projects match the current filters.
            </div>
          ) : (
            projects.map((project) => (
              <div key={project.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 min-w-0">
                    <input
                      type="checkbox"
                      checked={selected.has(project.id)}
                      onChange={() => toggleSelected(project.id)}
                      aria-label={`Select ${project.name}`}
                      className="mt-1 w-3.5 h-3.5 accent-blue-600 shrink-0"
                    />
                    <div className="min-w-0">
                      <div className="font-semibold text-slate-200 truncate flex items-center gap-2">
                        {project.name}
                        {project.pinned && <Pin className="w-3.5 h-3.5 text-amber-400" />}
                      </div>
                      <div className="text-xs font-mono text-slate-500 mt-0.5">{project.id}</div>
                      {project.description && (
                        <div className="text-sm text-slate-400 mt-1">{project.description}</div>
                      )}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleCheck(project.id)}
                    disabled={checkingId === project.id}
                    className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs text-slate-300 transition-colors disabled:opacity-60"
                  >
                    {checkingId === project.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <RefreshCw className="w-3.5 h-3.5" />
                    )}
                    Check Status
                  </button>
                </div>

                <div className="text-xs mt-3 text-slate-500 flex flex-wrap gap-x-4 gap-y-1">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                    {project.status}
                  </span>
                  {(project.tags ?? []).map((tag) => (
                    <span key={tag} className="flex items-center gap-1 rounded bg-slate-800 px-1.5 py-0.5 text-slate-400">
                      <Tag className="w-3 h-3" /> {tag}
                    </span>
                  ))}
                </div>

                <div className="mt-4">
                    <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
                      <span className="flex items-center gap-1.5">
                        {project.current_agent ?? "No agent"} — {project.current_task ?? "Idle"}
                      </span>
                      <span className="font-mono">{project.progress}%</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${project.progress}%` }}
                      />
                    </div>
                </div>

                {statusErrors.has(project.id) && (
                  <div className="mt-3 text-xs text-red-400">Failed to fetch status. Backend may be waking up.</div>
                )}

                <button
                  type="button"
                  onClick={() => openDetails(project)}
                  className="mt-4 flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300"
                >
                  <ChevronDown className={`w-3.5 h-3.5 transition-transform ${expanded === project.id ? "rotate-180" : ""}`} />
                  {expanded === project.id ? "Hide details" : "Details & metadata"}
                </button>

                {expanded === project.id && (
                  <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/60 p-4 space-y-4">
                    <div className="grid grid-cols-2 gap-3 text-[11px]">
                      <div><span className="text-slate-500">Created</span><div className="text-slate-300">{project.created_at ? new Date(project.created_at).toLocaleString() : "—"}</div></div>
                      <div><span className="text-slate-500">Updated</span><div className="text-slate-300">{project.updated_at ? new Date(project.updated_at).toLocaleString() : "—"}</div></div>
                      <div className="col-span-2"><span className="text-slate-500">Repository</span><div className="text-slate-300 truncate">{project.repo_url ?? "—"}</div></div>
                      <div><span className="text-slate-500">Template</span><div className="text-slate-300">{project.template_id ?? "—"}</div></div>
                      <div><span className="text-slate-500">Status</span><div className="text-slate-300">{project.status}</div></div>
                    </div>
                    <div className="flex items-end gap-2">
                      <div className="flex-1">
                        <label className="block text-[11px] text-slate-500 mb-1">Tags (comma separated)</label>
                        <input
                          value={tagDraft}
                          onChange={(event) => setTagDraft(event.target.value)}
                          className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-[11px] text-slate-200 outline-none focus:border-blue-600"
                        />
                      </div>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void updateMeta(project.id, { tags: parseTags(tagDraft) })}
                        className="rounded bg-blue-600 px-2.5 py-1.5 text-[11px] text-white disabled:opacity-50"
                      >
                        Save tags
                      </button>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void updateMeta(project.id, { pinned: !project.pinned })}
                        className="rounded bg-slate-800 px-2.5 py-1.5 text-[11px] text-slate-300 disabled:opacity-50"
                      >
                        {project.pinned ? "Unpin" : "Pin"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </section>
      </div>
    </div>
  );
}
