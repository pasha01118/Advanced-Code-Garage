"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  Ban,
  Bot,
  Cpu,
  Eye,
  Fingerprint,
  LayoutDashboard,
  Loader2,
  RefreshCw,
  Server,
  ShieldCheck,
  Unlock,
  UserCog,
  Users,
  Wifi,
} from "lucide-react";
import { useAuthSession } from "@/lib/use-auth-session";
import {
  getAppState,
  setAppState,
  setToggle,
  getProviderUsage,
  getSentinelEvents,
  getSentinelDiscussion,
  getSentinelSnapshot,
  runSentinel,
  getSentinelStreamUrl,
  listUsers,
  suspendUser,
  reactivateUser,
  updateAdminAccount,
} from "@/lib/api";
import { subscribeSSE } from "@/lib/stream-sse";
import { useIsAdmin } from "@/lib/use-admin";
import type {
  AppStateOut,
  ProviderUsageOut,
  SentinelEventOut,
  SentinelDiscussionEntryOut,
  UpdateAccountRequest,
  UserRowOut,
} from "@/lib/types";

type Tab = "overview" | "providers" | "sentinel" | "users" | "account";

type ProviderUsage = ProviderUsageOut;
type SentinelEvent = SentinelEventOut;
type SentinelDiscussionEntry = SentinelDiscussionEntryOut;
type UserRow = UserRowOut;

