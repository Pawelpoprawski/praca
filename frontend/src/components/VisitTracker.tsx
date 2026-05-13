"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import api from "@/services/api";

/**
 * Logs one visit per pathname change. Best-effort, swallows errors.
 * Skips /admin and /panel/* (we don't want owner clicks polluting visit stats).
 */
export default function VisitTracker() {
  const pathname = usePathname();
  const sentRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!pathname) return;
    if (pathname.startsWith("/admin")) return;
    if (pathname.startsWith("/panel")) return;
    if (sentRef.current.has(pathname)) return;
    sentRef.current.add(pathname);

    const ref = typeof document !== "undefined" ? document.referrer || null : null;

    api
      .post("/track/visit", { path: pathname, referrer: ref })
      .catch(() => {
        // Best-effort; don't break the page if backend is down
      });
  }, [pathname]);

  return null;
}
