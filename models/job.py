from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


JobStatus = Literal[
    "created",
    "discovering",
    "scoring",
    "awaiting_batch_approval",
    "building",
    "awaiting_page_approval",
    "deploying",
    "outreaching",
    "monitoring",
    "completed",
    "failed",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Job(BaseModel):
    # Core
    job_id: UUID = Field(default_factory=uuid4)
    location: str
    category: Optional[str] = None

    # Status
    status: JobStatus = "created"
    error_message: Optional[str] = None

    # Progress tracking
    businesses_found: int = 0
    businesses_approved: int = 0
    businesses_rejected: int = 0
    pages_built: int = 0
    pages_approved: int = 0
    emails_sent: int = 0
    replies_received: int = 0
    leads_escalated: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=utc_now)


class JobCreate(BaseModel):
    location: str
    category: Optional[str] = None


class JobUpdate(BaseModel):
    # Core
    job_id: Optional[UUID] = None
    location: Optional[str] = None
    category: Optional[str] = None

    # Status
    status: Optional[JobStatus] = None
    error_message: Optional[str] = None

    # Progress tracking
    businesses_found: Optional[int] = None
    businesses_approved: Optional[int] = None
    businesses_rejected: Optional[int] = None
    pages_built: Optional[int] = None
    pages_approved: Optional[int] = None
    emails_sent: Optional[int] = None
    replies_received: Optional[int] = None
    leads_escalated: Optional[int] = None

    # Timestamps
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
