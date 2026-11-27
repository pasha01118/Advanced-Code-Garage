"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  Clock,
  Cloud,
  Database,
  ExternalLink,
  LayoutDashboard,
  Loader2,
  RefreshCw,
  ScrollText,
  Server,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import {
  getAppState,
  getSentinelSnapshot,
  getWorkspaceMetrics,
  runSentinel,
} from "@/lib/api";
import { useAuthSession } from "@/lib/use-auth-session";
import { useIsAdmin } from "@/lib/use-admin";
import type {
  AppStateOut,
  MetricsOverviewOut,
  SentinelSnapshotOut,
} from "@/lib/types";

const RENDER_HEALTH = "https://agc-backend-ix19.onrender.com/health";
const RENDER_OPENAPI = "https://agc-backend-ix19.onrender.com/openapi.json";
const DEPLOY_GUIDE =
  "https://github.com/pasha01118/Advanced-Code-Garage/blob/main/apps/backend/VERCEL.md";
const MIGRATIONS =
  "https://github.com/pasha01118/Advanced-Code-Garage/tree/main/apps/backend/sql";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

const STATUS_TONES: Record<string, string> = {
  running: "bg-emerald-500",
  maintenance: "bg-amber-500",
  shutdown: "bg-red-500",
};

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

function formatTime(value?: string | null): string {
  if (!value) return "Never";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function Section({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: typeof Server;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
      <h2 className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-200">
        <Icon className="h-4 w-4 text-blue-400" /> {title}
      </h2>
      {children}
    </section>
  );
}

function DetailRow({
  label,
  value,
  hint,
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-slate-800/70 py-2.5 last:border-0">
      <div className="min-w-0">
        <div className="text-xs text-slate-500">{label}</div>
        {hint && <div className="mt-0.5 text-[11px] text-slate-600">{hint}</div>}
      </div>
      <div className="shrink-0 text-right font-mono text-xs text-slate-200">{value}</div>
    </div>
  );
}

function ExternalRow({
  label,
  href,
  note,
  badge,
}: {
  label: string;
  href: string;
  note: string;
  badge: string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
          <Server className="h-4 w-4 text-blue-400" /> {label}
        </div>
        <span className="rounded-full border border-slate-700 bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
          {badge}
        </span>
      </div>
      <p className="mt-2 text-xs text-slate-500">{note}</p>
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="mt-3 inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
      >
        Open <ExternalLink className="h-3 w-3" />
      </a>
    </div>
  );
}

export default function BackendPage() {
  const { session, loading: authLoading } = useAuthSession();
  const isAdmin = useIsAdmin(Boolean(session));
  const [appState, setAppState] = useState<AppStateOut | null>(null);
  const [metrics, setMetrics] = useState<MetricsOverviewOut | null>(null);
  const [sentinel, setSentinel] = useState<SentinelSnapshotOut | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningSentinel, setRunningSentinel] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const [appResult, metricsResult, sentinelResult] = await Promise.allSettled([
      getAppState(),
      getWorkspaceMetrics(),
      isAdmin ? getSentinelSnapshot() : Promise.resolve(null),
    ]);

    const nextErrors: string[] = [];
    if (appResult.status === "fulfilled") setAppState(appResult.value as AppStateOut);
    else {
      setAppState(null);
      nextErrors.push(`Backend state: ${errorMessage(appResult.reason)}`);
    }
    if (metricsResult.status === "fulfilled")
      setMetrics(metricsResult.value as MetricsOverviewOut);
    else {
      setMetrics(null);
      nextErrors.push(`Metrics: ${errorMessage(metricsResult.reason)}`);
    }
    if (sentinelResult.status === "fulfilled")
      setSentinel(sentinelResult.value as SentinelSnapshotOut | null);
    else nextErrors.push(`Sentinel: ${errorMessage(sentinelResult.reason)}`);

    setErrors(nextErrors);
    setLoading(false);
  }, [isAdmin]);

  useEffect(() => {
    if (authLoading || !session) return;
    const initial = window.setTimeout(() => void load(), 0);
    const timer = window.setInterval(() => void load(), 30_000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(timer);
    };
  }, [authLoading, session, load]);

  const runNow = async () => {
    setRunningSentinel(true);
    try {
      await runSentinel();
      await load();
    } catch (err) {
      setErrors((prev) => [...prev, `Sentinel run: ${errorMessage(err)}`]);
    } finally {
      setRunningSentinel(false);
    }
  };

  const stats = [
    {
      label: "API status",
      value: appState?.status ?? (loading ? "Checking" : "Unavailable"),
      detail: appState?.message || "Operational state from the backend",
      icon: Activity,
    },
    {
      label: "System mode",
      value: metrics?.system_mode ?? "—",
      detail: `${metrics?.active_agents ?? 0} active agents`,
      icon: Server,
    },
    {
      label: "Projects",
      value: metrics?.projects_total ?? "—",
      detail: `${metrics?.projects_by_status?.delivered ?? 0} delivered`,
      icon: LayoutDashboard,
    },
    {
      label: "Sentinel findings",
      value: metrics?.sentinel_open ?? "—",
      detail: isAdmin ? "Admin details below" : "Visible to administrators",
      icon: AlertTriangle,
    },
  ];

  const quickLinks = [
    { href: "/metrics", label: "Live metrics", icon: Activity },
    { href: "/terminal", label: "Terminal", icon: Terminal },
    ...(isAdmin
      ? [
          { href: "/admin", label: "Control Panel", icon: ShieldCheck },
          { href: "/audit", label: "Audit Log", icon: ScrollText },
        ]
      : []),
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <Server className="h-6 w-6 text-blue-400" /> Backend
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Runtime health and deployment overview. Refreshes every 30 seconds.
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

      {errors.length > 0 && (
        <div className="space-y-1 rounded-lg border border-red-800/60 bg-red-950/30 px-4 py-3 text-sm text-red-300">
          {errors.map((error) => (
            <div key={error}>{error}</div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="rounded-xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Icon className="h-4 w-4 text-blue-400" /> {stat.label}
              </div>
              <div className="mt-3 font-mono text-xl font-bold text-slate-100">{stat.value}</div>
              <div className="mt-1 truncate text-[11px] text-slate-500">{stat.detail}</div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Section title="Deployment targets" icon={Cloud}>
          <div className="space-y-3">
            <ExternalRow
              label="Render"
              badge="Primary"
              note="Long-lived uvicorn service. All frontend /api/* traffic is routed here until cutover."
              href={RENDER_HEALTH}
            />
            <ExternalRow
              label="Vercel"
              badge="Optional"
              note="Independent serverless FastAPI deployment. Uses a daily cron instead of the in-process Sentinel loop."
              href={DEPLOY_GUIDE}
            />
            <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
              <div className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-2 text-sm font-medium text-slate-200">
                  <Activity className="h-4 w-4 text-emerald-400" /> API proxy
                </span>
                <span className="rounded-full border border-emerald-800/60 bg-emerald-950/30 px-2 py-0.5 text-[10px] uppercase tracking-wide text-emerald-400">
                  Active
                </span>
              </div>
              <p className="mt-2 break-all font-mono text-[11px] text-slate-500">
                {`${API_BASE}/* → Render backend`}
              </p>
              <a
                href={RENDER_OPENAPI}
                target="_blank"
                rel="noreferrer"
                className="mt-3 inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
              >
                View contract <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        </Section>

        <Section title="Sentinel & cron" icon={Clock}>
          {isAdmin ? (
            <>
              <div className="space-y-1">
                <DetailRow
                  label="In-process loop"
                  value={
                    sentinel ? (
                      <span
                        className={
                          sentinel.running ? "text-emerald-400" : "text-amber-400"
                        }
                      >
                        {sentinel.running ? "Running" : "Stopped"}
                      </span>
                    ) : loading ? (
                      "Loading…"
                    ) : (
                      "Unavailable"
                    )
                  }
                  hint="Disabled automatically on Vercel Functions"
                />
                <DetailRow
                  label="Last cycle"
                  value={formatTime(sentinel?.last_run_at)}
                />
                <DetailRow
                  label="Interval"
                  value={sentinel ? `${sentinel.interval_seconds}s` : "—"}
                  hint="Vercel Hobby cron runs daily at 03:00 UTC"
                />
                <DetailRow
                  label="Cron endpoint"
                  value="/api/cron/sentinel"
                  hint="Bearer-protected by CRON_SECRET"
                />
              </div>
              <button
                type="button"
                onClick={() => void runNow()}
                disabled={runningSentinel || !sentinel}
                className="mt-4 flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-60"
              >
                {runningSentinel ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="h-3.5 w-3.5" />
                )}
                Run cycle now
              </button>
            </>
          ) : (
            <p className="text-xs text-slate-500">
              Sentinel runtime details and manual runs are available to administrators.
            </p>
          )}
        </Section>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Section title="Feature toggles" icon={ShieldCheck}>
          {Object.entries(appState?.toggles ?? {}).length > 0 ? (
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(appState?.toggles ?? {}).map(([name, enabled]) => (
                <div
                  key={name}
                  className="flex items-center justify-between gap-2 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2"
                >
                  <span className="truncate text-xs capitalize text-slate-400">
                    {name.replace(/_/g, " ")}
                  </span>
                  <span
                    className={`h-2 w-2 shrink-0 rounded-full ${
                      enabled ? "bg-emerald-500" : "bg-slate-600"
                    }`}
                    title={enabled ? "Enabled" : "Disabled"}
                  />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">
              {loading ? "Loading toggles…" : "No toggles reported by the backend."}
            </p>
          )}
          {appState?.updated_at && (
            <p className="mt-4 text-[11px] text-slate-600">
              Last changed {formatTime(appState.updated_at)}
            </p>
          )}
        </Section>

        <Section title="Operations" icon={Database}>
          <div className="space-y-1">
            <DetailRow
              label="Operational state"
              value={
                <span className="flex items-center justify-end gap-2">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      STATUS_TONES[appState?.status ?? ""] ?? "bg-slate-500"
                    }`}
                  />
                  {appState?.status ?? "—"}
                </span>
              }
            />
            <DetailRow label="Metrics source" value="Supabase PostgreSQL" />
            <DetailRow label="Migrations" value="Manual" hint="Nothing runs at startup" />
          </div>
          <a
            href={MIGRATIONS}
            target="_blank"
            rel="noreferrer"
            className="mt-4 inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
          >
            Migration runbook <ExternalLink className="h-3 w-3" />
          </a>
          <div className="mt-5 grid grid-cols-2 gap-2">
            {quickLinks.map((link) => {
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2 text-xs text-slate-400 hover:border-blue-800 hover:text-blue-300"
                >
                  <Icon className="h-3.5 w-3.5" /> {link.label}
                </Link>
              );
            })}
          </div>
        </Section>
      </div>
    </div>
  );
}
