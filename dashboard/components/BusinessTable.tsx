"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Business } from "@/lib/data";
import { CampaignStatusBadge } from "./StatusBadge";

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-text-muted text-xs">no site</span>;
  const color =
    score >= 70 ? "text-emerald-700 bg-emerald-50" : score >= 40 ? "text-amber-700 bg-amber-50" : "text-red-600 bg-red-50";
  return (
    <span className={`inline-flex items-center justify-center text-xs font-bold rounded-md px-2 py-0.5 ${color}`}>
      {score}
    </span>
  );
}

export default function BusinessTable({ businesses }: { businesses: Business[] }) {
  const router = useRouter();
  const [pending, setPending] = useState<string | null>(null);

  async function decide(businessId: string, status: "approved" | "rejected" | null) {
    setPending(businessId);
    await fetch("/api/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ business_id: businessId, status }),
    });
    setPending(null);
    router.refresh();
  }

  async function approvePage(businessId: string, approved: boolean) {
    setPending(businessId);
    await fetch("/api/page-approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ business_id: businessId, approved }),
    });
    setPending(null);
    router.refresh();
  }

  if (businesses.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-xl p-8 text-center text-text-muted text-sm">
        No businesses in this bucket.
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-bg border-b border-border text-left text-text-muted text-xs uppercase tracking-wide">
              <th className="px-4 py-3 font-semibold">Business</th>
              <th className="px-4 py-3 font-semibold">Score</th>
              <th className="px-4 py-3 font-semibold">Rating</th>
              <th className="px-4 py-3 font-semibold">Contact</th>
              <th className="px-4 py-3 font-semibold">Campaign</th>
              <th className="px-4 py-3 font-semibold">Demo</th>
              <th className="px-4 py-3 font-semibold text-right">Decision</th>
            </tr>
          </thead>
          <tbody>
            {businesses.map((b) => {
              const busy = pending === b.business_id;
              return (
                <tr key={b.business_id} className="border-b border-border last:border-0 hover:bg-bg transition-colors align-top">
                  <td className="px-4 py-3">
                    <div className="font-semibold text-navy">{b.business_name}</div>
                    <div className="text-text-muted text-xs">{b.category}</div>
                    {b.website_url && (
                      <a
                        href={b.website_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-teal text-xs hover:underline"
                      >
                        {new URL(b.website_url).hostname.replace("www.", "")}
                      </a>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <ScoreBadge score={b.website_score} />
                  </td>
                  <td className="px-4 py-3 text-text-secondary text-xs">
                    {b.google_rating ? (
                      <>
                        ★ {b.google_rating.toFixed(1)}
                        <span className="text-text-muted"> ({b.google_review_count ?? 0})</span>
                      </>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-4 py-3 text-text-secondary text-xs">
                    {b.email_primary ?? "—"}
                    <div>{b.phone_primary ?? ""}</div>
                  </td>
                  <td className="px-4 py-3">
                    <CampaignStatusBadge status={b.campaign_status} />
                  </td>
                  <td className="px-4 py-3">
                    {b.demo_url ? (
                      <div className="flex flex-col gap-1.5 items-start">
                        <a
                          href={b.demo_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-teal text-xs font-medium hover:underline"
                        >
                          Preview →
                        </a>
                        {b.demo_approved ? (
                          <span className="text-emerald-700 text-xs font-semibold">✓ Page approved</span>
                        ) : (
                          <button
                            disabled={busy}
                            onClick={() => approvePage(b.business_id, true)}
                            className="text-xs font-semibold bg-teal-bright hover:bg-teal text-white rounded-md px-2 py-1 disabled:opacity-50"
                          >
                            Approve page
                          </button>
                        )}
                      </div>
                    ) : (
                      <span className="text-text-muted text-xs">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {b.approval_status === null ? (
                      <div className="flex gap-1.5 justify-end">
                        <button
                          disabled={busy}
                          onClick={() => decide(b.business_id, "rejected")}
                          className="text-xs font-semibold border border-border text-text-secondary hover:border-danger hover:text-danger rounded-md px-2.5 py-1 disabled:opacity-50"
                        >
                          Reject
                        </button>
                        <button
                          disabled={busy}
                          onClick={() => decide(b.business_id, "approved")}
                          className="text-xs font-semibold bg-teal-bright hover:bg-teal text-white rounded-md px-2.5 py-1 disabled:opacity-50"
                        >
                          Approve
                        </button>
                      </div>
                    ) : (
                      <div className="flex flex-col items-end gap-1">
                        <span
                          className={`text-xs font-semibold ${
                            b.approval_status === "approved" ? "text-emerald-700" : "text-danger"
                          }`}
                        >
                          {b.approval_status === "approved" ? "✓ Approved" : "✕ Rejected"}
                        </span>
                        <button
                          disabled={busy}
                          onClick={() => decide(b.business_id, null)}
                          className="text-text-muted text-xs hover:text-text underline"
                        >
                          undo
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
