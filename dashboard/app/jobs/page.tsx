import Link from "next/link";
import { getJobs } from "@/lib/data";
import { JobStatusBadge } from "@/components/StatusBadge";


function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function JobsPage() {
  const jobs = await getJobs();

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-navy tracking-tight">Pipeline Runs</h1>
          <p className="text-text-secondary text-sm mt-1">
            {jobs.length} run{jobs.length === 1 ? "" : "s"} total
          </p>
        </div>
        <Link
          href="/run"
          className="bg-teal-bright hover:bg-teal text-white font-semibold text-sm rounded-lg px-4 py-2.5 transition-colors"
        >
          + New Run
        </Link>
      </div>

      {jobs.length === 0 ? (
        <div className="bg-surface border border-border rounded-xl p-12 text-center text-text-muted">
          No pipeline runs yet. Start one from the <Link href="/run" className="text-teal font-medium">New Run</Link> page.
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-bg border-b border-border text-left text-text-muted text-xs uppercase tracking-wide">
                  <th className="px-4 py-3 font-semibold">Location / Category</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold text-right">Found</th>
                  <th className="px-4 py-3 font-semibold text-right">Approved</th>
                  <th className="px-4 py-3 font-semibold text-right">Pages</th>
                  <th className="px-4 py-3 font-semibold text-right">Emailed</th>
                  <th className="px-4 py-3 font-semibold text-right">Replied</th>
                  <th className="px-4 py-3 font-semibold text-right">Escalated</th>
                  <th className="px-4 py-3 font-semibold">Started</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr
                    key={job.job_id}
                    className="border-b border-border last:border-0 hover:bg-bg transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/jobs/${job.job_id}`}
                        className="font-semibold text-navy hover:text-teal"
                      >
                        {job.location}
                      </Link>
                      <div className="text-text-muted text-xs">{job.category ?? "—"}</div>
                    </td>
                    <td className="px-4 py-3">
                      <JobStatusBadge status={job.status} />
                      {job.error_message && (
                        <div className="text-danger text-xs mt-1 max-w-[220px] truncate" title={job.error_message}>
                          {job.error_message}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-text">{job.businesses_found}</td>
                    <td className="px-4 py-3 text-right text-text">
                      {job.businesses_approved}
                      <span className="text-text-muted"> / {job.businesses_rejected}</span>
                    </td>
                    <td className="px-4 py-3 text-right text-text">
                      {job.pages_approved}
                      <span className="text-text-muted"> / {job.pages_built}</span>
                    </td>
                    <td className="px-4 py-3 text-right text-text">{job.emails_sent}</td>
                    <td className="px-4 py-3 text-right text-text">{job.replies_received}</td>
                    <td className="px-4 py-3 text-right font-semibold text-accent">
                      {job.leads_escalated}
                    </td>
                    <td className="px-4 py-3 text-text-muted text-xs whitespace-nowrap">
                      {formatDate(job.started_at ?? job.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
