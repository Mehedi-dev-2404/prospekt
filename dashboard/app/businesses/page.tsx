import { getAllBusinesses } from "@/lib/data";
import CampaignTracker from "@/components/CampaignTracker";


export default async function BusinessesPage() {
  const businesses = await getAllBusinesses();

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      <h1 className="text-2xl font-extrabold text-navy tracking-tight mb-1">Campaign Tracker</h1>
      <p className="text-text-secondary text-sm mb-6">
        Every business discovered across all pipeline runs.
      </p>
      <CampaignTracker businesses={businesses} />
    </div>
  );
}
