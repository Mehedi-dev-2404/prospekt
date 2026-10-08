"use client";

import { useMemo, useState } from "react";
import type { Business } from "@/lib/data";
import { CampaignStatusBadge } from "./StatusBadge";

type Row = Business & { job_location: string | null };

const STATUS_OPTIONS = [
  "all",
  "pending",
  "approved",
  "rejected",
  "page_built",
  "page_approved",
  "emailed",
  "replied",
  "escalated",
  "opted_out",
];

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function CampaignTracker({ businesses }: { businesses: Row[] }) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");

  const filtered = useMemo(() => {
    return businesses.filter((b) => {
      if (status !== "all" && b.campaign_status !== status) return false;
      if (!search) return true;
      const q = search.toLowerCase();
      return (
        b.business_name.toLowerCase().includes(q) ||
        (b.email_primary ?? "").toLowerCase().includes(q) ||
        (b.job_location ?? "").toLowerCase().includes(q) ||
        b.category.toLowerCase().includes(q)
      );
    });
  }, [businesses, search, status]);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <input
          type="text"
          placeholder="Search business, email, location…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-[220px] rounded-lg border border-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-bright"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-lg border border-border px-3 py-2 text-sm bg-surface focus:outline-none focus:ring-2 focus:ring-teal-bright"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s === "all" ? "All statuses" : s.replace("_", " ")}
            </option>
          ))}
        </select>
        <span className="text-text-muted text-sm">{filtered.length} of {businesses.length}</span>
      </div>

      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-bg border-b border-border text-left text-text-muted text-xs uppercase tracking-wide">
                <th className="px-4 py-3 font-semibold">Business</th>
                <th className="px-4 py-3 font-semibold">Location</th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="px-4 py-3 font-semibold">Demo</th>
                <th className="px-4 py-3 font-semibold">Emailed</th>
                <th className="px-4 py-3 font-semibold">Replied</th>
                <th className="px-4 py-3 font-semibold">Reply</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((b) => (
                <tr key={b.business_id} className="border-b border-border last:border-0 hover:bg-bg transition-colors align-top">
                  <td className="px-4 py-3">
                    <div className="font-semibold text-navy">{b.business_name}</div>
                    <div className="text-text-muted text-xs">{b.email_primary ?? "no email"}</div>
                    {b.opted_out && (
                      <span className="text-danger text-xs font-semibold">opted out</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-text-secondary text-xs">{b.job_location ?? "—"}</td>
                  <td className="px-4 py-3">
                    <CampaignStatusBadge status={b.campaign_status} />
                  </td>
                  <td className="px-4 py-3">
                    {b.demo_url ? (
                      <a href={b.demo_url} target="_blank" rel="noopener noreferrer" className="text-teal text-xs hover:underline">
                        View →
                      </a>
                    ) : (
                      <span className="text-text-muted text-xs">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-text-secondary text-xs whitespace-nowrap">
                    {formatDate(b.email_1_sent_at)}
                  </td>
                  <td className="px-4 py-3 text-text-secondary text-xs whitespace-nowrap">
                    {formatDate(b.replied_at)}
                  </td>
                  <td className="px-4 py-3 text-text-secondary text-xs max-w-[240px] truncate" title={b.reply_content ?? ""}>
                    {b.reply_content ?? "—"}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-text-muted">
                    No businesses match this filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
