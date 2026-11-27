"use client";

import { useCallback, useEffect, useState } from "react";
import {
  History,
  KeyRound,
  Loader2,
  RefreshCw,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import {
  getSecretAudit,
  listRepositories,
  listSecrets,
  revokeSecret,
  saveSecret,
} from "@/lib/api";
import { useAuthSession } from "@/lib/use-auth-session";
import type {
  RepositoryOut,
  SecretAuditOut,
  SecretOut,
  SecretScope,
} from "@/lib/types";

const SCOPES: SecretScope[] = ["repository", "environment", "user"];

function formatTime(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export default function SecretsPage() {
  const { session, loading: authLoading } = useAuthSession();
  const [secrets, setSecrets] = useState<SecretOut[]>([]);
  const [repositories, setRepositories] = useState<RepositoryOut[]>([]);
  const [audits, setAudits] = useState<Record<string, SecretAuditOut[]>>({});
  const [form, setForm] = useState({
    name: "",
    value: "",
    scope: "repository" as SecretScope,
    repository_id: "",
    environment: "",
    description: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const [secretResult, repoResult] = await Promise.allSettled([
      listSecrets(),
      listRepositories(),
    ]);
    if (secretResult.status === "fulfilled") setSecrets(secretResult.value.secrets);
    else setError(secretResult.reason instanceof Error ? secretResult.reason.message : "Failed to load secrets");
    if (repoResult.status === "fulfilled") setRepositories(repoResult.value.repositories);
    setLoading(false);
  }, []);

  useEffect(() => {
    if (authLoading || !session) return;
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [authLoading, session, load]);

  const repoName = (id: string | null | undefined) =>
    repositories.find((repo) => repo.id === id)?.full_name ?? id ?? "All repositories";

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      await saveSecret({
        name: form.name.trim(),
        value: form.value,
        scope: form.scope,
        repository_id: form.scope === "user" ? undefined : form.repository_id || undefined,
        environment: form.scope === "environment" ? form.environment.trim() : undefined,
        description: form.description.trim(),
      });
      setForm((current) => ({ ...current, name: "", value: "", description: "" }));
      setNotice("Secret stored securely. Its value cannot be read back from the UI.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to store secret");
    } finally {
      setSaving(false);
    }
  };

  const revoke = async (secretId: string) => {
    setBusyId(secretId);
    setError(null);
    try {
      await revokeSecret(secretId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke secret");
    } finally {
      setBusyId(null);
    }
  };

  const toggleAudit = async (secretId: string) => {
    if (audits[secretId]) {
      setAudits((current) => {
        const next = { ...current };
        delete next[secretId];
        return next;
      });
      return;
    }
    setBusyId(secretId);
    try {
      const result = await getSecretAudit(secretId);
      setAudits((current) => ({ ...current, [secretId]: result.entries }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <KeyRound className="h-6 w-6 text-blue-400" /> Secrets Vault
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Versioned, encrypted secrets. Plaintext is never returned after it is saved.
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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="rounded-xl border border-slate-800 bg-slate-900 p-6 lg:col-span-1">
          <h2 className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-200">
            <ShieldCheck className="h-4 w-4 text-emerald-400" /> Add or rotate a secret
          </h2>
          <form onSubmit={save} className="space-y-3">
            <input
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="NAME_like_this"
              required
              pattern="[A-Za-z0-9_]+"
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 font-mono text-xs text-slate-200 focus:border-blue-700 focus:outline-none"
            />
            <input
              type="password"
              value={form.value}
              onChange={(event) => setForm({ ...form, value: event.target.value })}
              placeholder="Secret value"
              required
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-200 focus:border-blue-700 focus:outline-none"
            />
            <select
              value={form.scope}
              onChange={(event) => setForm({ ...form, scope: event.target.value as SecretScope })}
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-200 focus:border-blue-700 focus:outline-none"
            >
              {SCOPES.map((scope) => (
                <option key={scope} value={scope}>
                  {scope} scoped
                </option>
              ))}
            </select>
            {form.scope !== "user" && (
              <select
                value={form.repository_id}
                onChange={(event) => setForm({ ...form, repository_id: event.target.value })}
                required
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-200 focus:border-blue-700 focus:outline-none"
              >
                <option value="">Select repository…</option>
                {repositories.map((repo) => (
                  <option key={repo.id} value={repo.id}>
                    {repo.full_name}
                  </option>
                ))}
              </select>
            )}
            {form.scope === "environment" && (
              <input
                value={form.environment}
                onChange={(event) => setForm({ ...form, environment: event.target.value })}
                placeholder="production"
                required
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-200 focus:border-blue-700 focus:outline-none"
              />
            )}
            <input
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              placeholder="Description (optional)"
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-200 focus:border-blue-700 focus:outline-none"
            />
            <button
              type="submit"
              disabled={saving}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-60"
            >
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <KeyRound className="h-3.5 w-3.5" />}
              Store secret
            </button>
          </form>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900 p-6 lg:col-span-2">
          <h2 className="mb-5 text-sm font-semibold text-slate-200">
            Stored secrets <span className="text-slate-600">({secrets.length})</span>
          </h2>
          {loading && secrets.length === 0 ? (
            <div className="flex justify-center py-16 text-slate-500">
              <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            </div>
          ) : secrets.length === 0 ? (
            <p className="text-xs text-slate-500">No secrets stored yet.</p>
          ) : (
            <div className="space-y-3">
              {secrets.map((secret) => (
                <div key={secret.id} className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-sm font-semibold text-slate-100">{secret.name}</span>
                        <span className="rounded-full border border-slate-700 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
                          {secret.scope}
                        </span>
                        {secret.revoked_at && (
                          <span className="rounded-full border border-red-800/60 bg-red-950/30 px-2 py-0.5 text-[10px] text-red-400">
                            revoked
                          </span>
                        )}
                      </div>
                      <div className="mt-2 space-y-0.5 text-[11px] text-slate-500">
                        <div className="truncate">Scope target: {repoName(secret.repository_id)}</div>
                        {secret.environment && <div>Environment: {secret.environment}</div>}
                        <div className="font-mono">Fingerprint: {secret.fingerprint}</div>
                        <div>Version {secret.version} · updated {formatTime(secret.updated_at)}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => void toggleAudit(secret.id)}
                        disabled={busyId === secret.id}
                        className="flex items-center gap-1 rounded-lg border border-slate-800 px-2 py-1.5 text-[11px] text-slate-400 hover:border-blue-800 hover:text-blue-300 disabled:opacity-60"
                      >
                        <History className="h-3.5 w-3.5" /> Audit
                      </button>
                      <button
                        type="button"
                        onClick={() => void revoke(secret.id)}
                        disabled={busyId === secret.id || Boolean(secret.revoked_at)}
                        className="flex items-center gap-1 rounded-lg border border-red-900/60 px-2 py-1.5 text-[11px] text-red-400 hover:bg-red-950/30 disabled:opacity-50"
                      >
                        <Trash2 className="h-3.5 w-3.5" /> Revoke
                      </button>
                    </div>
                  </div>
                  {audits[secret.id] && (
                    <div className="mt-4 space-y-1 border-t border-slate-800 pt-3">
                      {audits[secret.id].length === 0 ? (
                        <div className="text-[11px] text-slate-600">No access recorded.</div>
                      ) : (
                        audits[secret.id].map((entry) => (
                          <div key={entry.id} className="flex justify-between gap-3 font-mono text-[10px] text-slate-500">
                            <span className="text-slate-300">{entry.action}</span>
                            <span className="truncate">{entry.purpose}</span>
                            <span>{formatTime(entry.created_at)}</span>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
