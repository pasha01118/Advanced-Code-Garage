"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, ScrollText } from "lucide-react";
import { getAuditLog } from "@/lib/api";
import type { AuditEntryOut } from "@/lib/types";

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditEntryOut[]>([]);
  const [allUsers, setAllUsers] = useState(false);
  const [action, setAction] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getAuditLog({ all_users: allUsers, action: action || undefined, limit: 200 });
      setEntries(result.entries);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit log");
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [allUsers, action]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 150);
    return () => window.clearTimeout(timer);
  }, [load]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <ScrollText className="w-6 h-6 text-amber-400" /> Audit Log
        </h1>
        <p className="text-sm text-slate-500 mt-1">A chronological record of workspace actions.</p>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-800 bg-slate-900 p-4">
        <input
          value={action}
          onChange={(event) => setAction(event.target.value)}
          placeholder="Filter by action (e.g. project.create)"
          className="flex-1 min-w-56 rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-200 outline-none focus:border-blue-600"
        />
        <label className="flex items-center gap-2 text-xs text-slate-400">
          <input
            type="checkbox"
            checked={allUsers}
            onChange={(event) => setAllUsers(event.target.checked)}
            className="w-3.5 h-3.5 accent-blue-600"
          />
          All users (admin only)
        </label>
      </div>

      {error && <div className="rounded-lg border border-red-800/60 bg-red-950/30 px-4 py-3 text-sm text-red-300">{error}</div>}

      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-slate-800">
              <th className="px-4 py-3">When</th>
              <th className="px-4 py-3">Actor</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Target</th>
              <th className="px-4 py-3">Detail</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {loading ? (
              <tr><td colSpan={5} className="py-10 text-center text-slate-500"><Loader2 className="w-5 h-5 animate-spin mx-auto" /></td></tr>
            ) : entries.length === 0 ? (
              <tr><td colSpan={5} className="py-10 text-center text-slate-500">No audit entries found.</td></tr>
            ) : (
              entries.map((entry) => (
                <tr key={entry.id} className="hover:bg-slate-950/50">
                  <td className="px-4 py-2.5 text-xs text-slate-500 whitespace-nowrap">
                    {entry.created_at ? new Date(entry.created_at).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-[11px] text-slate-400 truncate max-w-40">{entry.actor ?? "—"}</td>
                  <td className="px-4 py-2.5"><span className="rounded bg-blue-500/10 px-2 py-0.5 text-[11px] text-blue-300">{entry.action}</span></td>
                  <td className="px-4 py-2.5 font-mono text-[11px] text-slate-400 truncate max-w-44">{entry.target ?? "—"}</td>
                  <td className="px-4 py-2.5 text-[11px] text-slate-500 font-mono truncate max-w-64">
                    {entry.detail ? JSON.stringify(entry.detail) : "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
