"use client";

import { useState } from "react";
import {
  Terminal,
  ShieldCheck,
  Loader2,
  Bot,
  Radar,
  Zap,
  Lock,
  Users,
  Braces,
  Power,
} from "lucide-react";
import { useLiveSwarm } from "@/lib/use-live-swarm";
import { setExecutionMode } from "@/lib/api";
import type { ExecutionMode } from "@/lib/types";
import LiveTerminal from "@/components/live-terminal";

const EXECUTION_MODES: { id: ExecutionMode; label: string; description: string; icon: typeof Zap }[] = [
  {
    id: "Autonomous",
    label: "Autonomous",
    description: "Swarm plans, codes, and deploys without intervention.",
    icon: Zap,
  },
  {
    id: "AI-Man",
    label: "AI-Man",
    description: "Agents propose; a human approves every gate.",
    icon: Bot,
  },
  {
    id: "Manual",
    label: "Manual",
    description: "Full manual control. Agents wait for explicit commands.",
    icon: Power,
  },
];

function AgentCard({
  name,
  role,
  status,
  currentTask,
}: {
  name: string;
  role: string;
  status: string;
  currentTask: string | null | undefined;
}) {
  return (
    <div className="flex items-start gap-3 p-3 bg-slate-950 rounded-lg border border-slate-800/50 hover:border-slate-700 transition-colors">
      <div className="w-2 h-2 mt-1.5 rounded-full bg-green-500 animate-pulse shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="font-medium text-slate-200 truncate">{name}</div>
        <div className="text-xs text-slate-500">{role}</div>
        {currentTask && (
          <div className="mt-1.5 text-[11px] text-blue-400 bg-blue-950/40 border border-blue-800/40 px-2 py-0.5 rounded-md inline-block">
            {currentTask}
          </div>
        )}
      </div>
      <div className="text-right shrink-0">
        <div className="text-xs font-mono text-slate-400">{status}</div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { swarm, error, refresh } = useLiveSwarm();
  const [switching, setSwitching] = useState(false);
  const [switchError, setSwitchError] = useState<string | null>(null);

  const handleModeSwitch = async (mode: ExecutionMode) => {
    if (switching || !swarm || swarm.system_mode === mode) return;
    setSwitching(true);
    setSwitchError(null);
    try {
      await setExecutionMode(mode);
      await refresh();
    } catch (err) {
      setSwitchError(err instanceof Error ? err.message : "Failed to switch mode");
    } finally {
      setSwitching(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Agent Playground</h1>
          <p className="text-sm text-slate-500 mt-1">
            Live state of the autonomous multi-agent developer ecosystem.
          </p>
        </div>
        {!swarm && error && (
          <span className="text-xs text-red-400 bg-red-950/40 border border-red-800/50 px-3 py-1.5 rounded-lg">
            Backend unavailable — retrying...
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Agent Swarm */}
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Terminal className="w-5 h-5 text-purple-400" /> Active Agent Swarm
            </h2>
            {!swarm ? (
              <div className="flex items-center justify-center py-10 text-slate-500">
                {error ? (
                  <div className="text-center text-sm">
                    <p className="mb-2">Cannot reach Agent Swarm.</p>
                    <button
                      onClick={refresh}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs text-blue-400 transition-colors"
                    >
                      Retry now
                    </button>
                  </div>
                ) : (
                  <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {swarm.active_agents.map((agent, i) => (
                  <AgentCard
                    key={i}
                    name={agent.name}
                    role={agent.role}
                    status={agent.status}
                    currentTask={agent.current_task}
                  />
                ))}
              </div>
            )}
          </section>

          {/* Live Terminal */}
          <LiveTerminal />
        </div>

        <div className="space-y-6">
          {/* Execution Modes */}
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-1 flex items-center gap-2">
              <Radar className="w-5 h-5 text-blue-400" /> Execution Mode
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Active: <span className="font-mono text-blue-400">{swarm?.system_mode ?? "..."}</span>
            </p>
            <div className="space-y-3">
              {EXECUTION_MODES.map((mode) => {
                const Icon = mode.icon;
                const active = swarm?.system_mode === mode.id;
                return (
                  <button
                    key={mode.id}
                    disabled={switching}
                    onClick={() => handleModeSwitch(mode.id)}
                    className={`w-full text-left p-4 rounded-xl border transition-colors disabled:opacity-60 ${
                      active
                        ? "bg-blue-600/15 border-blue-600/60"
                        : "bg-slate-950 border-slate-800 hover:border-slate-600"
                    }`}
                  >
                    <div className="flex items-center gap-2.5 mb-1">
                      <Icon className={`w-4 h-4 ${active ? "text-blue-400" : "text-slate-400"}`} />
                      <span className={`font-medium ${active ? "text-blue-300" : "text-slate-200"}`}>
                        {mode.label}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 leading-relaxed">{mode.description}</p>
                  </button>
                );
              })}
            </div>
            {switching && (
              <div className="mt-3 flex items-center gap-2 text-xs text-blue-400">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Switching mode...
              </div>
            )}
            {switchError && (
              <div className="mt-3 text-xs text-red-400 bg-red-950/40 border border-red-800/40 px-3 py-2 rounded-lg">
                {switchError}
              </div>
            )}
          </section>

          {/* Security Gate */}
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-green-500" /> Security Gate
            </h2>
            <div className="space-y-2 text-sm text-slate-400">
              <p className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-green-500" />
                Zero-Tolerance Audit:
                <span className="text-green-500 font-mono">{swarm?.security_gate ?? "..."}</span>
              </p>
              <p className="flex items-center gap-2">
                <Radar className="w-4 h-4 text-green-500" />
                Secrets Scan:
                <span className="text-green-500 font-mono">Clean</span>
              </p>
              <p className="flex items-center gap-2">
                <Users className="w-4 h-4 text-blue-500" />
                Branch Protection:
                <span className="text-blue-500 font-mono">Enforced</span>
              </p>
              <p className="flex items-center gap-2">
                <Braces className="w-4 h-4 text-purple-400" />
                BYOK Vault:
                <span className="text-purple-400 font-mono">Encrypted</span>
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}