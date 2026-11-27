"use client";

import { useSyncExternalStore } from "react";
import { getSwarm } from "./api";
import type { SwarmResponse } from "./types";

export interface LiveSwarm {
  swarm: SwarmResponse | null;
  error: string | null;
  refresh: () => void;
}

interface SwarmStoreState {
  swarm: SwarmResponse | null;
  error: string | null;
}

// One store and one poll loop shared by every hook consumer.
let state: SwarmStoreState = { swarm: null, error: null };
const listeners = new Set<() => void>();
let inFlight = false;
let pollTimer: ReturnType<typeof setInterval> | null = null;

function emit(): void {
  for (const listener of listeners) listener();
}

async function refreshShared(): Promise<void> {
  if (inFlight) return;
  inFlight = true;
  try {
    const data = await getSwarm();
    state = { swarm: data, error: null };
  } catch (err) {
    state = { ...state, error: err instanceof Error ? err.message : "Failed to reach backend" };
  } finally {
    inFlight = false;
    emit();
  }
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  if (!pollTimer) {
    void refreshShared();
    pollTimer = setInterval(() => {
      void refreshShared();
    }, 5000);
  }

  return () => {
    listeners.delete(listener);
    if (listeners.size === 0 && pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  };
}

function getSnapshot(): SwarmStoreState {
  return state;
}

export function useLiveSwarm(): LiveSwarm {
  const snapshot = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
  return {
    swarm: snapshot.swarm,
    error: snapshot.error,
    refresh: () => refreshShared(),
  };
}
