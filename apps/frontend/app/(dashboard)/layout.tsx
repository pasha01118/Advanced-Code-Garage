"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Cpu,
  LayoutDashboard,
  SquareTerminal,
  FolderGit2,
  ShieldCheck,
  Sparkles,
  LogOut,
  Loader2,
  Activity,
} from "lucide-react";
import { useAuthSession } from "@/lib/use-auth-session";
import { useLiveSwarm } from "@/lib/use-live-swarm";
import { supabase } from "@/lib/supabaseClient";
import { SystemBanner } from "@/components/SystemBanner";

const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/terminal", label: "Terminal", icon: SquareTerminal },
  { href: "/projects", label: "Projects", icon: FolderGit2 },
  { href: "/ai-integration", label: "AI Integration", icon: Sparkles },
  { href: "/admin", label: "Control Panel", icon: ShieldCheck, admin: true },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { session, loading } = useAuthSession();
  const { swarm } = useLiveSwarm();
  const pathname = usePathname();
  const router = useRouter();
  const redirectedRef = useRef(false);

  const email = session?.user?.email ?? "";
  const role = session?.user?.app_metadata?.role;
  const isAdmin = role === "admin" || email.endsWith("@advancedcodegarage.dev") || email === "pasha01118@gmail.com";

  useEffect(() => {
    if (!loading && !session && !redirectedRef.current) {
      redirectedRef.current = true;
      router.replace("/login");
    }
  }, [loading, session, router]);

  if (loading || !session) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      <SystemBanner />
      <aside className="w-56 shrink-0 border-r border-slate-800 bg-slate-900/40 hidden md:flex flex-col">
        <div className="h-16 border-b border-slate-800 flex items-center gap-2 px-4">
          <Cpu className="w-6 h-6 text-blue-500" />
          <div>
            <div className="font-bold leading-tight">Advanced</div>
            <div className="font-bold leading-tight text-blue-400">Code Garage</div>
          </div>
        </div>
        <nav className="flex-1 py-4 px-3 space-y-1">
          {NAV_ITEMS
            .filter((item) => !item.admin || isAdmin)
            .map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                    active
                      ? "bg-blue-600/15 text-blue-400 border border-blue-700/40"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
        </nav>
        <div className="p-3 border-t border-slate-800">
          <div className="text-xs text-slate-500 truncate mb-2">{session?.user?.email}</div>
          <button
            onClick={async () => {
              await supabase?.auth.signOut();
              router.replace("/login");
            }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs text-slate-300 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 sticky top-0 z-40 border-b border-slate-800 bg-slate-950/80 backdrop-blur">
          <div className="h-full max-w-7xl mx-auto px-4 md:px-6 flex items-center justify-between gap-4">
            <div className="flex md:hidden items-center gap-2">
              <Cpu className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-bold">ACG</span>
            </div>
            <div className="hidden md:flex items-center gap-2 text-sm text-slate-400">
              <Activity className="w-4 h-4 text-green-500" />
              {swarm ? (
                <span>
                  System Online · Mode:{" "}
                  <span className="font-mono text-blue-400">{swarm.system_mode}</span>
                </span>
              ) : (
                <span>System Online</span>
              )}
            </div>
            <nav className="flex md:hidden items-center gap-1">
              {NAV_ITEMS
                .filter((item) => !item.admin || isAdmin)
                .map((item) => {
                  const Icon = item.icon;
                  const active = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`p-2 rounded-lg ${active ? "text-blue-400" : "text-slate-500"}`}
                    >
                      <Icon className="w-5 h-5" />
                    </Link>
                  );
                })}
            </nav>
          </div>
        </header>
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}