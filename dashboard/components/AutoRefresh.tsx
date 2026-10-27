"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

const ACTIVE_STATUSES = new Set([
  "created",
  "discovering",
  "scoring",
  "awaiting_batch_approval",
  "building",
  "deploying",
  "outreaching",
]);

// Re-fetches the page while the pipeline is still moving, so newly built
// pages show up without a manual reload.
export default function AutoRefresh({ status }: { status: string }) {
  const router = useRouter();
  useEffect(() => {
    if (!ACTIVE_STATUSES.has(status)) return;
    const id = setInterval(() => router.refresh(), 10000);
    return () => clearInterval(id);
  }, [status, router]);
  return null;
}
