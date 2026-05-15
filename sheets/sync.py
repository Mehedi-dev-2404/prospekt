import asyncio
import json
import logging

from config import settings
from models.business import Business

MOCK_MODE = False

GOOGLE_SHEETS_ID = settings.GOOGLE_SHEETS_ID

logger = logging.getLogger(__name__)

HEADERS = [
    "business_id",
    "business_name",
    "category",
    "address_full",
    "postcode",
    "website_url",
    "website_score",
    "has_website",
    "email_primary",
    "phone_primary",
    "google_rating",
    "google_review_count",
    "campaign_status",
    "demo_url",
    "approval_status",
    "notes",
]


def _business_to_row(b: Business) -> list[str]:
    return [
        str(b.business_id),
        b.business_name or "",
        b.category or "",
        b.address_full or "",
        b.postcode or "",
        b.website_url or "",
        "" if b.website_score is None else str(b.website_score),
        "TRUE" if b.has_website else "FALSE",
        b.email_primary or "",
        b.phone_primary or "",
        "" if b.google_rating is None else str(b.google_rating),
        "" if b.google_review_count is None else str(b.google_review_count),
        b.campaign_status or "",
        b.demo_url or "",
        "",  # approval_status starts empty for human input
        b.notes or "",
    ]


def _sync_businesses_to_sheets_sync(businesses: list[Business], job_id: str) -> bool:
    logger.info(f"Starting sheets sync for job {job_id}")
    logger.info(f"GOOGLE_CREDENTIALS_JSON is set: {bool(settings.GOOGLE_CREDENTIALS_JSON)}")
    logger.info(f"GOOGLE_SHEETS_ID: {settings.GOOGLE_SHEETS_ID}")

    if settings.GOOGLE_CREDENTIALS_JSON is None:
        logger.error("GOOGLE_CREDENTIALS_JSON not set")
        return False

    try:
        import gspread  # type: ignore

        gc = gspread.service_account_from_dict(json.loads(settings.GOOGLE_CREDENTIALS_JSON))

        logger.info("Attempting to open spreadsheet...")
        sh = gc.open_by_key(GOOGLE_SHEETS_ID)
        logger.info(f"Spreadsheet opened successfully: {sh.title}")

        try:
            ws = sh.worksheet(job_id)
            sh.del_worksheet(ws)
            logger.info(f"Deleted existing worksheet: {job_id}")
        except Exception:
            pass
        ws = sh.add_worksheet(title=job_id, rows=1000, cols=len(HEADERS))
        logger.info(f"Worksheet created: {ws.title}")

        ws.append_row(HEADERS)
        logger.info("Headers written")

        rows = [_business_to_row(b) for b in businesses]
        if rows:
            ws.append_rows(rows)
        logger.info(f"Rows written: {len(businesses)}")

        return True
    except Exception as exc:
        logger.error("Failed to sync businesses to Sheets for job_id=%s: %s", job_id, exc)
        return False


async def sync_businesses_to_sheets(businesses: list[Business], job_id: str) -> bool:
    print(f"SHEETS SYNC CALLED - job_id={job_id}, businesses={len(businesses)}", flush=True)
    if MOCK_MODE:
        rows = [_business_to_row(b) for b in businesses]
        print("=== MOCK SHEETS SYNC ===")
        print(f"Worksheet: {job_id}")
        print("Headers:", HEADERS)
        for r in rows:
            print(r)
        print("========================")
        return True

    return await asyncio.to_thread(_sync_businesses_to_sheets_sync, businesses, job_id)
