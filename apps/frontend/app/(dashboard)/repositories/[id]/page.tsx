"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Braces,
  CheckCircle2,
  FileCode2,
  GitBranch,
  GitCompare,
  GitPullRequest,
  History,
  KeyRound,
  Loader2,
  LockKeyhole,
  RefreshCw,
  Save,
  ShieldCheck,
  Users,
} from "lucide-react";
import {
  applyRepoConfig,
  compareRefs,
  createBranch,
  createPull,
  getFile,
  getRepository,
  getRepoConfig,
  grantRepoPermission,
  listBranches,
  listFiles,
  listRepoAudit,
  listRepoPermissions,
  listRepoTemplates,
  listPulls,
  mergePull,
  previewRepoConfig,
  revokeRepoPermission,
  updatePull,
  writeFile,
} from "@/lib/api";
import { useAuthSession } from "@/lib/use-auth-session";
import { useIsAdmin } from "@/lib/use-admin";
import type {
  AgentMode,
  BranchOut,
  CompareOut,
  ConfigPreviewOut,
  FileOut,
  PullOut,
  RepoAuditOut,
  RepoConfig,
  RepoRoleOut,
  RepositoryOut,
  TemplateOut,
  TreeEntryOut,
} from "@/lib/types";

type Tab = "overview" | "files" | "customization" | "pulls" | "audit";

const TABS: { id: Tab; label: string; icon: typeof GitBranch }[] = [
  { id: "overview", label: "Overview", icon: GitBranch },
  { id: "files", label: "Files", icon: FileCode2 },
  { id: "customization", label: "Customization", icon: Braces },
  { id: "pulls", label: "Pull requests", icon: GitPullRequest },
  { id: "audit", label: "Audit & access", icon: History },
];

const MODES: AgentMode[] = ["Autonomous", "AI-Man", "Manual"];

