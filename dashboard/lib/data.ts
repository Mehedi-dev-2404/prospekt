import "server-only";
import { supabase } from "./supabase";

export type Job = {
  job_id: string;
  location: string;
  category: string | null;
  status: string;
  error_message: string | null;
  businesses_found: number;
  businesses_approved: number;
  businesses_rejected: number;
  pages_built: number;
  pages_approved: number;
  emails_sent: number;
  replies_received: number;
  leads_escalated: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string;
};

export type Business = {
  business_id: string;
  job_id: string | null;
  business_name: string;
  category: string;
  address_full: string;
  postcode: string;
  phone_primary: string | null;
  email_primary: string | null;
  website_url: string | null;
  website_score: number | null;
  has_website: boolean;
  google_maps_url: string | null;
  google_rating: number | null;
  google_review_count: number | null;
  demo_url: string | null;
  demo_approved: boolean;
  campaign_status: string;
  approval_status: "approved" | "rejected" | null;
  email_1_sent_at: string | null;
  replied_at: string | null;
  reply_content: string | null;
  opted_out: boolean;
  notes: string | null;
  created_at: string;
};

export async function getJobs(): Promise<Job[]> {
  const { data, error } = await supabase
    .from("jobs")
    .select("*")
    .order("created_at", { ascending: false });
  if (error) throw error;
  return data ?? [];
}

export async function getJob(jobId: string): Promise<Job | null> {
  const { data, error } = await supabase
    .from("jobs")
    .select("*")
    .eq("job_id", jobId)
    .maybeSingle();
  if (error) throw error;
  return data;
}

export async function getBusinessesForJob(jobId: string): Promise<Business[]> {
  const { data, error } = await supabase
    .from("businesses")
    .select("*")
    .eq("job_id", jobId)
    .order("website_score", { ascending: true, nullsFirst: true });
  if (error) throw error;
  return data ?? [];
}

export async function getAllBusinesses(): Promise<(Business & { job_location: string | null })[]> {
  const { data, error } = await supabase
    .from("businesses")
    .select("*, jobs(location)")
    .order("created_at", { ascending: false });
  if (error) throw error;
  return (data ?? []).map((row: any) => ({
    ...row,
    job_location: row.jobs?.location ?? null,
  }));
}

export async function setApprovalStatus(
  businessId: string,
  status: "approved" | "rejected" | null
): Promise<void> {
  const { error } = await supabase
    .from("businesses")
    .update({ approval_status: status })
    .eq("business_id", businessId);
  if (error) throw error;
}

export async function setPageApproval(businessId: string, approved: boolean): Promise<void> {
  const { error } = await supabase
    .from("businesses")
    .update({ demo_approved: approved })
    .eq("business_id", businessId);
  if (error) throw error;
}
