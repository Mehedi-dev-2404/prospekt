import asyncio
import json
import logging

from config import settings

GOOGLE_SHEETS_ID = settings.GOOGLE_SHEETS_ID

logger = logging.getLogger(__name__)

APPROVAL_COL = "approval_status"
BUSINESS_ID_COL = "business_id"


def _poll_approval_status_sync(job_id: str) -> dict:
    try:
        import gspread  # type: ignore

        gc = gspread.service_account_from_dict(json.loads(settings.GOOGLE_CREDENTIALS_JSON))
        sh = gc.open_by_key(GOOGLE_SHEETS_ID)
        print(f"Poller looking for job_id worksheet: {job_id}", flush=True)
        ws = sh.worksheet(job_id)

        values = ws.get_all_values()
        if not values or len(values) < 2:
            return {"approved": [], "rejected": []}

        header = values[0]
        print(f"Worksheet headers: {header}", flush=True)
        print(f"Total rows found: {len(values[1:])}", flush=True)
        try:
            id_idx = header.index(BUSINESS_ID_COL)
            approval_idx = header.index(APPROVAL_COL)
        except ValueError:
            logger.error("Sheet missing required columns in worksheet %s: %s", job_id, header)
            return {"approved": [], "rejected": []}

        print(f"Approval column index: {approval_idx}", flush=True)
        approved: list[str] = []
        rejected: list[str] = []

        for row in values[1:]:
            if len(row) <= max(id_idx, approval_idx):
                continue
            print(f"Row approval value: '{row[approval_idx]}'", flush=True)
            business_id = row[id_idx].strip()
            approval = row[approval_idx].strip()
            if approval == "Approve":
                approved.append(business_id)
            elif approval == "Reject":
                rejected.append(business_id)

        return {"approved": approved, "rejected": rejected}
    except Exception as exc:
        logger.error("Failed to poll approval status for job_id=%s: %s", job_id, exc)
        return {"approved": [], "rejected": []}


async def poll_approval_status(job_id: str) -> dict:
    if False:
        # Hardcoded IDs for mock behavior (approve first 3, reject the rest).
        ids = [
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
            "33333333-3333-3333-3333-333333333333",
            "44444444-4444-4444-4444-444444444444",
            "55555555-5555-5555-5555-555555555555",
        ]
        return {"approved": ids[:3], "rejected": ids[3:]}

    print("Poller taking real path", flush=True)
    return await asyncio.to_thread(_poll_approval_status_sync, job_id)
