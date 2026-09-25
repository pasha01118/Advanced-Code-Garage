"use client";

import { useEffect, useState } from "react";
import { X, Wrench, Power } from "lucide-react";
import { getAppState } from "@/lib/api";

interface AppState {
  status: "running" | "maintenance" | "shutdown";
  message: string;
  toggles: Record<string, boolean>;
}

export function SystemBanner() {
  const [state, setState] = useState<AppState | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    async function fetchState() {
      try {
        const s = await getAppState();
        setState(s);
      } catch {
        // silently fail
      }
    }
    fetchState();
    const interval = setInterval(fetchState, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!state || state.status === "running" || dismissed) return null;

  const isMaintenance = state.status === "maintenance";
  const Icon = isMaintenance ? Wrench : Power;
  const bgColor = isMaintenance ? "bg-yellow-900/30 border-yellow-700/50" : "bg-red-900/30 border-red-700/50";
  const textColor = isMaintenance ? "text-yellow-300" : "text-red-300";
  const iconColor = isMaintenance ? "text-yellow-400" : "text-red-400";

  return (
    <div className={`${bgColor} border ${textColor} fixed top-0 left-0 right-0 z-50 px-4 py-2`}>
      <div className="max-w-7xl mx-auto flex items-center gap-3">
        <Icon className={`w-5 h-5 ${iconColor} shrink-0`} />
        <div className="flex-1 text-sm">
          <span className="font-medium">
            {isMaintenance ? "Maintenance Mode" : "Service Shutdown"}
          </span>
          {state.message && <span className="ml-2">{state.message}</span>}
        </div>
        <button
          onClick={() => setDismissed(true)}
          className={`${textColor} hover:text-white transition-colors p-1`}
          aria-label="Dismiss banner"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}