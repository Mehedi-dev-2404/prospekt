from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Request
from fastapi.responses import JSONResponse
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


@router.post("/slack")
async def slack_trigger(
    background_tasks: BackgroundTasks,
    text: str = Form(default=""),
    user_name: str = Form(default="unknown"),
):
    if not text.strip():
        return JSONResponse(content={
            "response_type": "ephemeral",
            "text": "Usage: `/prospekt [location] [category]`\nExample: `/prospekt Brixton, London barbershops`",
        })

    parts = text.strip().rsplit(" ", 1)
    if len(parts) == 2 and not parts[1].replace(",", "").strip().isdigit():
        location = parts[0].strip()
        category = parts[1].strip()
    else:
        location = text.strip()
        category = "local businesses"

    import uuid
    from models.job import Job
    from pipeline.orchestrator import run_pipeline

    job_id = str(uuid.uuid4())
    now = _utc_now_iso()

    supabase.table("jobs").insert({
        "job_id": job_id,
        "location": location,
        "category": category,
        "status": "created",
        "created_at": now,
        "started_at": now,
        "updated_at": now,
    }).execute()

    job = Job(job_id=job_id, location=location, category=category)
    background_tasks.add_task(run_pipeline, location, category, job)

    return JSONResponse(content={
        "response_type": "in_channel",
        "text": (
            f"🚀 *Prospekt pipeline started!*\n"
            f"*Location:* {location}\n"
            f"*Category:* {category}\n"
            f"*Job ID:* `{job_id}`\n\n"
            f"Businesses will appear in Google Sheets for approval shortly."
        ),
    })


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
