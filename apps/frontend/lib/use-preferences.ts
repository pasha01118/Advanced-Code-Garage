"use client";

import { useSyncExternalStore } from "react";
import { getPreferences as fetchPreferences, updatePreferences } from "@/lib/api";
import type { PreferencesOut, UpdatePreferencesRequest } from "@/lib/types";

const STORAGE_KEY = "acg:preferences:v1";

const DEFAULTS: PreferencesOut = {
  theme: "dark",
  accent: "blue",
  density: "comfortable",
  reduced_motion: false,
  updated_at: null,
};

let current: PreferencesOut = DEFAULTS;
const listeners = new Set<() => void>();

function applyToDocument(value: PreferencesOut): void {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.dataset.theme = value.theme;
  root.dataset.accent = value.accent;
  root.dataset.density = value.density;
  root.dataset.reducedMotion = String(value.reduced_motion);
  root.style.colorScheme = value.theme;
}

function writeLocal(value: PreferencesOut): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  } catch {
    // Storage can be disabled; preferences still work for this session.
  }
}

function commit(next: PreferencesOut): void {
  current = next;
  applyToDocument(next);
  writeLocal(next);
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot(): PreferencesOut {
  return current;
}

function getServerSnapshot(): PreferencesOut {
  return DEFAULTS;
}

export function usePreferences(): PreferencesOut {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

export async function hydratePreferences(): Promise<void> {
  if (typeof window !== "undefined") {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<PreferencesOut>;
        commit({ ...DEFAULTS, ...parsed });
      } else {
        applyToDocument(current);
      }
    } catch {
      applyToDocument(current);
    }
  }

  try {
    const remote = await fetchPreferences();
    commit({ ...DEFAULTS, ...remote });
  } catch {
    // Anonymous users keep their local preferences.
  }
}

export async function savePreferences(patch: UpdatePreferencesRequest): Promise<void> {
  const clean = Object.fromEntries(
    Object.entries(patch).filter(([, value]) => value !== undefined && value !== null)
  ) as Partial<PreferencesOut>;
  commit({ ...current, ...clean });
  try {
    const remote = await updatePreferences(patch);
    commit({ ...current, ...remote });
  } catch {
    // Keep the local change when the API is unavailable.
  }
}