export default function AdminPage() {
  const { session } = useAuthSession();
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [appState, setAppStateState] = useState<AppStateOut | null>(null);
  const [providers, setProviders] = useState<ProviderUsage[]>([]);
  const [sentinelEvents, setSentinelEvents] = useState<SentinelEvent[]>([]);
  const [sentinelDiscussion, setSentinelDiscussion] = useState<SentinelDiscussionEntry[]>([]);
  const [sentinelRunning, setSentinelRunning] = useState(false);
  const [sentinelLastRun, setSentinelLastRun] = useState<string | null | undefined>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<Set<string>>(() => new Set());
  const [accountForm, setAccountForm] = useState<{ email: string; new_password: string }>({ email: "", new_password: "" });
  const [accountMsg, setAccountMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const unsubscribeStreamRef = useRef<(() => void) | null>(null);
  const [sentinelStreamConnected, setSentinelStreamConnected] = useState(false);

  const email = session?.user?.email ?? "";
  const isAdmin = useIsAdmin(Boolean(session));

  const startBusy = (key: string) => setBusy((prev) => new Set(prev).add(key));
  const stopBusy = (key: string) =>
    setBusy((prev) => {
      const next = new Set(prev);
      next.delete(key);
      return next;
    });

  const loadOverview = useCallback(async () => {
    try {
      const state = await getAppState();
      setAppStateState(state);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  const loadProviders = useCallback(async () => {
    try {
      const data = await getProviderUsage();
      setProviders(data.providers);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  const loadSentinel = useCallback(async () => {
    try {
      const [events, discussion, snapshot] = await Promise.all([
        getSentinelEvents(),
        getSentinelDiscussion(),
        getSentinelSnapshot(),
      ]);
      setSentinelEvents(events);
      setSentinelDiscussion(discussion);
      setSentinelRunning(snapshot.running);
      setSentinelLastRun(snapshot.last_run_at);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  const loadUsers = useCallback(async () => {
    try {
      const data = await listUsers();
      setUsers(data.users);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    await Promise.all([loadOverview(), loadProviders(), loadSentinel(), loadUsers()]);
    setLoading(false);
  }, [loadOverview, loadProviders, loadSentinel, loadUsers]);

  useEffect(() => {
    // Do not fire admin-only requests for signed-in non-admins. Defer the load
    // so the effect body itself never sets state synchronously.
    if (!isAdmin) return;
    void Promise.resolve().then(loadAll);
  }, [isAdmin, loadAll]);

  const connectSentinelStream = useCallback(() => {
    if (unsubscribeStreamRef.current) return;
    unsubscribeStreamRef.current = subscribeSSE(getSentinelStreamUrl(), {
      onOpen: () => setSentinelStreamConnected(true),
      onDisconnect: () => setSentinelStreamConnected(false),
      onMessage: (data) => {
        try {
          const payload: unknown = JSON.parse(data);
          if (typeof payload !== "object" || payload === null) return;
          const message = payload as { type?: unknown; data?: unknown };
          const item = message.data;
          if (message.type === "event" && item && typeof item === "object") {
            setSentinelEvents((prev) => [item as SentinelEvent, ...prev].slice(0, 100));
          } else if (message.type === "discussion" && item && typeof item === "object") {
            setSentinelDiscussion((prev) => [item as SentinelDiscussionEntry, ...prev].slice(0, 100));
          } else if (message.type === "heal" && item && typeof item === "object") {
            const healed = item as { id?: unknown; report?: unknown };
            if (typeof healed.id !== "string") return;
            setSentinelEvents((prev) =>
              prev.map((e) =>
                e.id === healed.id
                  ? {
                      ...e,
                      status: "auto_fixed",
                      auto_fix_report: typeof healed.report === "string" ? healed.report : e.auto_fix_report,
                    }
                  : e
              )
            );
          }
        } catch {
          // ignore parse errors
        }
      },
    });
  }, []);

  const disconnectSentinelStream = useCallback(() => {
    if (unsubscribeStreamRef.current) {
      unsubscribeStreamRef.current();
      unsubscribeStreamRef.current = null;
      setSentinelStreamConnected(false);
    }
  }, []);

  useEffect(() => {
    if (!isAdmin || activeTab !== "sentinel") return;
    connectSentinelStream();
    return () => disconnectSentinelStream();
  }, [isAdmin, activeTab, connectSentinelStream, disconnectSentinelStream]);

  async function handleToggleChange(name: string, enabled: boolean) {
    const key = `toggle-${name}`;
    startBusy(key);
    try {
      const state = await setToggle(name, enabled);
      setAppStateState(state);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      stopBusy(key);
    }
  }

  async function handleStatusChange(status: "running" | "maintenance" | "shutdown") {
    startBusy("status");
    try {
      const state = await setAppState({ status, message: "" });
      setAppStateState(state);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      stopBusy("status");
    }
  }

  async function handleRunSentinel() {
    startBusy("sentinel-run");
    try {
      await runSentinel();
      await loadSentinel();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      stopBusy("sentinel-run");
    }
  }

  async function handleSuspend(userId: string) {
    const input = prompt("Suspend duration (minutes):", "60");
    if (input === null) return;
    const minutes = Number(input);
    if (!Number.isInteger(minutes) || minutes < 1 || minutes > 525600) {
      setError("Suspend duration must be a whole number between 1 and 525600 minutes.");
      return;
    }
    const key = `suspend-${userId}`;
    startBusy(key);
    try {
      await suspendUser(userId, minutes);
      await loadUsers();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      stopBusy(key);
    }
  }

  async function handleReactivate(userId: string) {
    if (!confirm("Reactivate this user?")) return;
    const key = `reactivate-${userId}`;
    startBusy(key);
    try {
      await reactivateUser(userId);
      await loadUsers();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      stopBusy(key);
    }
  }

  async function handleAccountSubmit(e: React.FormEvent) {
    e.preventDefault();
    startBusy("account");
    setAccountMsg(null);
    try {
      const payload: UpdateAccountRequest = {
        email: accountForm.email.trim() || null,
        new_password: accountForm.new_password || null,
      };
      const res = await updateAdminAccount(payload);
      setAccountMsg({ type: "success", text: res.message });
      setAccountForm({ email: "", new_password: "" });
    } catch (e) {
      setAccountMsg({ type: "error", text: (e as Error).message });
    } finally {
      stopBusy("account");
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case "running": return "text-green-400 bg-green-900/30 border-green-700/50";
      case "maintenance": return "text-yellow-400 bg-yellow-900/30 border-yellow-700/50";
      case "shutdown": return "text-red-400 bg-red-900/30 border-red-700/50";
      default: return "text-slate-400 bg-slate-900/30 border-slate-700/50";
    }
  }

  function getSeverityColor(severity: string) {
    switch (severity) {
      case "error": return "text-red-400 bg-red-900/30 border-red-700/50";
      case "warn": return "text-yellow-400 bg-yellow-900/30 border-yellow-700/50";
      case "info": return "text-blue-400 bg-blue-900/30 border-blue-700/50";
      default: return "text-slate-400 bg-slate-900/30 border-slate-700/50";
    }
  }

  function getProviderStatusColor(status: string) {
    switch (status) {
      case "active": return "text-green-400 bg-green-900/30 border-green-700/50";
      case "quota": return "text-yellow-400 bg-yellow-900/30 border-yellow-700/50";
      case "error": return "text-red-400 bg-red-900/30 border-red-700/50";
      case "untested": return "text-slate-400 bg-slate-900/30 border-slate-700/50";
      default: return "text-slate-400 bg-slate-900/30 border-slate-700/50";
    }
  }

  if (!isAdmin) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="bg-slate-900 border border-red-900/60 rounded-xl p-8 max-w-md text-center">
          <ShieldCheck className="w-12 h-12 mx-auto mb-4 text-red-500" />
          <h2 className="text-xl font-bold mb-2">Access Restricted</h2>
          <p className="text-sm text-slate-400">
            This control panel requires admin privileges (RBAC). Signed in as{" "}
            <span className="font-mono text-slate-300">{email || "(no session)"}</span>.
          </p>
        </div>
      </div>
    );
  }

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "overview", label: "Overview", icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: "providers", label: "Providers", icon: <Server className="w-4 h-4" /> },
    { id: "sentinel", label: "Sentinel", icon: <Bot className="w-4 h-4" /> },
    { id: "users", label: "Users", icon: <Users className="w-4 h-4" /> },
    { id: "account", label: "Account", icon: <UserCog className="w-4 h-4" /> },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Fingerprint className="w-6 h-6 text-red-400" /> Admin Control Panel
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Operational state, feature toggles, provider health, sentinel self-healing, and user management.
        </p>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700/50 text-red-300 rounded-lg p-3 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} aria-label="Dismiss error" className="text-red-400 hover:text-red-300">×</button>
        </div>
      )}

      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? "bg-blue-600/15 text-blue-400 border border-blue-700/40"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (
        <div className="space-y-6">
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-blue-400" /> Operational State
            </h2>
            {appState && (
              <>
                <div className="mb-6">
                  <label className="block text-sm text-slate-400 mb-2">Status</label>
                  <div className="flex flex-wrap gap-2">
                    {(["running", "maintenance", "shutdown"] as const).map((s) => (
                      <button
                        key={s}
                        onClick={() => handleStatusChange(s)}
                        aria-label={`Set status to ${s}`}
                        aria-pressed={appState.status === s}
                        disabled={busy.has("status")}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${
                          appState.status === s ? getStatusColor(s) : "text-slate-400 border-slate-700/50 hover:border-slate-600"
                        } disabled:opacity-60`}
                      >
                        {s.charAt(0).toUpperCase() + s.slice(1)}
                      </button>
                    ))}
                  </div>
                  {appState.message && (
                    <p className="mt-2 text-sm text-slate-400">Message: <span className="text-slate-200">{appState.message}</span></p>
                  )}
                </div>

                <div className="border-t border-slate-800 pt-6">
                  <label className="block text-sm text-slate-400 mb-3">Feature Toggles</label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.entries(appState.toggles).map(([name, enabled]) => (
                      <div key={name} className="flex items-center justify-between p-3 bg-slate-950 rounded-xl border border-slate-800">
                        <div>
                          <div className="font-medium text-slate-200 capitalize">{name.replace("_", " ")}</div>
                          <p className="text-xs text-slate-500">
                            {enabled ? "Enabled" : "Disabled"}
                          </p>
                        </div>
                        <button
                          role="switch"
                          aria-checked={enabled}
                          aria-label={`Toggle ${name.replaceAll("_", " ")}`}
                          onClick={() => handleToggleChange(name, !enabled)}
                          disabled={busy.has(`toggle-${name}`)}
                          className={`shrink-0 w-12 h-6 rounded-full flex items-center transition-colors ${
                            enabled
                              ? "bg-green-600 border-green-600"
                              : "bg-slate-700 border-slate-700"
                          } disabled:opacity-60`}
                        >
                          <span
                            className={`w-5 h-5 rounded-full bg-white transition-transform ${
                              enabled ? "translate-x-6" : "translate-x-1"
                            }`}
                          />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </section>

          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Bot className="w-5 h-5 text-purple-400" /> Sentinel Self-Healing
              </h2>
              <button
                onClick={handleRunSentinel}
                disabled={busy.has("sentinel-run")}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm font-medium transition-colors disabled:opacity-60"
              >
                {busy.has("sentinel-run") ? (
                  <span className="flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Running...</span>
                ) : (
                  <span className="flex items-center gap-2"><RefreshCw className="w-4 h-4" /> Run Cycle</span>
                )}
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
              <div className="bg-slate-950 rounded-xl p-3 border border-slate-800">
                <div className="text-slate-500">Status</div>
                <div className="font-mono text-lg flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${sentinelRunning ? "bg-yellow-400" : "bg-green-400"}`} />
                  {sentinelRunning ? "Running" : "Idle"}
                </div>
              </div>
              <div className="bg-slate-950 rounded-xl p-3 border border-slate-800">
                <div className="text-slate-500">Last Run</div>
                <div className="font-mono text-lg">
                  {sentinelLastRun ? new Date(sentinelLastRun).toLocaleString() : "Never"}
                </div>
              </div>
              <div className="bg-slate-950 rounded-xl p-3 border border-slate-800">
                <div className="text-slate-500">Live Stream</div>
                <div className="font-mono text-lg flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${sentinelStreamConnected ? "bg-green-400" : "bg-red-400"}`} />
                  {sentinelStreamConnected ? "Connected" : "Disconnected"}
                </div>
              </div>
            </div>
          </section>
        </div>
      )}

      {activeTab === "providers" && (
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Server className="w-5 h-5 text-blue-400" /> Provider Health & Usage
            </h2>
            <button onClick={loadProviders} aria-label="Refresh provider usage" disabled={loading} className="px-3 py-2 text-sm bg-slate-800 hover:bg-slate-700 rounded-lg disabled:opacity-60">
              <RefreshCw className={`w-4 h-4 inline ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-800">
                  <th className="pb-2 font-medium">Provider</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">Models</th>
                  <th className="pb-2 font-medium">Tokens</th>
                  <th className="pb-2 font-medium">Balance</th>
                  <th className="pb-2 font-medium">Checked</th>
                  <th className="pb-2 font-medium">Suggestion</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {providers.map((p) => (
                  <tr key={p.provider} className="hover:bg-slate-950/50">
                    <td className="py-3 font-mono text-slate-200">{p.provider}</td>
                    <td className="py-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium border ${getProviderStatusColor(p.status)}`}>
                        {p.status.charAt(0).toUpperCase() + p.status.slice(1)}
                      </span>
                    </td>
                    <td className="py-3 text-slate-300">{p.model_count}</td>
                    <td className="py-3 text-slate-300 font-mono">{p.tokens_used.toLocaleString()}</td>
                    <td className="py-3 text-slate-300">
                      {p.balance_available !== null && p.balance_available !== undefined ? `$${p.balance_available.toFixed(2)}` : "—"}
                    </td>
                    <td className="py-3 text-slate-400">
                      {p.checked_at ? new Date(p.checked_at).toLocaleString() : "Never"}
                    </td>
                    <td className="py-3 text-slate-300 max-w-xs truncate">{p.suggestion || "—"}</td>
                  </tr>
                ))}
                {providers.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">No provider data available</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {activeTab === "sentinel" && (
        <div className="space-y-6">
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-400" /> Events
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b border-slate-800">
                    <th className="pb-2 font-medium">Time</th>
                    <th className="pb-2 font-medium">Severity</th>
                    <th className="pb-2 font-medium">Scope</th>
                    <th className="pb-2 font-medium">Agent</th>
                    <th className="pb-2 font-medium">Title</th>
                    <th className="pb-2 font-medium">Status</th>
                    <th className="pb-2 font-medium">Fix</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {sentinelEvents.map((e) => (
                    <tr key={e.id} className="hover:bg-slate-950/50">
                      <td className="py-2 text-slate-400 font-mono text-xs">
                        {new Date(e.created_at).toLocaleTimeString()}
                      </td>
                      <td className="py-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${getSeverityColor(e.severity)}`}>
                          {e.severity}
                        </span>
                      </td>
                      <td className="py-2 text-slate-300 capitalize">{e.scope}</td>
                      <td className="py-2 text-slate-300">{e.agent}</td>
                      <td className="py-2 text-slate-200 max-w-md truncate">{e.title}</td>
                      <td className="py-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${
                          e.status === "open" ? "text-yellow-400 bg-yellow-900/30 border-yellow-700/50" :
                          e.status === "auto_fixed" ? "text-green-400 bg-green-900/30 border-green-700/50" :
                          "text-slate-400 bg-slate-900/30 border-slate-700/50"
                        }`}>
                          {e.status.replace("_", " ")}
                        </span>
                      </td>
                      <td className="py-2 text-slate-400 max-w-xs truncate">
                        {e.suggested_fix || (e.auto_fix_report ? `Auto-fixed: ${e.auto_fix_report}` : "—")}
                      </td>
                    </tr>
                  ))}
                  {sentinelEvents.length === 0 && (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-500">No events recorded</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Eye className="w-5 h-5 text-blue-400" /> Discussion (AI Engineers)
            </h2>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {sentinelDiscussion.map((d) => (
                <div key={d.id} className="bg-slate-950 border border-slate-800 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium text-blue-400">{d.agent}</span>
                    <span className="text-xs text-slate-500">{new Date(d.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-sm text-slate-300 whitespace-pre-wrap">{d.message}</p>
                </div>
              ))}
              {sentinelDiscussion.length === 0 && (
                <div className="text-center text-slate-500 py-8">No discussion entries yet</div>
              )}
            </div>
          </section>

          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Wifi className="w-5 h-5 text-green-400" /> Live Telemetry Stream
            </h2>
            <div className="flex items-center gap-4 text-sm">
              <span className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${
                sentinelStreamConnected
                  ? "text-green-400 bg-green-900/30 border border-green-700/50"
                  : "text-red-400 bg-red-900/30 border border-red-700/50"
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${sentinelStreamConnected ? "bg-green-400" : "bg-red-400"}`} />
                {sentinelStreamConnected ? "Connected" : "Disconnected"}
              </span>
              <span className="text-slate-500">
                Events, discussion entries, and auto-heal actions stream here in real-time.
              </span>
            </div>
          </section>
        </div>
      )}

      {activeTab === "users" && (
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-400" /> User Management
            </h2>
            <button onClick={loadUsers} aria-label="Refresh users" disabled={loading} className="px-3 py-2 text-sm bg-slate-800 hover:bg-slate-700 rounded-lg disabled:opacity-60">
              <RefreshCw className={`w-4 h-4 inline ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-800">
                  <th className="pb-2 font-medium">ID</th>
                  <th className="pb-2 font-medium">Email</th>
                  <th className="pb-2 font-medium">Role</th>
                  <th className="pb-2 font-medium">Confirmed</th>
                  <th className="pb-2 font-medium">Banned Until</th>
                  <th className="pb-2 font-medium">Last Sign In</th>
                  <th className="pb-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-950/50">
                    <td className="py-3 font-mono text-xs text-slate-400">{u.id.slice(0, 8)}…</td>
                    <td className="py-3 text-slate-200">{u.email}</td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        u.admin ? "text-purple-400 bg-purple-900/30 border border-purple-700/50" : "text-slate-400 bg-slate-900/30 border border-slate-700/50"
                      }`}>
                        {u.admin ? "Admin" : "User"}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        u.confirmed ? "text-green-400 bg-green-900/30 border border-green-700/50" : "text-yellow-400 bg-yellow-900/30 border border-yellow-700/50"
                      }`}>
                        {u.confirmed ? "Yes" : "No"}
                      </span>
                    </td>
                    <td className="py-3 text-slate-300 font-mono text-xs">
                      {u.banned_until != null ? new Date(u.banned_until).toLocaleString() : "—"}
                    </td>
                    <td className="py-3 text-slate-400 font-mono text-xs">
                      {u.last_sign_in_at != null ? new Date(u.last_sign_in_at).toLocaleString() : "Never"}
                    </td>
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        {u.banned_until != null ? (
                          <button
                            onClick={() => handleReactivate(u.id)}
                            disabled={busy.has(`reactivate-${u.id}`)}
                            className="px-3 py-1.5 text-xs bg-green-600 hover:bg-green-500 rounded-lg text-white transition-colors disabled:opacity-60"
                          >
                            <Unlock className="w-3 h-3 inline mr-1" /> Reactivate
                          </button>
                        ) : (
                          <button
                            onClick={() => handleSuspend(u.id)}
                            disabled={busy.has(`suspend-${u.id}`)}
                            className="px-3 py-1.5 text-xs bg-red-600 hover:bg-red-500 rounded-lg text-white transition-colors disabled:opacity-60"
                          >
                            <Ban className="w-3 h-3 inline mr-1" /> Suspend
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">No users found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {activeTab === "account" && (
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-2xl">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <UserCog className="w-5 h-5 text-purple-400" /> Admin Account Settings
          </h2>
          <p className="text-sm text-slate-500 mb-6">
            Change your login email and/or password. Both fields are optional — leave blank to keep current value.
          </p>
          {accountMsg && (
            <div className={`mb-4 p-3 rounded-lg text-sm flex items-center justify-between ${
              accountMsg.type === "success"
                ? "bg-green-900/30 border border-green-700/50 text-green-300"
                : "bg-red-900/30 border border-red-700/50 text-red-300"
            }`}>
              <span>{accountMsg.text}</span>
              <button onClick={() => setAccountMsg(null)} aria-label="Dismiss message" className="text-slate-400 hover:text-slate-200">×</button>
            </div>
          )}
          <form onSubmit={handleAccountSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm text-slate-400 mb-1">New Email</label>
              <input
                id="email"
                type="email"
                value={accountForm.email}
                onChange={(e) => setAccountForm({ ...accountForm, email: e.target.value })}
                placeholder="admin@example.com"
                className="w-full px-4 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label htmlFor="new_password" className="block text-sm text-slate-400 mb-1">New Password (min 8 chars)</label>
              <input
                id="new_password"
                type="password"
                value={accountForm.new_password}
                onChange={(e) => setAccountForm({ ...accountForm, new_password: e.target.value })}
                placeholder="••••••••"
                className="w-full px-4 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={busy.has("account")}
              className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-white font-medium transition-colors disabled:opacity-60"
            >
              {busy.has("account") ? (
                <span className="flex items-center justify-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Saving...</span>
              ) : (
                "Save Changes"
              )}
            </button>
          </form>
        </section>
      )}

      {busy.size > 0 && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 pointer-events-none">
          <Loader2 className="w-10 h-10 animate-spin text-red-400" />
        </div>
      )}
    </div>
  );
}