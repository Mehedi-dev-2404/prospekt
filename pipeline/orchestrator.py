import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from config import settings
from database import supabase
from models.business import Business, BusinessCreate
from models.job import Job
from pipeline.deployer import deploy_landing_page
from pipeline.discovery import discover_businesses
from pipeline.generator import generate_landing_page
from pipeline.monitor import monitor_replies
from pipeline.outreach import send_outreach_email
from pipeline.scorer import score_business
from pipeline.scraper import scrape_business_context
from pipeline.approval import poll_batch_approval_status, poll_page_approval_status

POLL_INTERVAL_SECONDS = 120   # poll every 2 minutes
MAX_POLL_ATTEMPTS = 288       # 288 x 5 minutes = 24 hours

logger = logging.getLogger(__name__)


async def _slack_notify(message: str) -> None:
    if not settings.SLACK_WEBHOOK_URL or settings.SLACK_WEBHOOK_URL == "placeholder":
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                settings.SLACK_WEBHOOK_URL,
                json={"text": message},
                timeout=5,
            )
    except Exception as e:
        logger.warning(f"Slack notification failed: {e}")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_result(job: Job, error: str | None = None) -> dict:
    return {
        "job_id": str(job.job_id),
        "status": job.status,
        "businesses_found": job.businesses_found,
        "businesses_approved": job.businesses_approved,
        "emails_sent": job.emails_sent,
        "leads_escalated": job.leads_escalated,
        "error": error,
    }


def _insert_job_sync(job: Job) -> bool:
    payload = job.model_dump(mode="json")
    resp = supabase.table("jobs").insert(payload).execute()
    return bool(resp)


def _update_job_sync(job_id: str, updates: dict[str, Any]) -> bool:
    payload = {**updates, "updated_at": _utc_now_iso()}
    resp = supabase.table("jobs").update(payload).eq("job_id", job_id).execute()
    return bool(resp)


def _insert_businesses_sync(businesses: list[Business]) -> bool:
    rows = [b.model_dump(mode="json") for b in businesses]
    resp = supabase.table("businesses").insert(rows).execute()
    return bool(resp)


def _update_business_sync(business_id: str, updates: dict[str, Any]) -> bool:
    resp = supabase.table("businesses").update(updates).eq("business_id", business_id).execute()
    return bool(resp)


async def _set_job_status(job: Job, status: str, **extra: Any) -> None:
    job.status = status  # type: ignore[assignment]
    for key, value in extra.items():
        setattr(job, key, value)
    await asyncio.to_thread(
        _update_job_sync,
        str(job.job_id),
        {"status": status, **extra},
    )


async def _mark_failed(job: Job, error_message: str) -> dict:
    logger.error("Pipeline failed for job %s: %s", job.job_id, error_message)
    job.status = "failed"
    job.error_message = error_message
    await asyncio.to_thread(
        _update_job_sync,
        str(job.job_id),
        {"status": "failed", "error_message": error_message},
    )
    return _job_result(job, error_message)


async def _poll_page_approvals(approved_businesses: list[Business]) -> list[Business]:
    if not approved_businesses:
        return []

    business_ids = [str(b.business_id) for b in approved_businesses]
    for attempt in range(MAX_POLL_ATTEMPTS):
        approved_ids = set(await poll_page_approval_status(business_ids))
        if approved_ids:
            return [b for b in approved_businesses if str(b.business_id) in approved_ids]
        if attempt < MAX_POLL_ATTEMPTS - 1:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    return []


async def _find_email(business: Business) -> str | None:
    from urllib.parse import urlparse

    print(f"_find_email called for {business.business_name}, website: {business.website_url}, HUNTER_KEY set: {bool(settings.HUNTER_API_KEY)}", flush=True)

    # Try Hunter.io first
    if settings.HUNTER_API_KEY and business.website_url:
        try:
            domain = urlparse(business.website_url).netloc.replace("www.", "")
            if domain:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://api.hunter.io/v2/domain-search",
                        params={"domain": domain, "api_key": settings.HUNTER_API_KEY, "limit": 1},
                        timeout=10,
                    )
                    data = resp.json()
                    print(f"Hunter.io response for {domain}: {data}", flush=True)
                    emails = data.get("data", {}).get("emails", [])
                    if emails:
                        email = emails[0].get("value")
                        if email:
                            logger.info("Hunter.io found email for %s: %s", business.business_name, email)
                            return email
        except Exception as e:
            logger.warning("Hunter.io failed for %s: %s", business.business_name, e)

    # Fallback to info@domain
    if business.website_url:
        try:
            domain = urlparse(business.website_url).netloc.replace("www.", "")
            if domain:
                return f"info@{domain}"
        except Exception:
            pass

    return None


