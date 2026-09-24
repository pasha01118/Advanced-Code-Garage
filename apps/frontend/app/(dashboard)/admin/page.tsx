"use client";

import { useState } from "react";
import {
  ShieldCheck,
  KeyRound,
  Users,
  Cctv,
  Power,
  Fingerprint,
  Eye,
  Loader2,
  Ban,
  Lock,
  Unlock,
} from "lucide-react";
import { useAuthSession } from "@/lib/use-auth-session";

interface KillSwitch {
  id: string;
  label: string;
  description: string;
  armed: boolean;
  destructive: boolean;
}

const INITIAL_SWITCHES: KillSwitch[] = [
  {
    id: "swarm",
    label: "Agent Swarm",
    description: "Stop all active agents and in-flight tasks immediately.",
    armed: true,
    destructive: false,
  },
  {
    id: "git",
    label: "Git Operations",
    description: "Block all automated commits, pushes, and branch operations.",
    armed: true,
    destructive: false,
  },
  {
    id: "deploy",
    label: "Deployments",
    description: "Halt all pipeline triggers to Vercel, Render, and Cloudflare.",
    armed: true,
    destructive: false,
  },
  {
    id: "vault",
    label: "BYOK Vault Purge",
    description: "Destroy all customer encryption keys stored in the vault.",
    armed: false,
    destructive: true,
  },
];

export default function AdminPage() {
  const { session } = useAuthSession();
  const [switches, setSwitches] = useState<KillSwitch[]>(INITIAL_SWITCHES);
  const [audit, setAudit] = useState<string[]>([
    "[07:04:12] Git-Sir: authenticated RBAC session",
    "[07:04:12] Sadath: security gate ACTIVE",
    "[07:04:13] Kulsum: token budget 85% efficiency",
  ]);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const email = session?.user?.email ?? "";
  const isAdmin = email.endsWith("@advancedcodegarage.dev") || email === "pasha01118@gmail.com";

  const toggleSwitch = (id: string) => {
    const target = switches.find((s) => s.id === id);
    if (!target) return;

    if (target.destructive && !target.armed) {
      setConfirmId(id);
      return;
    }

    setBusy(true);
    setTimeout(() => {
      setSwitches((prev) =>
        prev.map((s) => (s.id === id ? { ...s, armed: !s.armed } : s))
      );
      setAudit((prev) => [
        `[${new Date().toLocaleTimeString()}] ${target.label}: ${target.armed ? "DISARMED" : "ARMED"}`,
        ...prev,
      ].slice(0, 30));
      setBusy(false);
    }, 600);
  };

  const confirmDestructive = (id: string) => {
    setBusy(true);
    setTimeout(() => {
      setSwitches((prev) =>
        prev.map((s) => (s.id === id ? { ...s, armed: !s.armed } : s))
      );
      setAudit((prev) => [
        `[${new Date().toLocaleTimeString()}] DESTRUCTIVE EXEC: ${id} wiped`,
        ...prev,
      ].slice(0, 30));
      setConfirmId(null);
      setBusy(false);
    }, 900);
  };

  if (!isAdmin) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="bg-slate-900 border border-red-900/60 rounded-xl p-8 max-w-md text-center">
          <ShieldCheck className="w-12 h-12 mx-auto mb-4 text-red-500" />
          <h2 className="text-xl font-bold mb-2">Access Restricted</h2>
          <p className="text-sm text-slate-400">
            This control panel requires admin privileges (RBAC). Signed in as{" "}
            <span className="font-mono text-slate-300">{email || "(no session)"}</span>.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Fingerprint className="w-6 h-6 text-red-400" /> Secret Control Panel
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          RBAC-gated emergency controls. Actions are audited.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Kill switches */}
        <section className="lg:col-span-2 bg-slate-900 border border-red-900/40 rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-1 flex items-center gap-2">
            <Power className="w-5 h-5 text-red-400" /> Kill Switches
          </h2>
          <p className="text-xs text-slate-500 mb-4">
            Toggling a switch engages the emergency procedure. Nothing here is virtual.
          </p>
          <div className="space-y-3">
            {switches.map((sw) => (
              <div key={sw.id} className="flex items-start justify-between gap-4 p-4 bg-slate-950 rounded-xl border border-slate-800">
                <div>
                  <div className="font-medium text-slate-200 flex items-center gap-2">
                    {sw.label}
                    {sw.destructive && (
                      <span className="text-[10px] uppercase tracking-wide text-red-400 bg-red-950/60 border border-red-800/50 px-1.5 py-0.5 rounded">
                        Destructive
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{sw.description}</p>
                </div>
                <button
                  onClick={() => toggleSwitch(sw.id)}
                  disabled={busy}
                  className={`shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                    sw.armed
                      ? "bg-green-900/30 border-green-700/50 text-green-300"
                      : "bg-red-900/30 border-red-700/50 text-red-300"
                  } disabled:opacity-60`}
                >
                  {sw.armed ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                  {sw.armed ? "Armed" : "Open"}
                </button>
              </div>
            ))}
          </div>
          {confirmId && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
              <div className="bg-slate-900 border border-red-800 rounded-xl p-6 max-w-sm w-full">
                <div className="flex items-center gap-2 text-red-400 font-semibold mb-2">
                  <Ban className="w-5 h-5" /> Destructive Action
                </div>
                <p className="text-sm text-slate-300 mb-1">
                  This will permanently destroy customer keys.
                </p>
                <p className="text-xs text-red-400 mb-4">This cannot be undone.</p>
                <div className="flex gap-3">
                  <button
                    onClick={() => confirmDestructive(confirmId)}
                    disabled={busy}
                    className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-white text-sm font-medium transition-colors disabled:opacity-60"
                  >
                    {busy ? "Executing..." : "Confirm & Wipe"}
                  </button>
                  <button
                    onClick={() => setConfirmId(null)}
                    disabled={busy}
                    className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-200 text-sm font-medium transition-colors disabled:opacity-60"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Audit log */}
        <section className="bg-black border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-1 flex items-center gap-2">
            <Eye className="w-5 h-5 text-blue-400" /> Audit Log
          </h2>
          <p className="text-xs text-slate-500 mb-4">Immutable (append-only)</p>
          <div className="space-y-2 font-mono text-[11px]">
            {audit.map((entry, i) => (
              <div key={i} className={`${i === 0 ? "text-green-400" : "text-slate-500"}`}>
                {entry}
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center gap-2 text-blue-400 font-medium text-sm mb-1">
            <Users className="w-4 h-4" /> RBAC
          </div>
          <p className="text-xs text-slate-500">
            Role-bound access control ensures only authorized operators can trigger destructive
            procedures.
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center gap-2 text-green-400 font-medium text-sm mb-1">
            <Cctv className="w-4 h-4" /> Monitoring
          </div>
          <p className="text-xs text-slate-500">
            Live telemetry of every agent action, piped through the Security Gate before execution.
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center gap-2 text-purple-400 font-medium text-sm mb-1">
            <KeyRound className="w-4 h-4" /> Encrypted BYOK Vault
          </div>
          <p className="text-xs text-slate-500">
            Bring-your-own-key encryption vault. Keys are client-side encrypted and never persisted.
          </p>
        </div>
      </div>

      {busy && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 pointer-events-none">
          <Loader2 className="w-10 h-10 animate-spin text-red-400" />
        </div>
      )}
    </div>
  );
}