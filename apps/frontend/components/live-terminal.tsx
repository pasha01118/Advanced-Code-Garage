"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Bookmark,
  CirclePause,
  Copy,
  History,
  Loader2,
  Play,
  RefreshCw,
  Save,
  Search,
  Trash2,
} from "lucide-react";
import {
  addCommandHistory,
  clearCommandHistory,
  createSnippet,
  deleteSnippet,
  getLogHistory,
  getLogsStreamUrl,
  listCommandHistory,
  listSnippets,
  parseLogEvent,
} from "@/lib/api";
import { subscribeSSE } from "@/lib/stream-sse";
import type { HistoryEntryOut, LogEntry, LogHistoryEntryOut, SnippetOut } from "@/lib/types";

const MAX_LINES = 300;

type StreamStatus = "connecting" | "connected" | "disconnected";
type LogLine = LogEntry & { key: number };

function isLogEntry(value: unknown): value is LogEntry {
  if (typeof value !== "object" || value === null) return false;
  const entry = value as Record<string, unknown>;
  return (
    typeof entry.level === "string" &&
    typeof entry.agent === "string" &&
    typeof entry.message === "string" &&
    (entry.timestamp === undefined || entry.timestamp === null || typeof entry.timestamp === "string")
  );
}

function levelClass(level: string): string {
  switch (level.toUpperCase()) {
    case "OK":
    case "SUCCESS":
      return "text-green-400";
    case "WARN":
    case "WARNING":
      return "text-yellow-400";
    case "ERROR":
    case "FAIL":
      return "text-red-400";
    case "DEBUG":
      return "text-slate-400";
    default:
      return "text-blue-300";
  }
}

