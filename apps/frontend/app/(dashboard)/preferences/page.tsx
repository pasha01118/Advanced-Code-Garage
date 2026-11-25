"use client";

import { useState } from "react";
import { Check, Loader2, Palette, Settings2 } from "lucide-react";
import type { Accent, Density, Theme } from "@/lib/types";
import { savePreferences, usePreferences } from "@/lib/use-preferences";

const THEMES: { id: Theme; label: string; hint: string }[] = [
  { id: "dark", label: "Dark", hint: "Low-light workspace" },
  { id: "light", label: "Light", hint: "Bright workspace" },
];
const ACCENTS: { id: Accent; label: string; dot: string }[] = [
  { id: "blue", label: "Blue", dot: "bg-blue-500" },
  { id: "emerald", label: "Emerald", dot: "bg-emerald-500" },
  { id: "violet", label: "Violet", dot: "bg-violet-500" },
  { id: "amber", label: "Amber", dot: "bg-amber-500" },
];
const DENSITIES: { id: Density; label: string; hint: string }[] = [
  { id: "comfortable", label: "Comfortable", hint: "Generous spacing" },
  { id: "compact", label: "Compact", hint: "Fit more on screen" },
];

export default function PreferencesPage() {
  const prefs = usePreferences();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const apply = async (patch: Partial<typeof prefs>) => {
    setBusy(true);
    setMessage(null);
    try {
      await savePreferences(patch);
      setMessage("Preferences saved");
    } catch {
      setMessage("Saved locally — sync unavailable");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Settings2 className="w-6 h-6 text-blue-400" /> Preferences
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Personalize the workspace. Settings sync to your account when the API is available.
        </p>
      </div>
      {message && <div className="rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-xs text-slate-300">{message}</div>}

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
          <Palette className="w-4 h-4 text-purple-400" /> Appearance
        </h2>
        <div className="grid grid-cols-2 gap-3">
          {THEMES.map((theme) => (
            <OptionButton
              key={theme.id}
              active={prefs.theme === theme.id}
              disabled={busy}
              label={theme.label}
              hint={theme.hint}
              onClick={() => void apply({ theme: theme.id })}
            />
          ))}
        </div>
        <div className="mt-5 text-xs text-slate-500 mb-2">Accent colour</div>
        <div className="grid grid-cols-4 gap-3">
          {ACCENTS.map((accent) => (
            <button
              key={accent.id}
              type="button"
              disabled={busy}
              onClick={() => void apply({ accent: accent.id })}
              className={`flex flex-col items-center gap-2 rounded-lg border p-3 text-xs disabled:opacity-60 ${
                prefs.accent === accent.id
                  ? "border-blue-600/60 bg-blue-600/10 text-slate-100"
                  : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-600"
              }`}
            >
              <span className={`w-4 h-4 rounded-full ${accent.dot}`} />
              {accent.label}
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-sm font-semibold mb-4">Layout density</h2>
        <div className="grid grid-cols-2 gap-3">
          {DENSITIES.map((density) => (
            <OptionButton
              key={density.id}
              active={prefs.density === density.id}
              disabled={busy}
              label={density.label}
              hint={density.hint}
              onClick={() => void apply({ density: density.id })}
            />
          ))}
        </div>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <label className="flex items-center justify-between gap-4 cursor-pointer">
          <div>
            <div className="text-sm font-medium text-slate-200">Reduce motion</div>
            <div className="text-xs text-slate-500 mt-0.5">Disable animations and transitions.</div>
          </div>
          <input
            type="checkbox"
            checked={prefs.reduced_motion}
            disabled={busy}
            onChange={(event) => void apply({ reduced_motion: event.target.checked })}
            className="w-4 h-4 accent-blue-600"
          />
        </label>
      </section>
      {busy && <div className="text-xs text-slate-500 flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" /> Saving…</div>}
    </div>
  );
}

function OptionButton({
  active,
  disabled,
  label,
  hint,
  onClick,
}: {
  active: boolean;
  disabled: boolean;
  label: string;
  hint: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`flex items-center justify-between rounded-lg border px-4 py-3 text-left disabled:opacity-60 ${
        active
          ? "border-blue-600/60 bg-blue-600/10"
          : "border-slate-800 bg-slate-950 hover:border-slate-600"
      }`}
    >
      <span>
        <span className="block text-sm text-slate-200">{label}</span>
        <span className="block text-[11px] text-slate-500">{hint}</span>
      </span>
      {active && <Check className="w-4 h-4 text-blue-400" />}
    </button>
  );
}
