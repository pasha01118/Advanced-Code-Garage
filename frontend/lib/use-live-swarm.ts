"use client";

import { useEffect, useRef, useState } from "react";
import { getSwarm } from "./api";
import type { SwarmResponse } from "./types";

export interface LiveSwarm {
  swarm: SwarmResponse | null;
  error: string | null;
  refresh: () => void;
}

export function useLiveSwarm(): LiveSwarm {
  const [swarm, setSwarm] = useState<SwarmResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);
  const mountedRef = useRef(true);

  const refresh = async () => {
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    try {
      const data = await getSwarm();
      if (mountedRef.current) {
        setSwarm(data);
        setError(null);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : "Failed to reach backend");
      }
    } finally {
      inFlightRef.current = false;
    }
  };

  useEffect(() => {
    mountedRef.current = true;
    const interval = setInterval(() => {
      refresh();
    }, 5000);

    const boot = setTimeout(() => {
      refresh();
    }, 0);

    return () => {
      mountedRef.current = false;
      clearInterval(interval);
      clearTimeout(boot);
    };
  }, []);

  return { swarm, error, refresh };
}