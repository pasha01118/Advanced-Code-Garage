"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bell, CheckCheck, Trash2, X } from "lucide-react";
import {
  getNotificationCounts,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  clearNotifications,
} from "@/lib/api";
import type { NotificationOut } from "@/lib/types";

const POLL_MS = 30_000;

function tone(type: string): string {
  switch (type) {
    case "success": return "text-emerald-400";
    case "warn": return "text-amber-400";
    case "error": return "text-red-400";
    default: return "text-blue-400";
  }
}

function ago(value?: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const seconds = Math.max(0, Math.round((Date.now() - date.getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationOut[]>([]);
  const [unread, setUnread] = useState(0);
  const [busy, setBusy] = useState(false);
  const [toasts, setToasts] = useState<NotificationOut[]>([]);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const knownRef = useRef<Set<string> | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [list, counts] = await Promise.all([
        listNotifications(false, 50),
        getNotificationCounts(),
      ]);
      setItems(list.notifications);
      setUnread(counts.unread);
      const ids = new Set(list.notifications.filter((n) => !n.read_at).map((n) => n.id));
      if (knownRef.current !== null) {
        const fresh = list.notifications.filter(
          (n) => !n.read_at && !knownRef.current?.has(n.id)
        );
        if (fresh.length > 0) {
          setToasts((prev) => [...fresh.slice(0, 3), ...prev].slice(0, 3));
        }
      }
      knownRef.current = ids;
    } catch {
      // Keep the last known list when the API is unavailable.
    }
  }, []);

  useEffect(() => {
    const initial = window.setTimeout(() => void refresh(), 0);
    const timer = window.setInterval(() => void refresh(), POLL_MS);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(timer);
    };
  }, [refresh]);

  useEffect(() => {
    if (!open) return;
    const onDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.stopImmediatePropagation();
      setOpen(false);
      triggerRef.current?.focus();
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey, true);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey, true);
    };
  }, [open]);

  useEffect(() => {
    if (toasts.length === 0) return;
    const timer = window.setTimeout(
      () => setToasts((prev) => prev.slice(0, -1)),
      6000
    );
    return () => window.clearTimeout(timer);
  }, [toasts]);

  const run = async (action: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await action();
      await refresh();
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="relative" ref={rootRef}>
        <button
          ref={triggerRef}
          type="button"
          aria-label={`Notifications${unread ? `, ${unread} unread` : ""}`}
          aria-haspopup="menu"
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
          className="relative p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-colors"
        >
          <Bell className="w-4 h-4" />
          {unread > 0 && (
            <span className="absolute -top-0.5 -right-0.5 min-w-4 h-4 px-1 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center">
              {unread > 9 ? "9+" : unread}
            </span>
          )}
        </button>
        {open && (
          <div
            role="menu"
            aria-label="Notifications"
            className="absolute right-0 mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-slate-800 bg-slate-900 shadow-2xl z-50"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
              <div className="text-sm font-semibold text-slate-100">
                Notifications <span className="text-xs text-slate-500">({unread} unread)</span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  disabled={busy || unread === 0}
                  onClick={() => void run(markAllNotificationsRead)}
                  title="Mark all read"
                  className="p-1.5 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-800 disabled:opacity-40"
                >
                  <CheckCheck className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  disabled={busy || items.length === 0}
                  onClick={() => void run(clearNotifications)}
                  title="Clear all"
                  className="p-1.5 rounded text-slate-400 hover:text-red-400 hover:bg-slate-800 disabled:opacity-40"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
            <div className="max-h-80 overflow-y-auto divide-y divide-slate-800/70">
              {items.length === 0 ? (
                <div className="px-4 py-8 text-center text-xs text-slate-500">No notifications yet.</div>
              ) : (
                items.map((item) => (
                  <div
                    key={item.id}
                    role="menuitem"
                    className={`px-4 py-3 text-xs ${item.read_at ? "opacity-60" : "bg-blue-500/5"}`}
                  >
                    <div className="flex items-start gap-2">
                      <span className={`mt-0.5 ${tone(item.type)}`}>●</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-slate-200">{item.title}</div>
                        {item.body && <div className="mt-0.5 text-slate-400 line-clamp-2">{item.body}</div>}
                        <div className="mt-1 text-[10px] text-slate-500">{ago(item.created_at)}</div>
                      </div>
                      {!item.read_at && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => void run(() => markNotificationRead(item.id))}
                          className="text-[10px] text-blue-400 hover:text-blue-300 disabled:opacity-40"
                        >
                          Read
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
            <Link
              href="/notifications"
              onClick={() => setOpen(false)}
              className="block px-4 py-2.5 text-center text-xs text-blue-400 hover:bg-slate-800/60 border-t border-slate-800"
            >
              View all notifications
            </Link>
          </div>
        )}
      </div>

      {toasts.length > 0 && (
        <div className="fixed bottom-4 right-4 z-[60] flex flex-col gap-2 w-72 max-w-[calc(100vw-2rem)]">
          {toasts.map((toast) => (
            <div
              key={toast.id}
              className="rounded-lg border border-slate-700 bg-slate-900 p-3 shadow-xl text-xs"
            >
              <div className="flex items-start gap-2">
                <span className={tone(toast.type)}>●</span>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-slate-100">{toast.title}</div>
                  <div className="text-slate-400 line-clamp-2">{toast.body}</div>
                </div>
                <button
                  type="button"
                  aria-label="Dismiss notification"
                  onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
                  className="text-slate-500 hover:text-slate-200"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