async def run_pipeline(location: str, category: str = None, job: Job = None) -> dict:
    if job is None:
        job = Job(location=location, category=category, status="created", started_at=datetime.now(timezone.utc))
        try:
            await asyncio.to_thread(_insert_job_sync, job)
        except Exception as exc:
            logger.error("Failed to create initial job row: %s", exc)
            job.status = "failed"
            job.error_message = "Failed to create job"
            return _job_result(job, job.error_message)

    # Stage: Discovery
    try:
        await _set_job_status(job, "discovering")
        discovered = await discover_businesses(location, category)
        businesses: list[Business] = [Business(**b.model_dump(), job_id=job.job_id) for b in discovered]
        job.businesses_found = len(businesses)
        await _set_job_status(job, "discovering", businesses_found=job.businesses_found)
    except Exception as exc:
        return await _mark_failed(job, f"Discovery failed: {exc}")

    # Stage: Scoring
    try:
        await _set_job_status(job, "scoring")
        for b in businesses:
            if b.has_website and b.website_url:
                score, _reason = await score_business(b)
                b.website_score = score
                b.has_website = bool(b.website_url)
    except Exception as exc:
        return await _mark_failed(job, f"Scoring failed: {exc}")

    # Stage: Scraping
    contexts: dict[str, dict] = {}
    try:
        for b in businesses:
            context = await scrape_business_context(b)
            contexts[str(b.business_id)] = context
    except Exception as exc:
        return await _mark_failed(job, f"Scraping failed: {exc}")

    # Stage: Save to Supabase
    try:
        await asyncio.to_thread(_insert_businesses_sync, businesses)
    except Exception as exc:
        return await _mark_failed(job, f"Saving businesses failed: {exc}")

    # Stage: Awaiting batch approval (reviewed in the Prospekt dashboard)
    try:
        await _set_job_status(job, "awaiting_batch_approval")
        dashboard_link = f"{settings.DASHBOARD_URL}/jobs/{job.job_id}" if settings.DASHBOARD_URL else f"job {job.job_id}"
        await _slack_notify(
            f"🔍 *Prospekt — Batch Ready for Approval*\n\n"
            f"Job ID: {job.job_id}\n"
            f"Location: {location} | Category: {category}\n"
            f"Businesses found: {job.businesses_found}\n\n"
            f"👉 Review and approve/reject businesses in the dashboard: {dashboard_link}"
        )
    except Exception as exc:
        return await _mark_failed(job, f"Awaiting batch approval setup failed: {exc}")

    # Stage: Poll batch approvals
    approved_businesses: list[Business] = []
    rejected_businesses: list[Business] = []
    try:
        polled = {"approved": [], "rejected": []}
        for attempt in range(MAX_POLL_ATTEMPTS):
            polled = await poll_batch_approval_status(str(job.job_id))
            approved_ids = set(polled.get("approved", []))
            rejected_ids = set(polled.get("rejected", []))
            if approved_ids or rejected_ids:
                break
            if attempt < MAX_POLL_ATTEMPTS - 1:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)

        id_to_business = {str(b.business_id): b for b in businesses}
        approved_businesses = [id_to_business[i] for i in polled.get("approved", []) if i in id_to_business]
        rejected_businesses = [id_to_business[i] for i in polled.get("rejected", []) if i in id_to_business]

        job.businesses_approved = len(approved_businesses)
        job.businesses_rejected = len(rejected_businesses)
        await _set_job_status(
            job,
            "awaiting_batch_approval",
            businesses_approved=job.businesses_approved,
            businesses_rejected=job.businesses_rejected,
        )
    except Exception as exc:
        return await _mark_failed(job, f"Approval polling failed: {exc}")

    # Stage: Find emails for approved businesses (Hunter.io with info@ fallback)
    print(f"Finding emails for {len(approved_businesses)} approved businesses", flush=True)
    print(f"approved_businesses type: {type(approved_businesses)}, count: {len(approved_businesses)}", flush=True)
    for b in approved_businesses:
        print(f"  - {b.business_name}, email: {b.email_primary}, type: {type(b)}", flush=True)
    for business in approved_businesses:
        email = await _find_email(business)
        if email:
            business.email_primary = email
            supabase.table("businesses").update({"email_primary": email}).eq("business_id", str(business.business_id)).execute()

    # Stage: Generate pages
    generated_pages: dict[str, str] = {}
    try:
        await _set_job_status(job, "building")
        for b in approved_businesses:
            html = await generate_landing_page(b, contexts.get(str(b.business_id), {}))
            generated_pages[str(b.business_id)] = html
        job.pages_built = len(generated_pages)
        await _set_job_status(job, "building", pages_built=job.pages_built)
    except Exception as exc:
        return await _mark_failed(job, f"Page generation failed: {exc}")

    # Stage: Awaiting page approval
    try:
        await _set_job_status(job, "awaiting_page_approval")
    except Exception as exc:
        return await _mark_failed(job, f"Page review setup failed: {exc}")

    # Stage: Poll page approvals
    page_approved_businesses: list[Business] = []
    try:
        page_approved_businesses = await _poll_page_approvals(approved_businesses)
        job.pages_approved = len(page_approved_businesses)
        await _set_job_status(job, "awaiting_page_approval", pages_approved=job.pages_approved)
    except Exception as exc:
        return await _mark_failed(job, f"Page approval polling failed: {exc}")

    # Stage: Deploy
    deployed_businesses: list[Business] = []
    try:
        await _set_job_status(job, "deploying")
        for b in page_approved_businesses:
            html = generated_pages.get(str(b.business_id), "")
            deployed_url = await deploy_landing_page(b.business_name, html)
            if deployed_url:
                b.demo_url = deployed_url
                deployed_businesses.append(b)
                await asyncio.to_thread(
                    _update_business_sync,
                    str(b.business_id),
                    {"demo_url": deployed_url},
                )
    except Exception as exc:
        return await _mark_failed(job, f"Deployment failed: {exc}")

    # Stage: Outreach
    emailed_businesses: list[Business] = []
    try:
        await _set_job_status(job, "outreaching")
        emails_sent = 0
        for b in deployed_businesses:
            ok = await send_outreach_email(
                b,
                contexts.get(str(b.business_id), {}),
                b.demo_url or "",
            )
            if ok:
                emails_sent += 1
                emailed_businesses.append(b)
                await asyncio.to_thread(
                    _update_business_sync,
                    str(b.business_id),
                    {"campaign_status": "emailed"},
                )
        job.emails_sent = emails_sent
        await _set_job_status(job, "outreaching", emails_sent=job.emails_sent)
        dashboard_link = f"{settings.DASHBOARD_URL}/jobs/{job.job_id}" if settings.DASHBOARD_URL else f"job {job.job_id}"
        await _slack_notify(
            f"✅ *Prospekt — Outreach Complete*\n\n"
            f"Job ID: {job.job_id}\n"
            f"Location: {location} | Category: {category}\n"
            f"Businesses approved: {job.businesses_approved}\n"
            f"Pages deployed: {job.pages_built}\n"
            f"Emails sent: {job.emails_sent}\n\n"
            f"View details in the dashboard: {dashboard_link}"
        )
    except Exception as exc:
        return await _mark_failed(job, f"Outreach failed: {exc}")

    # Stage: Monitor
    try:
        await _set_job_status(job, "monitoring")
        replies_received = 0
        leads_escalated = 0
        for b in emailed_businesses:
            result = await monitor_replies(b)
            if result.get("replied"):
                replies_received += 1
                if result.get("classification") == "interested":
                    leads_escalated += 1
        job.replies_received = replies_received
        job.leads_escalated = leads_escalated
        await _set_job_status(
            job,
            "monitoring",
            replies_received=job.replies_received,
            leads_escalated=job.leads_escalated,
        )
    except Exception as exc:
        return await _mark_failed(job, f"Monitoring failed: {exc}")

    # Stage: Complete
    try:
        job.completed_at = datetime.now(timezone.utc)
        await _set_job_status(job, "completed", completed_at=job.completed_at.isoformat())
        return _job_result(job, None)
    except Exception as exc:
        return await _mark_failed(job, f"Completion failed: {exc}")
