from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse

from database import supabase
from models.job import Job, JobCreate
from pipeline.orchestrator import run_pipeline

router = APIRouter()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/run")
async def start_pipeline(body: JobCreate, background_tasks: BackgroundTasks) -> dict:
    job = Job(
        location=body.location,
        category=body.category,
        status="created",
        started_at=_utc_now(),
    )
    supabase.table("jobs").insert(job.model_dump(mode="json")).execute()
    background_tasks.add_task(run_pipeline, body.location, body.category, job)
    return {"job_id": str(job.job_id), "status": "created", "message": "Pipeline started"}


@router.get("/status/{job_id}")
async def get_job_status(job_id: UUID) -> dict:
    resp = supabase.table("jobs").select("*").eq("job_id", str(job_id)).single().execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return resp.data


@router.get("/jobs")
async def list_jobs(status: Optional[str] = None) -> list:
    query = supabase.table("jobs").select("*").order("created_at", desc=True).limit(50)
    if status:
        query = query.eq("status", status)
    resp = query.execute()
    return resp.data or []


@router.get("/preview/{business_id}", response_class=HTMLResponse)
async def preview_page(business_id: str):
    result = supabase.table("businesses").select("demo_html, business_name").eq("business_id", business_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Business not found")
    demo_html = result.data.get("demo_html")
    if not demo_html:
        return HTMLResponse(content="<h1>No preview available yet</h1>", status_code=200)
    return HTMLResponse(content=demo_html, status_code=200)


@router.post("/cancel/{job_id}")
async def cancel_job(job_id: UUID) -> dict:
    resp = (
        supabase.table("jobs")
        .update({"status": "cancelled", "updated_at": _utc_now().isoformat()})
        .eq("job_id", str(job_id))
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": str(job_id), "status": "cancelled"}
