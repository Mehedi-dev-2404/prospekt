import asyncio
import logging

from database import supabase

logger = logging.getLogger(__name__)


def _poll_batch_approval_sync(job_id: str) -> dict:
    try:
        resp = (
            supabase.table("businesses")
            .select("business_id, approval_status")
            .eq("job_id", job_id)
            .execute()
        )
        approved = [r["business_id"] for r in resp.data if r.get("approval_status") == "approved"]
        rejected = [r["business_id"] for r in resp.data if r.get("approval_status") == "rejected"]
        return {"approved": approved, "rejected": rejected}
    except Exception as exc:
        logger.error("Failed to poll batch approval status for job_id=%s: %s", job_id, exc)
        return {"approved": [], "rejected": []}


async def poll_batch_approval_status(job_id: str) -> dict:
    return await asyncio.to_thread(_poll_batch_approval_sync, job_id)


def _poll_page_approval_sync(business_ids: list[str]) -> list[str]:
    try:
        resp = (
            supabase.table("businesses")
            .select("business_id, demo_approved")
            .in_("business_id", business_ids)
            .execute()
        )
        return [r["business_id"] for r in resp.data if r.get("demo_approved")]
    except Exception as exc:
        logger.error("Failed to poll page approval status: %s", exc)
        return []


async def poll_page_approval_status(business_ids: list[str]) -> list[str]:
    if not business_ids:
        return []
    return await asyncio.to_thread(_poll_page_approval_sync, business_ids)
