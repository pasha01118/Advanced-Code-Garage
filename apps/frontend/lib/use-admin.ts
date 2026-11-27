"use client";

import { useEffect, useState } from "react";
import { getAuthMe } from "./api";

/**
 * Effective admin status as decided by the backend (app_metadata.role or the
 * ADMIN_USER_IDS allowlist). Signed-in users without either are not admins.
 */
export function useIsAdmin(enabled: boolean): boolean {
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    let alive = true;
    void Promise.resolve().then(() => {
      if (!alive) return;
      setIsAdmin(false);
      if (!enabled) return;
      getAuthMe()
        .then((me) => {
          if (alive) setIsAdmin(me.is_admin);
        })
        .catch(() => {
          if (alive) setIsAdmin(false);
        });
    });
    return () => {
      alive = false;
    };
  }, [enabled]);

  return isAdmin;
}
