"use client";

import { useEffect, useRef, useState } from "react";
import { CirclePause, Play, RefreshCw, Trash2, Loader2 } from "lucide-react";
import { getLogsStreamUrl, parseLogEvent } from "@/lib/api";
import type { LogEntry } from "@/lib/types";

const MAX_LINES = 300;

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
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const [paused, setPaused] = useState(false);
  const pausedRef = useRef(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const stickRef = useRef(true);

  const appendLog = (entry: LogEntry) => {
    setLogs((prev) => {
      const next = [...prev, entry];
      return next.length > MAX_LINES ? next.slice(next.length - MAX_LINES) : next;
    });
  };

  useEffect(() => {
    const source = new EventSource(getLogsStreamUrl());

    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);

    source.onmessage = (event) => {
      if (pausedRef.current) return;
      const entry = parseLogEvent(event.data);
      if (entry) appendLog(entry);
    };

    return () => {
      source.close();
      setConnected(false);
    };
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (el && stickRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [logs]);

  const togglePause = () => {
    const next = !paused;
    setPaused(next);
    pausedRef.current = next;
  };

  const clearLogs = () => {
    setLogs([]);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-950/50">
        <div className="flex items-center gap-2 text-sm">
          <span
            className={`w-2 h-2 rounded-full ${
              connected ? "bg-green-500" : "bg-red-500 animate-pulse"
            }`}
          />
          <span className="font-semibold">Live Agent Terminal</span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full border ${
              connected
                ? "text-green-400 border-green-700/50 bg-green-900/20"
                : "text-red-400 border-red-700/50 bg-red-900/20"
            }`}
          >
            {connected ? "Streaming" : "Reconnecting..."}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={togglePause}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs text-slate-300 transition-colors"
          >
            {paused ? <Play className="w-3.5 h-3.5" /> : <CirclePause className="w-3.5 h-3.5" />}
            {paused ? "Resume" : "Pause"}
          </button>
          <button
            onClick={clearLogs}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs text-slate-300 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear
          </button>
        </div>
      </div>

      <div ref={scrollRef} className="bg-black h-[520px] overflow-y-auto font-mono text-xs p-4 space-y-1.5">
        {logs.length === 0 ? (
          <div className="flex items-center gap-2 text-slate-500">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Waiting for agent output...
          </div>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="flex items-start gap-3">
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