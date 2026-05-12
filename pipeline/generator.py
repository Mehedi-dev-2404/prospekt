import json
import logging

from anthropic import AsyncAnthropic

from config import settings
from database import supabase
from models.business import Business
from pipeline.template import TEMPLATE

MOCK_MODE = False

ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a copywriter for local business websites. "
    "Return ONLY a valid JSON object — no explanation, no markdown, no code blocks."
)

FIELD_DEFAULTS = {
    "business_name": "Local Business",
    "category": "Business",
    "tagline": "Quality service you can trust.",
    "description": "We are a trusted local business committed to providing excellent service.",
    "primary_color": "#2563EB",
    "google_rating": "5.0",
    "google_review_count": "0",
    "location": "",
    "address": "",
    "phone": "",
    "email": "",
    "service_1": "Consultation",
    "service_2": "Planning",
    "service_3": "Delivery",
    "service_4": "Support",
    "service_5": "Maintenance",
}

PLACEHOLDER_MAP = {
    "{{BUSINESS_NAME}}": "business_name",
    "{{CATEGORY}}": "category",
    "{{TAGLINE}}": "tagline",
    "{{DESCRIPTION}}": "description",
    "{{PRIMARY_COLOR}}": "primary_color",
    "{{GOOGLE_RATING}}": "google_rating",
    "{{GOOGLE_REVIEW_COUNT}}": "google_review_count",
    "{{LOCATION}}": "location",
    "{{ADDRESS}}": "address",
    "{{PHONE}}": "phone",
    "{{EMAIL}}": "email",
    "{{SERVICE_1}}": "service_1",
    "{{SERVICE_2}}": "service_2",
    "{{SERVICE_3}}": "service_3",
    "{{SERVICE_4}}": "service_4",
    "{{SERVICE_5}}": "service_5",
}


def _fill_template(data: dict) -> str:
    html = TEMPLATE
    for placeholder, key in PLACEHOLDER_MAP.items():
        value = str(data.get(key) or FIELD_DEFAULTS.get(key, ""))
        html = html.replace(placeholder, value)
    return html


def _mock_data(business: Business, context: dict) -> dict:
    services = context.get("services") or [business.category]
    if isinstance(services, str):
        services = [services]
    padded = (services + ["Service"] * 5)[:5]
    return {
        "business_name": context.get("business_name") or business.business_name,
        "category": context.get("category") or business.category,
        "tagline": context.get("tagline") or f"Trusted {business.category} services in your area.",
        "description": context.get("description") or f"{business.business_name} provides professional {business.category} services.",
        "primary_color": context.get("primary_color") or "#2563EB",
        "google_rating": str(business.google_rating or "5.0"),
        "google_review_count": str(business.google_review_count or "0"),
        "location": context.get("location") or business.address_full or business.postcode,
        "address": business.address_full or business.postcode,
        "phone": business.phone_primary or "",
        "email": business.email_primary or "",
        "service_1": padded[0],
        "service_2": padded[1],
        "service_3": padded[2],
        "service_4": padded[3],
        "service_5": padded[4],
    }


async def _ask_claude(business: Business, context: dict) -> dict:
    services = context.get("services") or [business.category]
    if isinstance(services, list):
        services_text = ", ".join(str(s) for s in services[:10])
    else:
        services_text = str(services)

    user_prompt = (
        "Generate website content for this local business and return it as a JSON object.\n\n"
        f"Business name: {context.get('business_name') or business.business_name}\n"
        f"Category: {context.get('category') or business.category}\n"
        f"Address: {business.address_full or business.postcode}\n"
        f"Phone: {business.phone_primary or ''}\n"
        f"Email: {business.email_primary or ''}\n"
        f"Google rating: {business.google_rating or ''}\n"
        f"Google review count: {business.google_review_count or ''}\n"
        f"Services: {services_text}\n"
        f"Tagline hint: {context.get('tagline') or ''}\n"
        f"Description hint: {context.get('description') or ''}\n"
        f"Tone: {context.get('tone') or 'professional'}\n"
        f"Primary color: {context.get('primary_color') or '#2563EB'}\n\n"
        "Return a JSON object with exactly these fields:\n"
        "business_name, category, tagline, description, primary_color,\n"
        "google_rating, google_review_count, location, address, phone, email,\n"
        "service_1, service_2, service_3, service_4, service_5\n\n"
        "Rules:\n"
        "- primary_color must be a valid hex color\n"
        "- google_rating and google_review_count must be strings\n"
        "- tagline should be punchy, 1 sentence\n"
        "- description should be 2-3 sentences\n"
        "- service_1 through service_5 are short service names (2-5 words each)\n"
        "- location is the city/area name only (not full address)\n"
    )

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = ""
    for block in response.content:
        if getattr(block, "type", None) == "text":
            raw_text += getattr(block, "text", "")
    raw_text = raw_text.strip()

    # Strip JSON code fences
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()

    parsed, _ = json.JSONDecoder().raw_decode(raw_text)
    if not isinstance(parsed, dict):
        raise ValueError(f"Claude returned non-object JSON: {type(parsed)}")
    return parsed


async def generate_landing_page(business: Business, context: dict) -> str:
    if MOCK_MODE:
        data = _mock_data(business, context)
        return _fill_template(data)

    try:
        logger.info("Requesting JSON content from Claude for '%s'.", business.business_name)
        data = await _ask_claude(business, context)
        logger.info("Claude returned JSON for '%s': %s", business.business_name, list(data.keys()))
    except Exception as exc:
        logger.error(
            "Claude JSON generation failed for '%s', falling back to mock data: %s",
            business.business_name,
            exc,
            exc_info=True,
        )
        data = _mock_data(business, context)

    html = _fill_template(data)

    try:
        supabase.table("businesses").update({"demo_html": html}).eq(
            "business_id", str(business.business_id)
        ).execute()
    except Exception as exc:
        logger.error("Failed to save demo_html to Supabase for '%s': %s", business.business_name, exc)

    return html
