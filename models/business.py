from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


CampaignStatus = Literal[
    "pending",
    "approved",
    "rejected",
    "page_built",
    "page_approved",
    "emailed",
    "replied",
    "escalated",
    "opted_out",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Business(BaseModel):
    # Core identity
    business_id: UUID = Field(default_factory=uuid4)
    business_name: str
    category: str
    address_full: str
    postcode: str

    # Contact info
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email_primary: Optional[str] = None
    email_secondary: Optional[str] = None
    website_url: Optional[str] = None

    # Web presence scoring
    website_score: Optional[int] = Field(default=None, ge=0, le=100)
    has_website: bool = False

    # Social media
    google_maps_url: Optional[str] = None
    google_rating: Optional[float] = None
    google_review_count: Optional[int] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    tiktok_url: Optional[str] = None

    # Key contacts
    owner_name: Optional[str] = None
    owner_linkedin: Optional[str] = None
    key_contact_email: Optional[str] = None
    key_contact_phone: Optional[str] = None

    # Demo and campaign
    demo_url: Optional[str] = None
    demo_approved: bool = False
    campaign_status: CampaignStatus = "pending"
    assigned_rep: Optional[str] = None

    # Email tracking
    email_1_sent_at: Optional[datetime] = None
    email_2_sent_at: Optional[datetime] = None
    email_3_sent_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    reply_content: Optional[str] = None

    # Compliance
    opted_out: bool = False
    notes: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class BusinessCreate(BaseModel):
    business_name: str
    category: str
    address_full: str
    postcode: str
    phone_primary: Optional[str] = None
    website_url: Optional[str] = None
    has_website: bool = False
    google_maps_url: Optional[str] = None
    google_rating: Optional[float] = None
    google_review_count: Optional[int] = None


class BusinessUpdate(BaseModel):
    # Core identity
    business_id: Optional[UUID] = None
    business_name: Optional[str] = None
    category: Optional[str] = None
    address_full: Optional[str] = None
    postcode: Optional[str] = None

    # Contact info
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email_primary: Optional[str] = None
    email_secondary: Optional[str] = None
    website_url: Optional[str] = None

    # Web presence scoring
    website_score: Optional[int] = Field(default=None, ge=0, le=100)
    has_website: Optional[bool] = None

    # Social media
    google_maps_url: Optional[str] = None
    google_rating: Optional[float] = None
    google_review_count: Optional[int] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    tiktok_url: Optional[str] = None

    # Key contacts
    owner_name: Optional[str] = None
    owner_linkedin: Optional[str] = None
    key_contact_email: Optional[str] = None
    key_contact_phone: Optional[str] = None

    # Demo and campaign
    demo_url: Optional[str] = None
    demo_approved: Optional[bool] = None
    campaign_status: Optional[CampaignStatus] = None
    assigned_rep: Optional[str] = None

    # Email tracking
    email_1_sent_at: Optional[datetime] = None
    email_2_sent_at: Optional[datetime] = None
    email_3_sent_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    reply_content: Optional[str] = None

    # Compliance
    opted_out: Optional[bool] = None
    notes: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
