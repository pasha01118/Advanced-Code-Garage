"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  Boxes,
  Bot,
  CircleAlert,
  Database,
  Loader2,
  Radio,
  RefreshCw,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import { getWorkspaceMetrics } from "@/lib/api";
import type { MetricsOverviewOut } from "@/lib/types";

const STATUS_TONES: Record<string, string> = {
  delivered: "bg-emerald-500",
  analyzing: "bg-blue-500",
  queued: "bg-amber-500",
  failed: "bg-red-500",
};

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<MetricsOverviewOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await getWorkspaceMetrics();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load metrics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const initial = window.setTimeout(() => void load(), 0);
    const timer = window.setInterval(() => void load(), 15_000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(timer);
    };
  }, [load]);

  const stats = metrics
    ? [
        { icon: Boxes, label: "Projects", value: metrics.projects_total, detail: `${metrics.projects_by_status.delivered ?? 0} delivered` },
        { icon: Bot, label: "Active agents", value: metrics.active_agents, detail: metrics.system_mode },
        { icon: Database, label: "AI keys", value: metrics.providers_configured, detail: `${metrics.providers_active} active` },
        { icon: CircleAlert, label: "Open findings", value: metrics.sentinel_open, detail: metrics.app_status },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="w-6 h-6 text-blue-400" /> Live Metrics
          </h1>
          <p className="text-sm text-slate-500 mt-1">Workspace health, refreshed every 15 seconds.</p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 text-xs text-slate-300 hover:bg-slate-700 disabled:opacity-60"
        >
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-800/60 bg-red-950/30 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {!metrics && loading ? (
        <div className="flex justify-center py-16 text-slate-500">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
        </div>
      ) : metrics ? (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((stat) => {
              const Icon = stat.icon;
              return (
                <div key={stat.label} className="rounded-xl border border-slate-800 bg-slate-900 p-5">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Icon className="w-4 h-4 text-blue-400" /> {stat.label}
                  </div>
                  <div className="mt-3 text-2xl font-bold font-mono text-slate-100">{stat.value}</div>
                  <div className="mt-1 text-[11px] text-slate-500 truncate">{stat.detail}</div>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <h2 className="text-sm font-semibold text-slate-200 mb-5 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-purple-400" /> Project status distribution
              </h2>
              <div className="space-y-4">
                {Object.entries(metrics.projects_by_status).map(([status, count]) => {
                  const total = Math.max(1, metrics.projects_total);
                  return (
                    <div key={status}>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="capitalize text-slate-400">{status}</span>
                        <span className="font-mono text-slate-300">{count}</span>
                      </div>
                      <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${STATUS_TONES[status] ?? "bg-blue-500"}`}
                          style={{ width: `${Math.round((count / total) * 100)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <h2 className="text-sm font-semibold text-slate-200 mb-5 flex items-center gap-2">
                <Radio className="w-4 h-4 text-emerald-400" /> Projects created (last 7 days)
              </h2>
              <div className="flex h-40 items-end gap-2">
                {metrics.projects_recent.map((point) => {
                  const max = Math.max(1, ...metrics.projects_recent.map((p) => p.value));
                  return (
                    <div key={point.label} className="flex-1 flex flex-col items-center gap-2">
                      <div className="w-full flex-1 flex items-end">
                        <div
                          className="w-full rounded-t bg-blue-600/80 min-h-[2px]"
                          style={{ height: `${Math.max(3, (point.value / max) * 100)}%` }}
                          title={`${point.label}: ${point.value}`}
                        />
                      </div>
                      <span className="text-[9px] text-slate-500 font-mono">{point.label.slice(5)}</span>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>

          <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-400" /> Signal summary
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div><div className="text-slate-500 text-xs">Terminal entries</div><div className="font-mono text-slate-200">{metrics.logs_recent}</div></div>
              <div><div className="text-slate-500 text-xs">Unread notifications</div><div className="font-mono text-slate-200">{metrics.notifications_unread}</div></div>
              <div><div className="text-slate-500 text-xs">Operational state</div><div className="font-mono text-slate-200">{metrics.app_status}</div></div>
              <div>
                <div className="text-slate-500 text-xs">Audit history</div>
                <Link href="/audit" className="text-blue-400 hover:text-blue-300">Open log →</Link>
              </div>
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}
