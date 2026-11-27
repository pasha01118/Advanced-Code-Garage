"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ChevronsUpDown, Loader2, LogOut, UserRound } from "lucide-react";
import { supabase } from "@/lib/supabaseClient";

type AccountAction = "logout" | "switch";

/** Only internal paths are safe to return to after signing in again. */
function safeReturnPath(pathname: string): string {
  if (!pathname.startsWith("/") || pathname.startsWith("//") || pathname.includes("\\")) {
    return "/";
  }
  return pathname === "/login" ? "/" : pathname;
}

export function ProfileMenu({ email }: { email?: string | null }) {
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState<AccountAction | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!open) return;

    const onPointerDown = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const signOut = async (action: AccountAction) => {
    if (pending) return;
    setPending(action);
    setOpen(false);

    try {
      if (supabase) {
        // Global sign-out invalidates other sessions too. If the server call
        // fails (e.g. offline), still clear this browser so switching works.
        const { error } = await supabase.auth.signOut({ scope: "global" });
        if (error) await supabase.auth.signOut({ scope: "local" });
      }
    } finally {
      const next = safeReturnPath(pathname);
      router.replace(
        action === "switch"
          ? `/login?reason=switch&next=${encodeURIComponent(next)}`
          : "/login?reason=logout",
      );
    }
  };

  const initial = email?.trim().charAt(0)?.toUpperCase() || "?";

  return (
    <div ref={containerRef} className="relative shrink-0">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Account menu"
        className="flex max-w-[14rem] items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/70 px-2 py-1.5 text-xs text-slate-300 transition hover:border-slate-700 hover:bg-slate-800/70"
      >
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-600/20 text-blue-300">
          {initial}
        </span>
        <span className="hidden truncate sm:inline">{email || "Account"}</span>
        <ChevronsUpDown className="h-3.5 w-3.5 shrink-0 text-slate-500" />
      </button>

      {open && (
        <div
          role="menu"
          aria-label="Account actions"
          className="absolute right-0 top-full z-50 mt-2 w-64 overflow-hidden rounded-lg border border-slate-800 bg-slate-900 shadow-xl"
        >
          <div className="border-b border-slate-800 px-3 py-2.5">
            <p className="text-[11px] uppercase tracking-wide text-slate-500">Signed in as</p>
            <p className="mt-0.5 truncate text-sm text-slate-200">{email || "Unknown account"}</p>
          </div>
          <button
            type="button"
            role="menuitem"
            disabled={pending !== null}
            onClick={() => void signOut("switch")}
            className="flex w-full items-center gap-2.5 px-3 py-2.5 text-left text-sm text-slate-300 transition hover:bg-slate-800 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {pending === "switch" ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <UserRound className="h-4 w-4" />
            )}
            Switch Profile
          </button>
          <button
            type="button"
            role="menuitem"
            disabled={pending !== null}
            onClick={() => void signOut("logout")}
            className="flex w-full items-center gap-2.5 border-t border-slate-800 px-3 py-2.5 text-left text-sm text-slate-300 transition hover:bg-slate-800 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {pending === "logout" ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <LogOut className="h-4 w-4" />
            )}
            Log Out
          </button>
        </div>
      )}
    </div>
  );
}
