"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Command, CornerDownLeft, Loader2, Search } from "lucide-react";
import { searchWorkspace, runSentinel, setExecutionMode } from "@/lib/api";
import type { ExecutionMode, SearchResultOut } from "@/lib/types";
import { savePreferences, usePreferences } from "@/lib/use-preferences";
import { useLiveSwarm } from "@/lib/use-live-swarm";

interface PaletteItem {
  key: string;
  title: string;
  subtitle: string;
  href?: string;
  run?: () => Promise<void> | void;
}

export function CommandPalette({ isAdmin = false }: { isAdmin?: boolean }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [active, setActive] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const router = useRouter();
  const prefs = usePreferences();
  const { refresh: refreshSwarm } = useLiveSwarm();

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
        setQuery("");
        setResults([]);
        setActive(0);
        setNotice(null);
      } else if (event.key === "Escape" && open) {
        event.preventDefault();
        event.stopImmediatePropagation();
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    document.addEventListener("keydown", onKey, true);
    return () => document.removeEventListener("keydown", onKey, true);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    const frame = window.requestAnimationFrame(() => inputRef.current?.focus());
    const onTab = (event: KeyboardEvent) => {
      if (event.key !== "Tab" || !dialogRef.current) return;
      const focusable = Array.from(
        dialogRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'
        )
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onTab);
    return () => {
      window.cancelAnimationFrame(frame);
      document.removeEventListener("keydown", onTab);
      previous?.focus();
    };
  }, [open]);

  useEffect(() => {
    if (!open || query.trim().length < 2) {
      const timer = window.setTimeout(() => {
        setResults([]);
        setLoading(false);
      }, 0);
      return () => window.clearTimeout(timer);
    }
    let cancelled = false;
    const timer = window.setTimeout(() => {
      setLoading(true);
      void searchWorkspace(query)
        .then((data) => {
          if (cancelled) return;
          setResults(data.results);
          setActive(0);
        })
        .catch(() => {
          if (!cancelled) setResults([]);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 150);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [open, query]);

  const actions = useMemo<PaletteItem[]>(() => {
    const items: PaletteItem[] = [
      {
        key: "action:theme",
        title: `Switch to ${prefs.theme === "dark" ? "light" : "dark"} theme`,
        subtitle: "Personalization",
        run: () => savePreferences({ theme: prefs.theme === "dark" ? "light" : "dark" }),
      },
      { key: "nav:/preferences", title: "Preferences", subtitle: "Open page", href: "/preferences" },
      { key: "nav:/notifications", title: "Notifications", subtitle: "Open page", href: "/notifications" },
      { key: "nav:/metrics", title: "Metrics", subtitle: "Open page", href: "/metrics" },
    ];
    for (const mode of ["Autonomous", "AI-Man", "Manual"] as ExecutionMode[]) {
      items.push({
        key: `mode:${mode}`,
        title: `Set execution mode: ${mode}`,
        subtitle: "Swarm command",
        run: async () => {
          await setExecutionMode(mode);
          await refreshSwarm();
          setNotice(`Execution mode set to ${mode}`);
        },
      });
    }
    if (isAdmin) {
      items.push({
        key: "action:sentinel",
        title: "Run Sentinel cycle",
        subtitle: "Admin command",
        run: async () => {
          const result = await runSentinel();
          setNotice(
            result.skipped
              ? "Sentinel cycle already running"
              : `Sentinel added ${result.events_added} finding(s)`
          );
        },
      });
      items.push({ key: "nav:/audit", title: "Audit log", subtitle: "Open page", href: "/audit" });
    }
    return items;
  }, [isAdmin, prefs.theme, refreshSwarm]);

  const items = useMemo<PaletteItem[]>(() => {
    const remote: PaletteItem[] = results.map((result) => ({
      key: `${result.type}:${result.id}`,
      title: result.title,
      subtitle: result.subtitle || result.type,
      href: result.href,
    }));
    const needle = query.trim().toLowerCase();
    const filteredActions = needle
      ? actions.filter((item) => `${item.title} ${item.subtitle}`.toLowerCase().includes(needle))
      : actions;
    return [...remote, ...filteredActions].slice(0, 30);
  }, [actions, query, results]);

  const select = async (item: PaletteItem) => {
    try {
      if (item.href) router.push(item.href);
      if (item.run) await item.run();
      if (!item.href && !notice) setNotice("Command complete");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Command failed");
    }
  };

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((index) => Math.min(index + 1, Math.max(items.length - 1, 0)));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((index) => Math.max(index - 1, 0));
    } else if (event.key === "Enter" && items[active]) {
      event.preventDefault();
      void select(items[active]);
    }
  };

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => {
          setOpen(true);
          setQuery("");
          setResults([]);
          setActive(0);
          setNotice(null);
        }}
        className="hidden sm:flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-slate-800 text-xs text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-colors"
        aria-label="Open command palette"
      >
        <Command className="w-3.5 h-3.5" />
        <span>Commands</span>
        <kbd className="ml-2 px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-500">⌘K</kbd>
      </button>

      {open && (
        <div
          className="fixed inset-0 z-[70] flex items-start justify-center bg-slate-950/70 p-4 pt-[12vh] backdrop-blur-sm"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setOpen(false);
          }}
        >
          <div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label="Command palette"
            className="w-full max-w-xl overflow-hidden rounded-xl border border-slate-700 bg-slate-900 shadow-2xl"
          >
            <div className="flex items-center gap-3 border-b border-slate-800 px-4 py-3">
              <Search className="w-4 h-4 shrink-0 text-slate-500" />
              <input
                ref={inputRef}
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setActive(0);
                }}
                onKeyDown={onKeyDown}
                placeholder="Search pages, projects, providers, or type a command..."
                className="w-full bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
              />
              {loading && <Loader2 className="w-4 h-4 animate-spin text-slate-500" />}
            </div>
            {notice && (
              <div className="border-b border-slate-800 bg-blue-500/10 px-4 py-2 text-xs text-blue-300">
                {notice}
              </div>
            )}
            <div className="max-h-[55vh] overflow-y-auto p-2" role="listbox" aria-label="Commands">
              {items.length === 0 ? (
                <div className="px-3 py-8 text-center text-xs text-slate-500">
                  {query ? "No matching commands." : "Type at least two characters to search."}
                </div>
              ) : (
                items.map((item, index) => (
                  <button
                    key={item.key}
                    type="button"
                    role="option"
                    aria-selected={index === active}
                    onMouseEnter={() => setActive(index)}
                    onClick={() => void select(item)}
                    className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                      index === active ? "bg-blue-600/20 text-blue-200" : "text-slate-300 hover:bg-slate-800/70"
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium">{item.title}</div>
                      <div className="text-[11px] text-slate-500">{item.subtitle}</div>
                    </div>
                    {index === active && <CornerDownLeft className="w-3.5 h-3.5 text-slate-500" />}
                  </button>
                ))
              )}
            </div>
            <div className="border-t border-slate-800 px-4 py-2 text-[10px] text-slate-500">
              ↑↓ navigate · Enter run · Esc close
            </div>
          </div>
        </div>
      )}
    </>
  );
}
