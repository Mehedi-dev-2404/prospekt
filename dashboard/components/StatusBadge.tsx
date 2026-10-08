const JOB_STATUS_STYLES: Record<string, string> = {
  created: "bg-gray-100 text-gray-600",
  discovering: "bg-blue-50 text-blue-600",
  scoring: "bg-blue-50 text-blue-600",
  awaiting_batch_approval: "bg-amber-50 text-amber-700",
  building: "bg-blue-50 text-blue-600",
  awaiting_page_approval: "bg-amber-50 text-amber-700",
  deploying: "bg-blue-50 text-blue-600",
  outreaching: "bg-blue-50 text-blue-600",
  monitoring: "bg-teal-light text-teal",
  completed: "bg-emerald-50 text-emerald-700",
  failed: "bg-red-50 text-red-600",
};

const CAMPAIGN_STATUS_STYLES: Record<string, string> = {
  pending: "bg-gray-100 text-gray-600",
  approved: "bg-teal-light text-teal",
  rejected: "bg-red-50 text-red-600",
  page_built: "bg-blue-50 text-blue-600",
  page_approved: "bg-blue-50 text-blue-600",
  emailed: "bg-amber-50 text-amber-700",
  replied: "bg-emerald-50 text-emerald-700",
  escalated: "bg-accent/20 text-accent",
  opted_out: "bg-gray-100 text-gray-400",
};

function humanize(value: string): string {
  return value
    .split("_")
    .map((w) => w[0]?.toUpperCase() + w.slice(1))
    .join(" ");
}

export function JobStatusBadge({ status }: { status: string }) {
  const style = JOB_STATUS_STYLES[status] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full ${style}`}>
      {humanize(status)}
    </span>
  );
}

export function CampaignStatusBadge({ status }: { status: string }) {
  const style = CAMPAIGN_STATUS_STYLES[status] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full ${style}`}>
      {humanize(status)}
    </span>
  );
}
