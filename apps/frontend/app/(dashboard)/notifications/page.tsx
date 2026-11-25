"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Bell, CheckCheck, Loader2, Trash2 } from "lucide-react";
import {
  clearNotifications,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/api";
import type { NotificationOut } from "@/lib/types";

export default function NotificationsPage() {
  const [items, setItems] = useState<NotificationOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await listNotifications(unreadOnly, 200);
      setItems(result.notifications);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load notifications");
    } finally {
      setLoading(false);
    }
  }, [unreadOnly]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const run = async (action: () => Promise<unknown>) => {
    await action();
    await load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="w-6 h-6 text-blue-400" /> Notifications
          </h1>
          <p className="text-sm text-slate-500 mt-1">System, project and Sentinel events for your account.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setUnreadOnly((value) => !value)}
            className={`px-3 py-1.5 rounded-lg text-xs border ${unreadOnly ? "border-blue-600/60 bg-blue-600/10 text-blue-300" : "border-slate-800 bg-slate-900 text-slate-400"}`}
          >
            {unreadOnly ? "Unread only" : "All"}
          </button>
          <button
            type="button"
            onClick={() => void run(markAllNotificationsRead)}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-100"
            title="Mark all read"
          >
            <CheckCheck className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => void run(clearNotifications)}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-red-400"
            title="Clear all"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && <div className="rounded-lg border border-red-800/60 bg-red-950/30 px-4 py-3 text-sm text-red-300">{error}</div>}

      <div className="space-y-2">
        {loading ? (
          <div className="flex justify-center py-12 text-slate-500"><Loader2 className="w-6 h-6 animate-spin text-blue-500" /></div>
        ) : items.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/50 py-14 text-center">
            <Bell className="w-6 h-6 mx-auto mb-3 text-slate-600" />
            <div className="text-sm text-slate-400">No notifications here yet.</div>
            <Link href="/" className="mt-2 inline-block text-xs text-blue-400 hover:text-blue-300">Back to overview</Link>
          </div>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              className={`rounded-xl border p-4 ${item.read_at ? "border-slate-800 bg-slate-900" : "border-blue-800/50 bg-blue-950/20"}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-medium text-slate-100">{item.title}</div>
                  {item.body && <div className="mt-1 text-xs text-slate-400">{item.body}</div>}
                  <div className="mt-2 text-[10px] text-slate-500">
                    {item.source} · {item.created_at ? new Date(item.created_at).toLocaleString() : "unknown time"}
                  </div>
                </div>
                {!item.read_at && (
                  <button
                    type="button"
                    onClick={() => void run(() => markNotificationRead(item.id))}
                    className="shrink-0 rounded-lg bg-slate-800 px-2.5 py-1.5 text-[11px] text-blue-300 hover:bg-slate-700"
                  >
                    Mark read
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
