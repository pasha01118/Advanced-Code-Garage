"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Archive,
  ExternalLink,
  FolderGit2,
  GitBranch,
  KeyRound,
  Loader2,
  RefreshCw,
  Search,
  Server,
  ShieldCheck,
} from "lucide-react";
import {
  listGithubInstallations,
  listRepositories,
  syncGithubInstallation,
} from "@/lib/api";
import { useAuthSession } from "@/lib/use-auth-session";
import { useIsAdmin } from "@/lib/use-admin";
import type { InstallationOut, RepositoryOut } from "@/lib/types";

export default function RepositoriesPage() {
  const { session, loading: authLoading } = useAuthSession();
  const isAdmin = useIsAdmin(Boolean(session));
  const [repositories, setRepositories] = useState<RepositoryOut[]>([]);
  const [installations, setInstallations] = useState<InstallationOut[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<number | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [repoResult, installationResult] = await Promise.allSettled([
        listRepositories(),
        isAdmin ? listGithubInstallations() : Promise.resolve(null),
      ]);
      if (repoResult.status === "fulfilled") setRepositories(repoResult.value.repositories);
      else throw repoResult.reason;
      if (installationResult.status === "fulfilled")
        setInstallations(installationResult.value?.installations ?? []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load repositories");
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => {
    if (authLoading || !session) return;
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [authLoading, session, load]);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return repositories;
    return repositories.filter((repo) =>
      `${repo.full_name} ${repo.default_branch}`.toLowerCase().includes(query)
    );
  }, [repositories, search]);

  const sync = async (installationId: number) => {
    setSyncing(installationId);
    setNotice(null);
    try {
      const result = await syncGithubInstallation(installationId);
      setNotice(
        `Synced ${result.total} repositories (${result.repositories_added} new, ${result.repositories_updated} updated).`
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "GitHub sync failed");
    } finally {
      setSyncing(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <FolderGit2 className="h-6 w-6 text-blue-400" /> Repositories
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            GitHub App installations and the repositories available to the swarm.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg bg-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 disabled:opacity-60"
        >
          {loading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="h-3.5 w-3.5" />
          )}
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

      {isAdmin && (
        <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-200">
            <ShieldCheck className="h-4 w-4 text-blue-400" /> GitHub App installations
          </h2>
          {installations.length === 0 ? (
            <p className="text-xs text-slate-500">
              No installation received yet. Install the GitHub App on your account, then a
              webhook delivery will register it automatically.
            </p>
          ) : (
            <div className="space-y-2">
              {installations.map((installation) => (
                <div
                  key={installation.installation_id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-950/40 px-4 py-3"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 text-sm text-slate-200">
                      <Server className="h-4 w-4 text-emerald-400" />
                      <span className="truncate font-mono">{installation.account_login}</span>
                      {installation.suspended && (
                        <span className="rounded bg-red-950/40 px-1.5 py-0.5 text-[10px] text-red-400">
                          suspended
                        </span>
                      )}
                    </div>
                    <div className="mt-1 font-mono text-[11px] text-slate-600">
                      installation {installation.installation_id}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => void sync(installation.installation_id)}
                    disabled={syncing === installation.installation_id}
                    className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-60"
                  >
                    {syncing === installation.installation_id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <RefreshCw className="h-3.5 w-3.5" />
                    )}
                    Sync repositories
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-600" />
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search repositories…"
          className="w-full rounded-lg border border-slate-800 bg-slate-900 py-2 pl-9 pr-3 text-sm text-slate-200 placeholder:text-slate-600 focus:border-blue-700 focus:outline-none"
        />
      </div>

      {loading && repositories.length === 0 ? (
        <div className="flex justify-center py-16 text-slate-500">
          <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-10 text-center text-sm text-slate-500">
          No repositories synced yet.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((repo) => (
            <div key={repo.id} className="rounded-xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate font-mono text-sm font-semibold text-slate-100">
                    {repo.full_name}
                  </div>
                  <div className="mt-1 flex items-center gap-3 text-[11px] text-slate-500">
                    <span className="flex items-center gap-1">
                      <GitBranch className="h-3 w-3" /> {repo.default_branch}
                    </span>
                    <span>{repo.private ? "Private" : "Public"}</span>
                    {(repo.archived || repo.disabled) && (
                      <span className="flex items-center gap-1 text-amber-500">
                        <Archive className="h-3 w-3" /> inactive
                      </span>
                    )}
                  </div>
                </div>
                {repo.html_url && (
                  <a
                    href={repo.html_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-slate-500 hover:text-blue-400"
                    aria-label="Open on GitHub"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>
              <Link
                href="/secrets"
                className="mt-4 inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-1.5 text-xs text-slate-400 hover:border-blue-800 hover:text-blue-300"
              >
                <KeyRound className="h-3.5 w-3.5" /> Manage secrets
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
