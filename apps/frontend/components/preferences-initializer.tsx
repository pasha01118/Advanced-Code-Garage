"use client";

import { useEffect } from "react";
import { hydratePreferences } from "@/lib/use-preferences";

export function PreferencesInitializer() {
  useEffect(() => {
    void hydratePreferences();
  }, []);
  return null;
}
