"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { bootstrapAdmin } from "@/lib/api";
import { useRouter } from "next/navigation";
import { Cpu, Mail, Lock, User, Loader2, AlertCircle, ShieldCheck } from "lucide-react";

type Mode = "signin" | "signup" | "admin";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [mode, setMode] = useState<Mode>("signin");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const router = useRouter();

  const isSignUp = mode === "signup";
  const isAdmin = mode === "admin";

  const configErrorMessage = !supabase
    ? "Supabase not configured. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables."
    : null;

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!supabase && mode !== "admin") {
      setError("Supabase client not initialized. Check environment variables.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (isAdmin) {
        const result = await bootstrapAdmin({
          email,
          password,
          ...(name ? { name } : {}),
        });
        setSuccess(`${result.message} Signing you in as ${result.email} (${result.role}).`);
        const { error: signInError } = await supabase!.auth.signInWithPassword({ email, password });
        if (signInError) throw signInError;
        router.push("/");
      } else if (isSignUp) {
        const { error } = await supabase!.auth.signUp({ email, password });
        if (error) throw error;
        alert("Check your email for the confirmation link!");
      } else {
        const { error } = await supabase!.auth.signInWithPassword({ email, password });
        if (error) throw error;
        router.push("/");
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Authentication failed";
      if (message === "Failed to fetch") {
        setError("Could not reach the app server. Make sure the backend is running and try again.");
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setError(null);
    setSuccess(null);
    if (mode === "signup") setMode("signin");
    else if (mode === "admin") setMode("signin");
    else setMode("signup");
  };

  const goAdminMode = () => {
    setError(null);
    setSuccess(null);
    setMode("admin");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl">
        <div className="flex flex-col items-center mb-8">
          <Cpu className="w-12 h-12 text-blue-500 mb-4" />
          <h1 className="text-2xl font-bold text-white">Advanced Code Garage</h1>
          <p className="text-slate-400 text-sm mt-2">
            {isAdmin
              ? "First-run Admin account setup (no confirmation email)"
              : "Sign in to access the Agent Swarm"}
          </p>
        </div>

        {configErrorMessage && (
          <div className="mb-4 p-3 bg-amber-900/50 border border-amber-800 text-amber-200 text-sm rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {configErrorMessage}
          </div>
        )}

        {isAdmin && (
          <div className="mb-4 p-3 bg-emerald-950/60 border border-emerald-800/60 text-emerald-200 text-sm rounded-lg flex items-start gap-2">
            <ShieldCheck className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>
              Creates the platform admin directly in-app — confirmation email bypassed. Only allowed
              while no admin exists yet.
            </span>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-900/50 border border-red-800 text-red-200 text-sm rounded-lg">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-green-900/50 border border-green-800 text-green-200 text-sm rounded-lg">
            {success}
          </div>
        )}

        <form onSubmit={handleAuth} className="space-y-4">
          {isAdmin && (
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Display Name <span className="text-slate-500">(optional)</span>
              </label>
              <div className="relative">
                <User className="absolute left-3 top-3 w-5 h-5 text-slate-500" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="Operator Name"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 w-5 h-5 text-slate-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-lg py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="developer@example.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 w-5 h-5 text-slate-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={isAdmin ? 8 : undefined}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg py-2.5 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full text-white font-medium py-2.5 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed ${
              isAdmin ? "bg-emerald-700 hover:bg-emerald-600" : "bg-blue-600 hover:bg-blue-500"
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Processing...
              </>
            ) : isAdmin ? (
              "Create Admin Account"
            ) : isSignUp ? (
              "Sign Up"
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        <div className="mt-6 text-center space-y-2">
          <button
            onClick={toggleMode}
            className="text-sm text-blue-400 hover:text-blue-300 transition"
          >
            {mode === "signup" && "Already have an account? Sign In"}
            {mode === "admin" && "Back to Sign In"}
            {mode === "signin" && "Don't have an account? Sign Up"}
          </button>
          {mode !== "admin" && (
            <div>
              <button
                onClick={goAdminMode}
                className="inline-flex items-center gap-1.5 text-sm text-emerald-400 hover:text-emerald-300 transition"
              >
                <ShieldCheck className="w-4 h-4" />
                Admin Sign-Up (first boot)
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}