from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from database import supabase
from pipeline.monitor import monitor_replies
from models.business import Business

router = APIRouter()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class UnsubscribeRequest(BaseModel):
    email: str


@router.post("/reply")
async def handle_reply(request: Request) -> dict:
    form = await request.form()

    sender_email: str = form.get("from", "") or form.get("sender", "")
    subject: str = form.get("subject", "")
    body_text: str = form.get("text", "") or form.get("body", "")

    if not sender_email:
        raise HTTPException(status_code=400, detail="Missing sender email")

    # Strip angle brackets if present: "Name <email@example.com>"
    if "<" in sender_email and ">" in sender_email:
        sender_email = sender_email.split("<")[-1].rstrip(">").strip()

    resp = (
        supabase.table("businesses")
        .select("*")
        .eq("email_primary", sender_email)
        .limit(1)
        .execute()
    )
    if not resp.data:
        # Unknown sender — acknowledge without error
        return {"status": "ok"}

    business_data = resp.data[0]
    supabase.table("businesses").update(
        {
            "reply_content": body_text,
            "replied_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
        }
    ).eq("email_primary", sender_email).execute()

    business = Business(**business_data)
    business.reply_content = body_text
    await monitor_replies(business)

    return {"status": "ok"}


@router.post("/unsubscribe")
async def handle_unsubscribe(body: UnsubscribeRequest) -> dict:
    resp = (
        supabase.table("businesses")
        .select("business_id")
        .eq("email_primary", body.email)
        .limit(1)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Email not found")

    supabase.table("businesses").update(
        {
            "opted_out": True,
            "updated_at": _utc_now_iso(),
        }
    ).eq("email_primary", body.email).execute()

    return {"status": "ok", "message": "Unsubscribed"}
