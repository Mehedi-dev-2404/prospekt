import Link from "next/link";
import { notFound } from "next/navigation";
import { getJob, getBusinessesForJob } from "@/lib/data";
import { JobStatusBadge } from "@/components/StatusBadge";
import BusinessTable from "@/components/BusinessTable";


export default async function JobDetailPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  const job = await getJob(jobId);
  if (!job) notFound();

  const businesses = await getBusinessesForJob(jobId);
  const awaitingBatch = businesses.filter((b) => b.approval_status === null);
  const decided = businesses.filter((b) => b.approval_status !== null);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      <Link href="/jobs" className="text-teal text-sm font-medium hover:underline">
        ← All runs
      </Link>

      <div className="flex items-center justify-between mt-3 mb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-navy tracking-tight">{job.location}</h1>
          <p className="text-text-secondary text-sm mt-1">{job.category ?? "All categories"}</p>
        </div>
        <JobStatusBadge status={job.status} />
      </div>

      {job.error_message && (
        <div className="bg-red-50 border border-red-200 text-danger text-sm rounded-lg px-4 py-3 mb-6">
          {job.error_message}
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 mb-8">
        {[
          ["Found", job.businesses_found],
          ["Approved", job.businesses_approved],
          ["Rejected", job.businesses_rejected],
          ["Pages built", job.pages_built],
          ["Pages approved", job.pages_approved],
          ["Emailed", job.emails_sent],
          ["Replied", job.replies_received],
          ["Escalated", job.leads_escalated],
        ].map(([label, value]) => (
          <div key={label as string} className="bg-surface border border-border rounded-lg px-3 py-3 text-center">
            <div className="text-xl font-extrabold text-navy">{value}</div>
            <div className="text-text-muted text-xs mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {awaitingBatch.length > 0 && (
        <div className="mb-8">
          <h2 className="text-sm font-bold text-navy uppercase tracking-wide mb-3">
            Awaiting Approval ({awaitingBatch.length})
          </h2>
          <BusinessTable businesses={awaitingBatch} />
        </div>
      )}

      {decided.length > 0 && (
        <div>
          <h2 className="text-sm font-bold text-navy uppercase tracking-wide mb-3">
            Decided ({decided.length})
          </h2>
          <BusinessTable businesses={decided} />
        </div>
      )}

      {businesses.length === 0 && (
        <div className="bg-surface border border-border rounded-xl p-12 text-center text-text-muted">
          No businesses discovered yet for this run.
        </div>
      )}
    </div>
  );
}
