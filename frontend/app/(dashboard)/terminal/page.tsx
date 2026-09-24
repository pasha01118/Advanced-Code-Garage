"use client";

import { SquareTerminal, Cpu, Bot, Users } from "lucide-react";
import LiveTerminal from "@/components/live-terminal";
import { useLiveSwarm } from "@/lib/use-live-swarm";

export default function TerminalPage() {
  const { swarm } = useLiveSwarm();

  const stats = [
    { icon: Cpu, label: "Active Agents", value: swarm?.active_agents.length ?? "—" },
    { icon: Bot, label: "Execution Mode", value: swarm?.system_mode ?? "—" },
    { icon: Users, label: "Security Gate", value: swarm?.security_gate ?? "—" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <SquareTerminal className="w-6 h-6 text-green-400" /> Realtime Terminal
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Live output streamed from the agent swarm over SSE.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-3">
              <div className="p-2 bg-slate-950 rounded-lg">
                <Icon className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <div className="text-xs text-slate-500">{stat.label}</div>
                <div className="font-mono text-slate-200">{stat.value}</div>
              </div>
            </div>
          );
        })}
      </div>

      <LiveTerminal />
    </div>
  );
}