"use client";

import { useEffect, useRef, useState } from "react";
import { CirclePause, Play, RefreshCw, Trash2, Loader2 } from "lucide-react";
import { getLogsStreamUrl, parseLogEvent } from "@/lib/api";
import { subscribeSSE } from "@/lib/stream-sse";
import type { LogEntry } from "@/lib/types";

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

export default function LiveTerminal() {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [status, setStatus] = useState<StreamStatus>("connecting");
  const [paused, setPaused] = useState(false);
  const [sticky, setSticky] = useState(true);
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

  const statusLabel =
    status === "connected" ? "Streaming" : status === "connecting" ? "Connecting..." : "Disconnected · retrying";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-950/50">
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
        {logs.length === 0 ? (
          <div className="flex items-center gap-2 text-slate-500">
            {status === "disconnected" ? (
              <RefreshCw className="w-3.5 h-3.5" />
            ) : (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            )}
            {status === "connected"
              ? "Waiting for agent output..."
              : status === "connecting"
                ? "Connecting to log stream..."
                : "Disconnected — waiting to reconnect..."}
          </div>
        ) : (
          logs.map((log) => (
            <div key={log.key} className="flex items-start gap-3">
              <span className="text-slate-600 shrink-0">
                {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ""}
              </span>
              <span
                className={`shrink-0 w-14 text-left ${levelClass(log.level)}`}
              >
                [{log.level.toUpperCase()}]
              </span>
              <span className="text-purple-300 shrink-0">{log.agent}</span>
              <span className="text-slate-300 break-all">{log.message}</span>
            </div>
          ))
        )}
        <div className="flex items-center gap-1 text-green-400">
          <RefreshCw className="w-3 h-3 animate-spin" />
          _
        </div>
      </div>
    </div>
  );
}