export default function LiveTerminal({ showTools = false }: { showTools?: boolean }) {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [status, setStatus] = useState<StreamStatus>("connecting");
  const [paused, setPaused] = useState(false);
  const [sticky, setSticky] = useState(true);
  const [tab, setTab] = useState<"live" | "history">("live");
  const [search, setSearch] = useState("");
  const [snippets, setSnippets] = useState<SnippetOut[]>([]);
  const [commands, setCommands] = useState<HistoryEntryOut[]>([]);
  const [historyLogs, setHistoryLogs] = useState<LogHistoryEntryOut[]>([]);
  const [snippetName, setSnippetName] = useState("");
  const [snippetCommand, setSnippetCommand] = useState("");
  const [commandInput, setCommandInput] = useState("");
  const [toolsError, setToolsError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const pausedRef = useRef(false);
  const nextKeyRef = useRef(0);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const appendLog = (entry: LogEntry) => {
      const line: LogLine = { ...entry, key: nextKeyRef.current++ };
      setLogs((prev) => {
        const next = [...prev, line];
        return next.length > MAX_LINES ? next.slice(next.length - MAX_LINES) : next;
      });
    };

    return subscribeSSE(getLogsStreamUrl(), {
      onOpen: () => setStatus("connected"),
      onDisconnect: () => setStatus("disconnected"),
      onMessage: (data) => {
        if (pausedRef.current) return;
        const entry = parseLogEvent(data);
        if (isLogEntry(entry)) appendLog(entry);
      },
    });
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (el && sticky) el.scrollTop = el.scrollHeight;
  }, [logs, sticky]);

  useEffect(() => {
    if (!showTools) return;
    void Promise.all([listSnippets(), listCommandHistory(50)])
      .then(([snippetData, historyData]) => {
        setSnippets(snippetData.snippets);
        setCommands(historyData.entries);
      })
      .catch((error: unknown) => {
        setToolsError(error instanceof Error ? error.message : "Terminal tools unavailable");
      });
  }, [showTools]);

  useEffect(() => {
    if (tab !== "history") return;
    let cancelled = false;
    const timer = window.setTimeout(() => {
      void getLogHistory({ limit: 200, search: search || undefined })
        .then((data) => {
          if (!cancelled) setHistoryLogs(data.entries);
        })
        .catch((error: unknown) => {
          if (!cancelled) setToolsError(error instanceof Error ? error.message : "History unavailable");
        });
    }, 150);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [search, tab]);

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    setSticky(el.scrollHeight - el.scrollTop - el.clientHeight < 24);
  };

  const togglePause = () => {
    const next = !paused;
    setPaused(next);
    pausedRef.current = next;
  };

  const clearLogs = () => setLogs([]);

  const refreshTools = useCallback(async () => {
    const [snippetData, historyData] = await Promise.all([
      listSnippets(),
      listCommandHistory(50),
    ]);
    setSnippets(snippetData.snippets);
    setCommands(historyData.entries);
  }, []);

  const handleSaveSnippet = async () => {
    if (!snippetName.trim() || !snippetCommand.trim()) return;
    setBusy(true);
    setToolsError(null);
    try {
      await createSnippet({ name: snippetName.trim(), command: snippetCommand.trim(), description: "" });
      setSnippetName("");
      setSnippetCommand("");
      await refreshTools();
    } catch (error) {
      setToolsError(error instanceof Error ? error.message : "Failed to save snippet");
    } finally {
      setBusy(false);
    }
  };

  const handleRecordCommand = async () => {
    const command = commandInput.trim();
    if (!command) return;
    setBusy(true);
    try {
      await addCommandHistory(command);
      setCommandInput("");
      await refreshTools();
    } catch (error) {
      setToolsError(error instanceof Error ? error.message : "Failed to record command");
    } finally {
      setBusy(false);
    }
  };

  const copy = (value: string) => {
    void navigator.clipboard?.writeText(value);
  };

  const needle = search.trim().toLowerCase();
  const visibleLogs = needle
    ? logs.filter((log) =>
        `${log.level} ${log.agent} ${log.message}`.toLowerCase().includes(needle)
      )
    : logs;

  const statusLabel =
    status === "connected" ? "Streaming" : status === "connecting" ? "Connecting..." : "Disconnected · retrying";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-b border-slate-800 bg-slate-950/50">
        <div className="flex items-center gap-2 text-sm">
          <span
            className={`w-2 h-2 rounded-full ${
              status === "connected"
                ? "bg-green-500"
                : status === "connecting"
                  ? "bg-yellow-500 animate-pulse"
                  : "bg-red-500"
            }`}
          />
          <span className="font-semibold">Live Agent Terminal</span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full border ${
              status === "connected"
                ? "text-green-400 border-green-700/50 bg-green-900/20"
                : status === "connecting"
                  ? "text-yellow-400 border-yellow-700/50 bg-yellow-900/20"
                  : "text-red-400 border-red-700/50 bg-red-900/20"
            }`}
          >
            {statusLabel}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {showTools && (
            <div className="flex rounded-lg border border-slate-800 overflow-hidden text-xs">
              <button
                type="button"
                onClick={() => setTab("live")}
                className={`px-3 py-1.5 ${tab === "live" ? "bg-blue-600/20 text-blue-300" : "text-slate-400 hover:bg-slate-800"}`}
              >
                Live
              </button>
              <button
                type="button"
                onClick={() => setTab("history")}
                className={`px-3 py-1.5 ${tab === "history" ? "bg-blue-600/20 text-blue-300" : "text-slate-400 hover:bg-slate-800"}`}
              >
                History
              </button>
            </div>
          )}
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-500" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search output"
              aria-label="Search terminal output"
              className="w-36 rounded-lg border border-slate-800 bg-slate-950 pl-7 pr-2 py-1.5 text-xs text-slate-200 outline-none focus:border-blue-600"
            />
          </div>
          <button
            onClick={togglePause}
            aria-label={paused ? "Resume log stream" : "Pause log stream"}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs text-slate-300 transition-colors"
          >
            {paused ? <Play className="w-3.5 h-3.5" /> : <CirclePause className="w-3.5 h-3.5" />}
            {paused ? "Resume" : "Pause"}
          </button>
          <button
            onClick={clearLogs}
            aria-label="Clear terminal output"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs text-slate-300 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        onScroll={handleScroll}
        aria-label="Agent log output"
        className="bg-black h-[520px] overflow-y-auto font-mono text-xs p-4 space-y-1.5"
      >
        {(tab === "live" ? visibleLogs : historyLogs).length === 0 ? (
          <div className="flex items-center gap-2 text-slate-500">
            {status === "disconnected" ? (
              <RefreshCw className="w-3.5 h-3.5" />
            ) : (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            )}
            {tab === "history"
              ? "No matching history entries."
              : status === "connected"
                ? "Waiting for agent output..."
                : status === "connecting"
                  ? "Connecting to log stream..."
                  : "Disconnected — waiting to reconnect..."}
          </div>
        ) : (
          (tab === "live" ? visibleLogs : historyLogs).map((log, index) => (
            <div key={tab === "live" ? (log as LogLine).key : `history-${index}`} className="flex items-start gap-3">
              <span className="text-slate-600 shrink-0">
                {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ""}
              </span>
              <span className={`shrink-0 w-14 text-left ${levelClass(log.level)}`}>
                [{log.level.toUpperCase()}]
              </span>
              <span className="text-purple-300 shrink-0">{log.agent}</span>
              <span className="text-slate-300 break-all">{log.message}</span>
            </div>
          ))
        )}
        {tab === "live" && (
          <div className="flex items-center gap-1 text-green-400">
            <RefreshCw className="w-3 h-3 animate-spin" />
            _
          </div>
        )}
      </div>

      {showTools && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 border-t border-slate-800 bg-slate-950/40 p-4">
          <section className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <Bookmark className="w-3.5 h-3.5 text-amber-400" /> Saved snippets
            </div>
            <div className="flex gap-2">
              <input
                value={snippetName}
                onChange={(event) => setSnippetName(event.target.value)}
                placeholder="Name"
                aria-label="Snippet name"
                className="w-1/3 rounded border border-slate-800 bg-slate-950 px-2 py-1.5 text-[11px] outline-none focus:border-blue-600"
              />
              <input
                value={snippetCommand}
                onChange={(event) => setSnippetCommand(event.target.value)}
                placeholder="Command or note"
                aria-label="Snippet command"
                className="flex-1 rounded border border-slate-800 bg-slate-950 px-2 py-1.5 text-[11px] outline-none focus:border-blue-600"
              />
              <button
                type="button"
                disabled={busy || !snippetName.trim() || !snippetCommand.trim()}
                onClick={() => void handleSaveSnippet()}
                className="rounded bg-blue-600 px-2 py-1.5 text-[11px] text-white disabled:opacity-50"
                title="Save snippet"
              >
                <Save className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="max-h-28 space-y-1 overflow-y-auto">
              {snippets.length === 0 ? (
                <div className="text-[11px] text-slate-500">No snippets saved.</div>
              ) : (
                snippets.map((snippet) => (
                  <div key={snippet.id} className="flex items-center gap-2 text-[11px]">
                    <button
                      type="button"
                      onClick={() => copy(snippet.command)}
                      className="flex-1 truncate text-left text-slate-300 hover:text-blue-300"
                      title={snippet.command}
                    >
                      <span className="text-slate-500">{snippet.name}:</span> {snippet.command}
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => void deleteSnippet(snippet.id).then(refreshTools)}
                      className="text-slate-500 hover:text-red-400 disabled:opacity-40"
                      title="Delete snippet"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </section>

          <section className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <History className="w-3.5 h-3.5 text-blue-400" /> Command history
            </div>
            <div className="flex gap-2">
              <input
                value={commandInput}
                onChange={(event) => setCommandInput(event.target.value)}
                placeholder="Record a command"
                aria-label="Command to record"
                className="flex-1 rounded border border-slate-800 bg-slate-950 px-2 py-1.5 text-[11px] outline-none focus:border-blue-600"
              />
              <button
                type="button"
                disabled={busy || !commandInput.trim()}
                onClick={() => void handleRecordCommand()}
                className="rounded bg-slate-800 px-2 py-1.5 text-[11px] text-slate-300 hover:bg-slate-700 disabled:opacity-50"
              >
                Record
              </button>
              <button
                type="button"
                disabled={busy || commands.length === 0}
                onClick={() => void clearCommandHistory().then(refreshTools)}
                className="rounded bg-slate-800 px-2 py-1.5 text-[11px] text-slate-400 hover:text-red-400 disabled:opacity-50"
                title="Clear command history"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="max-h-28 space-y-1 overflow-y-auto font-mono text-[11px]">
              {commands.length === 0 ? (
                <div className="text-slate-500">No commands recorded.</div>
              ) : (
                commands.map((entry) => (
                  <button
                    key={entry.id}
                    type="button"
                    onClick={() => copy(entry.command)}
                    className="flex w-full items-center gap-2 text-left text-slate-400 hover:text-blue-300"
                  >
                    <Copy className="w-3 h-3 shrink-0 text-slate-600" />
                    <span className="truncate">{entry.command}</span>
                  </button>
                ))
              )}
            </div>
          </section>

          <section className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <RefreshCw className="w-3.5 h-3.5 text-emerald-400" /> Tools status
            </div>
            {toolsError ? (
              <div className="rounded border border-red-800/60 bg-red-950/30 p-2 text-[11px] text-red-300">
                {toolsError}
              </div>
            ) : (
              <div className="text-[11px] text-slate-500">
                {snippets.length} snippet(s) · {commands.length} command(s) · {historyLogs.length} persisted log row(s) loaded.
                <br />
                Commands are recorded as notes; no shell execution endpoint is exposed.
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