function splitList(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseObject(text: string): Record<string, string> {
  try {
    const parsed = JSON.parse(text || "{}") as unknown;
    return parsed && typeof parsed === "object" && !Array.isArray(parsed)
      ? Object.fromEntries(
          Object.entries(parsed).map(([key, value]) => [key, String(value)])
        )
      : {};
  } catch {
    return {};
  }
}

function formatTime(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export default function RepositoryWorkspacePage() {
  const params = useParams<{ id: string }>();
  const repositoryId = typeof params.id === "string" ? params.id : "";
  const { session, loading: authLoading } = useAuthSession();
  const isAdmin = useIsAdmin(Boolean(session));

  const [tab, setTab] = useState<Tab>("overview");
  const [repository, setRepository] = useState<RepositoryOut | null>(null);
  const [branches, setBranches] = useState<BranchOut[]>([]);
  const [pulls, setPulls] = useState<PullOut[]>([]);
  const [tree, setTree] = useState<TreeEntryOut[]>([]);
  const [audit, setAudit] = useState<RepoAuditOut[]>([]);
  const [roles, setRoles] = useState<RepoRoleOut[]>([]);
  const [templates, setTemplates] = useState<TemplateOut[]>([]);
  const [diff, setDiff] = useState<CompareOut | null>(null);
  const [preview, setPreview] = useState<ConfigPreviewOut | null>(null);
  const [config, setConfig] = useState<RepoConfig>({
    version: 1,
    agent_mode: "AI-Man",
    branch_protection: false,
  });
  const [configYaml, setConfigYaml] = useState("");
  const [selectedPath, setSelectedPath] = useState("");
  const [file, setFile] = useState<FileOut | null>(null);
  const [draft, setDraft] = useState("");
  const [commitMessage, setCommitMessage] = useState("Update via Advanced Code Garage");
  const [newBranch, setNewBranch] = useState("");
  const [prForm, setPrForm] = useState({ title: "", head: "", base: "", body: "" });
  const [compareForm, setCompareForm] = useState({ base: "", head: "" });
  const [permissionForm, setPermissionForm] = useState({ user_id: "", role: "read" });
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadCore = useCallback(async () => {
    if (!repositoryId) return;
    setBusy(true);
    const results = await Promise.allSettled([
      getRepository(repositoryId),
      getRepoConfig(repositoryId),
      listBranches(repositoryId),
      listPulls(repositoryId),
      listRepoTemplates(repositoryId),
      listRepoAudit(repositoryId),
    ]);
    if (results[0].status === "fulfilled") setRepository(results[0].value);
    if (results[1].status === "fulfilled") {
      setConfig(results[1].value.config);
      setConfigYaml(results[1].value.yaml);
    }
    if (results[2].status === "fulfilled") {
      const branches = results[2].value.branches;
      setBranches(branches);
      const defaultBranch = branches.find((branch) => branch.protected)?.name ?? "";
      setCompareForm((current) => ({
        base: current.base || defaultBranch,
        head: current.head || defaultBranch,
      }));
      setPrForm((current) => ({ ...current, base: current.base || defaultBranch }));
    }
    if (results[3].status === "fulfilled") setPulls(results[3].value.pulls);
    if (results[4].status === "fulfilled") setTemplates(results[4].value.templates);
    if (results[5].status === "fulfilled") setAudit(results[5].value.entries);
    const failed = results.find((result) => result.status === "rejected");
    if (failed && failed.status === "rejected") {
      setError(failed.reason instanceof Error ? failed.reason.message : "Failed to load repository");
    } else {
      setError(null);
    }
    setBusy(false);
  }, [repositoryId]);

  useEffect(() => {
    if (authLoading || !session) return;
    const timer = window.setTimeout(() => void loadCore(), 0);
    return () => window.clearTimeout(timer);
  }, [authLoading, session, loadCore]);

  const loadFiles = useCallback(async () => {
    if (!repositoryId) return;
    const result = await listFiles(repositoryId);
    setTree(result.entries);
  }, [repositoryId]);

  const loadRoles = useCallback(async () => {
    if (!repositoryId || !isAdmin) return;
    const result = await listRepoPermissions(repositoryId);
    setRoles(result.entries);
  }, [repositoryId, isAdmin]);

  const openFile = async (path: string) => {
    setBusy(true);
    try {
      const result = await getFile(repositoryId, path);
      setFile(result);
      setDraft(result.content);
      setSelectedPath(path);
      setNotice(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to read file");
    } finally {
      setBusy(false);
    }
  };

  const saveFile = async () => {
    if (!file) return;
    setBusy(true);
    setNotice(null);
    try {
      const result = await writeFile(repositoryId, {
        path: selectedPath,
        content: draft,
        message: commitMessage,
        branch: file.branch,
        sha: file.sha,
        idempotency_key: crypto.randomUUID(),
      });
      setNotice(`Committed ${result.commit_sha.slice(0, 8) || "change"}.`);
      await openFile(selectedPath);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to commit file");
    } finally {
      setBusy(false);
    }
  };

  const addBranch = async () => {
    if (!newBranch.trim()) return;
    setBusy(true);
    try {
      await createBranch(repositoryId, { name: newBranch.trim() });
      setNotice(`Branch ${newBranch.trim()} created.`);
      setNewBranch("");
      await loadCore();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create branch");
    } finally {
      setBusy(false);
    }
  };

  const updateConfigField = <K extends keyof RepoConfig>(key: K, value: RepoConfig[K]) => {
    setConfig((current) => ({ ...current, [key]: value }));
    setPreview(null);
  };

  const showPreview = async () => {
    setBusy(true);
    try {
      const result = await previewRepoConfig(repositoryId, {
        config,
        branch: "",
        message: "Update .acg/config.yaml",
      });
      setPreview(result);
      setNotice(result.changed ? "Review the diff before applying." : "No changes to apply.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to preview config");
    } finally {
      setBusy(false);
    }
  };

  const applyConfig = async () => {
    setBusy(true);
    try {
      const result = await applyRepoConfig(repositoryId, {
        config,
        branch: "",
        message: "Update .acg/config.yaml",
        idempotency_key: crypto.randomUUID(),
      });
      setNotice(`Configuration committed in ${result.commit_sha.slice(0, 8) || "a new commit"}.`);
      setPreview(null);
      await loadCore();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to apply config");
    } finally {
      setBusy(false);
    }
  };

  const submitPull = async () => {
    setBusy(true);
    try {
      await createPull(repositoryId, {
        title: prForm.title,
        head: prForm.head,
        base: prForm.base,
        body: prForm.body,
        draft: false,
        idempotency_key: crypto.randomUUID(),
      });
      setNotice("Pull request created.");
      setPrForm({ title: "", head: "", base: "", body: "" });
      await loadCore();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create pull request");
    } finally {
      setBusy(false);
    }
  };

  const runCompare = async () => {
    setBusy(true);
    try {
      setDiff(await compareRefs(repositoryId, compareForm.base, compareForm.head));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to compare refs");
    } finally {
      setBusy(false);
    }
  };

  const reviewPull = async (pull: PullOut, state: "open" | "closed") => {
    setBusy(true);
    try {
      await updatePull(repositoryId, pull.number, { state });
      await loadCore();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update pull request");
    } finally {
      setBusy(false);
    }
  };

  const doMerge = async (pull: PullOut) => {
    setBusy(true);
    try {
      const result = await mergePull(repositoryId, pull.number, {
        idempotency_key: crypto.randomUUID(),
      });
      setNotice(result.merged ? `Merged as ${result.sha.slice(0, 8)}.` : result.message);
      await loadCore();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to merge pull request");
    } finally {
      setBusy(false);
    }
  };

  const grant = async () => {
    if (!permissionForm.user_id.trim()) return;
    setBusy(true);
    try {
      await grantRepoPermission(repositoryId, {
        user_id: permissionForm.user_id.trim(),
        role: permissionForm.role as "owner" | "write" | "read",
      });
      setPermissionForm({ user_id: "", role: "read" });
      await loadRoles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to grant access");
    } finally {
      setBusy(false);
    }
  };

  const revoke = async (userId: string) => {
    setBusy(true);
    try {
      await revokeRepoPermission(repositoryId, userId);
      await loadRoles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke access");
    } finally {
      setBusy(false);
    }
  };

  if (!repositoryId) {
    return <div className="text-sm text-red-400">Missing repository id.</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            href="/repositories"
            className="mb-2 inline-flex items-center gap-1 text-xs text-slate-500 hover:text-blue-400"
          >
            <ArrowLeft className="h-3 w-3" /> Repositories
          </Link>
          <h1 className="flex items-center gap-2 font-mono text-2xl font-bold text-slate-100">
            <GitBranch className="h-6 w-6 text-blue-400" />
            {repository?.full_name ?? repositoryId}
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            {repository?.private ? "Private" : "Public"} repository · default branch{" "}
            {repository?.default_branch ?? "main"}
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            void loadCore();
            if (tab === "files") void loadFiles();
            if (tab === "audit") void loadRoles();
          }}
          disabled={busy}
          className="flex items-center gap-2 rounded-lg bg-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 disabled:opacity-60"
        >
          {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-800/60 bg-red-950/30 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}
      {notice && (
        <div className="rounded-lg border border-emerald-800/60 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-300">
          {notice}
        </div>
      )}

      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-2">
        {TABS.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                setTab(item.id);
                if (item.id === "files") void loadFiles();
                if (item.id === "audit") void loadRoles();
              }}
              className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs transition ${
                tab === item.id
                  ? "bg-blue-600/20 text-blue-300"
                  : "text-slate-500 hover:bg-slate-900 hover:text-slate-300"
              }`}
            >
              <Icon className="h-3.5 w-3.5" /> {item.label}
            </button>
          );
        })}
      </div>

      {tab === "overview" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-200">
              <GitBranch className="h-4 w-4 text-emerald-400" /> Branches
            </h2>
            <div className="mb-4 flex gap-2">
              <input
                value={newBranch}
                onChange={(event) => setNewBranch(event.target.value)}
                placeholder="new-branch-name"
                className="min-w-0 flex-1 rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 font-mono text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => void addBranch()}
                className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500"
              >
                Create
              </button>
            </div>
            <div className="space-y-1.5">
              {branches.length === 0 ? (
                <p className="text-xs text-slate-600">No branches returned.</p>
              ) : (
                branches.map((branch) => (
                  <div
                    key={branch.name}
                    className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2"
                  >
                    <span className="truncate font-mono text-xs text-slate-200">{branch.name}</span>
                    <span className="font-mono text-[10px] text-slate-600">
                      {branch.protected ? "protected" : branch.sha.slice(0, 7)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </section>

          <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-200">
              <GitCompare className="h-4 w-4 text-blue-400" /> Compare refs
            </h2>
            <div className="grid grid-cols-2 gap-2">
              <input
                value={compareForm.base}
                onChange={(event) => setCompareForm({ ...compareForm, base: event.target.value })}
                placeholder="base"
                className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 font-mono text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
              />
              <input
                value={compareForm.head}
                onChange={(event) => setCompareForm({ ...compareForm, head: event.target.value })}
                placeholder="head"
                className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 font-mono text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
              />
            </div>
            <button
              type="button"
              onClick={() => void runCompare()}
              className="mt-3 rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-blue-700 hover:text-blue-300"
            >
              Compare
            </button>
            {diff && (
              <div className="mt-4 space-y-2">
                <div className="text-[11px] text-slate-500">
                  {diff.total_commits} commits · +{diff.ahead_by} / -{diff.behind_by}
                </div>
                {diff.files.length === 0 && (
                  <p className="text-xs text-slate-600">No file differences.</p>
                )}
                {diff.files.map((fileChange) => (
                  <div key={fileChange.filename} className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                    <div className="flex justify-between gap-2 font-mono text-[11px] text-slate-300">
                      <span className="truncate">{fileChange.filename}</span>
                      <span className="text-emerald-500">
                        +{fileChange.additions} / <span className="text-red-400">-{fileChange.deletions}</span>
                      </span>
                    </div>
                    {fileChange.patch && (
                      <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap font-mono text-[10px] text-slate-500">
                        {fileChange.patch}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {tab === "files" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <h2 className="mb-3 text-sm font-semibold text-slate-200">Repository tree</h2>
            <div className="max-h-[70vh] space-y-1 overflow-auto">
              {tree.length === 0 ? (
                <p className="text-xs text-slate-600">No files loaded.</p>
              ) : (
                tree
                  .filter((entry) => entry.type === "blob")
                  .map((entry) => (
                    <button
                      key={entry.path}
                      type="button"
                      onClick={() => void openFile(entry.path)}
                      className={`block w-full truncate rounded px-2 py-1.5 text-left font-mono text-[11px] ${
                        selectedPath === entry.path
                          ? "bg-blue-600/20 text-blue-300"
                          : "text-slate-400 hover:bg-slate-800"
                      }`}
                    >
                      {entry.path}
                    </button>
                  ))
              )}
            </div>
          </section>
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-5 lg:col-span-2">
            {!file ? (
              <div className="flex h-64 flex-col items-center justify-center gap-2 text-slate-600">
                <FileCode2 className="h-8 w-8" />
                <p className="text-xs">Select a file to view and edit it.</p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="font-mono text-sm text-slate-200">{selectedPath}</div>
                  <span className="text-[10px] text-slate-600">
                    {file.size} bytes · {file.branch}
                  </span>
                </div>
                <textarea
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  spellCheck={false}
                  className="h-96 w-full rounded-lg border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
                />
                <div className="flex flex-wrap gap-2">
                  <input
                    value={commitMessage}
                    onChange={(event) => setCommitMessage(event.target.value)}
                    className="min-w-0 flex-1 rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => void saveFile()}
                    disabled={busy}
                    className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-60"
                  >
                    <Save className="h-3.5 w-3.5" /> Commit
                  </button>
                </div>
                {file.truncated && (
                  <p className="text-[10px] text-amber-500">
                    This file was truncated in the editor. Committing it would shorten it.
                  </p>
                )}
              </div>
            )}
          </section>
        </div>
      )}

      {tab === "customization" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-6 lg:col-span-2">
            <h2 className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Braces className="h-4 w-4 text-blue-400" /> .acg/config.yaml
            </h2>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="space-y-1">
                <span className="text-[11px] text-slate-500">Agent mode</span>
                <select
                  value={config.agent_mode}
                  onChange={(event) => updateConfigField("agent_mode", event.target.value as AgentMode)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
                >
                  {MODES.map((mode) => (
                    <option key={mode} value={mode}>
                      {mode}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex items-center gap-2 self-end pb-2 text-xs text-slate-300">
                <input
                  type="checkbox"
                  checked={config.branch_protection}
                  onChange={(event) => updateConfigField("branch_protection", event.target.checked)}
                  className="h-3.5 w-3.5 accent-blue-600"
                />
                Require branch protection
              </label>
              <label className="space-y-1 sm:col-span-2">
                <span className="text-[11px] text-slate-500">Allowed providers (comma separated)</span>
                <input
                  value={(config.allowed_providers ?? []).join(", ")}
                  onChange={(event) => updateConfigField("allowed_providers", splitList(event.target.value))}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
                />
              </label>
              <label className="space-y-1">
                <span className="text-[11px] text-slate-500">Review rules (one per line)</span>
                <textarea
                  value={(config.review_rules ?? []).join("\n")}
                  onChange={(event) => updateConfigField("review_rules", splitList(event.target.value))}
                  rows={3}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
                />
              </label>
              <label className="space-y-1">
                <span className="text-[11px] text-slate-500">Required checks (one per line)</span>
                <textarea
                  value={(config.required_checks ?? []).join("\n")}
                  onChange={(event) => updateConfigField("required_checks", splitList(event.target.value))}
                  rows={3}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
                />
              </label>
              <label className="space-y-1">
                <span className="text-[11px] text-slate-500">Deployment targets (comma separated)</span>
                <input
                  value={(config.deployment_targets ?? []).join(", ")}
                  onChange={(event) => updateConfigField("deployment_targets", splitList(event.target.value))}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
                />
              </label>
              <label className="space-y-1">
                <span className="text-[11px] text-slate-500">Secret bindings (JSON, names only)</span>
                <input
                  value={JSON.stringify(config.secret_bindings ?? {})}
                  onChange={(event) => updateConfigField("secret_bindings", parseObject(event.target.value))}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 font-mono text-[11px] text-slate-200 focus:border-blue-700 focus:outline-none"
                />
              </label>
              <label className="space-y-1 sm:col-span-2">
                <span className="text-[11px] text-slate-500">Custom commands (JSON)</span>
                <textarea
                  value={JSON.stringify(config.custom_commands ?? {}, null, 2)}
                  onChange={(event) => updateConfigField("custom_commands", parseObject(event.target.value))}
                  rows={3}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 font-mono text-[11px] text-slate-200 focus:border-blue-700 focus:outline-none"
                />
              </label>
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void showPreview()}
                className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-blue-700 hover:text-blue-300"
              >
                <GitCompare className="h-3.5 w-3.5" /> Preview diff
              </button>
              <button
                type="button"
                onClick={() => void applyConfig()}
                disabled={busy || !preview?.changed}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-50"
              >
                <CheckCircle2 className="h-3.5 w-3.5" /> Commit config
              </button>
            </div>

            {preview && (
              <pre className="mt-4 max-h-72 overflow-auto rounded-lg border border-slate-800 bg-slate-950 p-3 font-mono text-[10px] text-slate-400">
                {preview.diff || "No changes."}
              </pre>
            )}
          </section>

          <section className="space-y-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
              <h2 className="mb-3 text-sm font-semibold text-slate-200">Templates</h2>
              <div className="space-y-2">
                {templates.length === 0 ? (
                  <p className="text-xs text-slate-600">No templates available.</p>
                ) : (
                  templates.map((template) => (
                    <button
                      key={template.id}
                      type="button"
                      onClick={() => {
                        setConfig(template.config);
                        setPreview(null);
                        setNotice(`Loaded ${template.name}. Preview before committing.`);
                      }}
                      className="block w-full rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2 text-left hover:border-blue-800"
                    >
                      <div className="text-xs text-slate-200">{template.name}</div>
                      <div className="mt-1 text-[10px] text-slate-500">{template.description}</div>
                    </button>
                  ))
                )}
              </div>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
              <h2 className="mb-2 text-sm font-semibold text-slate-200">Current file on disk</h2>
              <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-950 p-3 font-mono text-[10px] text-slate-500">
                {configYaml || "(not present)"}
              </pre>
            </div>
          </section>
        </div>
      )}

      {tab === "pulls" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-6 lg:col-span-2">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-200">
              <GitPullRequest className="h-4 w-4 text-blue-400" /> Open pull requests
            </h2>
            {pulls.length === 0 ? (
              <p className="text-xs text-slate-600">No open pull requests.</p>
            ) : (
              <div className="space-y-3">
                {pulls.map((pull) => (
                  <div key={pull.number} className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="text-sm text-slate-100">
                          <span className="mr-2 font-mono text-xs text-slate-500">#{pull.number}</span>
                          {pull.title}
                        </div>
                        <div className="mt-1 font-mono text-[10px] text-slate-500">
                          {pull.head} → {pull.base}
                        </div>
                      </div>
                      <div className="flex gap-1.5">
                        <a
                          href={pull.url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded-lg border border-slate-800 px-2 py-1 text-[10px] text-slate-400 hover:text-blue-300"
                        >
                          View
                        </a>
                        <button
                          type="button"
                          onClick={() => void reviewPull(pull, "closed")}
                          className="rounded-lg border border-slate-800 px-2 py-1 text-[10px] text-slate-400 hover:text-amber-300"
                        >
                          Close
                        </button>
                        <button
                          type="button"
                          onClick={() => void doMerge(pull)}
                          className="rounded-lg bg-emerald-700/40 px-2 py-1 text-[10px] text-emerald-300 hover:bg-emerald-700/60"
                        >
                          Merge
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="mb-4 text-sm font-semibold text-slate-200">New pull request</h2>
            <div className="space-y-3">
              <input
                value={prForm.title}
                onChange={(event) => setPrForm({ ...prForm, title: event.target.value })}
                placeholder="Title"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
              />
              <input
                value={prForm.head}
                onChange={(event) => setPrForm({ ...prForm, head: event.target.value })}
                placeholder="Head branch"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 font-mono text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
              />
              <input
                value={prForm.base}
                onChange={(event) => setPrForm({ ...prForm, base: event.target.value })}
                placeholder="Base branch"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 font-mono text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
              />
              <textarea
                value={prForm.body}
                onChange={(event) => setPrForm({ ...prForm, body: event.target.value })}
                placeholder="Description"
                rows={4}
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => void submitPull()}
                disabled={busy}
                className="w-full rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-60"
              >
                Create pull request
              </button>
            </div>
          </section>
        </div>
      )}

      {tab === "audit" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-6 lg:col-span-2">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-200">
              <History className="h-4 w-4 text-blue-400" /> Operation timeline
            </h2>
            {audit.length === 0 ? (
              <p className="text-xs text-slate-600">No repository operations recorded.</p>
            ) : (
              <div className="space-y-2">
                {audit.map((entry) => (
                  <div key={entry.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2">
                    <div className="min-w-0">
                      <div className="font-mono text-[11px] text-slate-200">{entry.action}</div>
                      <div className="mt-0.5 truncate text-[10px] text-slate-500">
                        {entry.target || "—"} · {entry.request_id || "no request id"}
                      </div>
                    </div>
                    <div className="text-[10px] text-slate-600">{formatTime(entry.created_at)}</div>
                  </div>
                ))}
              </div>
            )}
          </section>
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Users className="h-4 w-4 text-emerald-400" /> Access
            </h2>
            {isAdmin ? (
              <>
                <div className="mb-4 flex gap-2">
                  <input
                    value={permissionForm.user_id}
                    onChange={(event) => setPermissionForm({ ...permissionForm, user_id: event.target.value })}
                    placeholder="User ID"
                    className="min-w-0 flex-1 rounded-lg border border-slate-800 bg-slate-950 px-2 py-1.5 font-mono text-[11px] text-slate-200 focus:border-blue-700 focus:outline-none"
                  />
                  <select
                    value={permissionForm.role}
                    onChange={(event) => setPermissionForm({ ...permissionForm, role: event.target.value })}
                    className="rounded-lg border border-slate-800 bg-slate-950 px-2 py-1.5 text-[11px] text-slate-200 focus:border-blue-700 focus:outline-none"
                  >
                    <option value="read">read</option>
                    <option value="write">write</option>
                    <option value="owner">owner</option>
                  </select>
                  <button
                    type="button"
                    onClick={() => void grant()}
                    className="rounded-lg bg-blue-600 px-2 py-1.5 text-[11px] text-white hover:bg-blue-500"
                  >
                    Grant
                  </button>
                </div>
                <div className="space-y-2">
                  {roles.length === 0 ? (
                    <p className="text-xs text-slate-600">
                      No explicit grants. Only admins can operate this repository.
                    </p>
                  ) : (
                    roles.map((role) => (
                      <div key={`${role.repository_id}-${role.user_id}`} className="flex items-center justify-between gap-2 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2">
                        <div className="min-w-0">
                          <div className="truncate font-mono text-[11px] text-slate-200">{role.user_id}</div>
                          <div className="text-[10px] text-slate-500">{role.role}</div>
                        </div>
                        <button
                          type="button"
                          onClick={() => void revoke(role.user_id)}
                          className="rounded-lg border border-red-900/60 px-2 py-1 text-[10px] text-red-400 hover:bg-red-950/30"
                        >
                          Revoke
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </>
            ) : (
              <div className="flex gap-2 rounded-lg border border-slate-800 bg-slate-950/40 p-3 text-[11px] text-slate-500">
                <LockKeyhole className="h-4 w-4 shrink-0" />
                Ask an admin to grant you access to this repository.
              </div>
            )}
            <div className="mt-5 flex gap-2 border-t border-slate-800 pt-4 text-[10px] text-slate-500">
              <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-500" />
              Tokens stay server-side. Secrets are managed in the{" "}
              <Link href="/secrets" className="text-blue-400 hover:underline">
                vault
              </Link>
              .
            </div>
            <div className="mt-3 flex items-center gap-2 text-[10px] text-slate-500">
              <KeyRound className="h-3.5 w-3.5" /> Secret names in config are references only.
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
