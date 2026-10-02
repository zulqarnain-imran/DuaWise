"use client";

import { useEffect } from "react";

/**
 * Registers the service worker after load.
 *
 * Registration is skipped in development: a cached shell makes hot reload serve
 * stale modules, which is confusing rather than helpful while iterating.
 */
export function ServiceWorkerRegistration() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") return;
    if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) return;

    const register = () => {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        // Offline support is a progressive enhancement; failure must not surface.
      });
    };

    if (document.readyState === "complete") {
      register();
    } else {
      window.addEventListener("load", register, { once: true });
    }
  }, []);

  return null;
}
