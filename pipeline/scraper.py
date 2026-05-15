import asyncio
import json
import logging
import socket
from typing import Any, Optional

from anthropic import AsyncAnthropic

from config import settings
from models.business import Business

ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
SYSTEM_PROMPT = (
    "You are a business analyst. Extract structured information from website content."
)

logger = logging.getLogger(__name__)


def _minimal_context(business: Business) -> dict:
    return {
        "business_name": business.business_name,
        "tagline": f"{business.category.title()} business in {business.postcode or 'the local area'}",
        "description": (
            f"{business.business_name} operates in the {business.category} space. "
            f"Limited website data is available, so this profile is based on core business details."
        ),
        "tone": "professional",
        "primary_color": "#2563EB",
        "logo_url": None,
        "services": [business.category],
        "location": business.address_full or business.postcode or "Unknown",
    }



def _extract_text_from_response(response: object) -> str:
    content = getattr(response, "content", [])
    text_parts: list[str] = []

    for block in content:
        if getattr(block, "type", None) == "text":
            text_parts.append(getattr(block, "text", ""))

    return "\n".join(part for part in text_parts if part).strip()


def _normalize_context(data: dict[str, Any], business: Business) -> dict:
    minimal = _minimal_context(business)
    merged = {**minimal, **data}

    services = merged.get("services")
    if not isinstance(services, list):
        merged["services"] = minimal["services"]
    else:
        merged["services"] = [str(item) for item in services[:5] if str(item).strip()]
        if not merged["services"]:
            merged["services"] = minimal["services"]

    for key in ("business_name", "tagline", "description", "tone", "primary_color", "location"):
        value = merged.get(key)
        if value is None or not str(value).strip():
            merged[key] = minimal[key]
        else:
            merged[key] = str(value).strip()

    logo_url = merged.get("logo_url")
    merged["logo_url"] = str(logo_url).strip() if logo_url else None

    return merged


async def _infer_with_claude(business: Business) -> dict:
    try:
        client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

        rating_info = (
            f"Google rating: {business.google_rating} ({business.google_review_count} reviews)"
            if business.google_rating
            else "Google rating: not available"
        )
        user_prompt = (
            "Infer structured business context from the following details.\n"
            "Return ONLY a JSON object with exactly these keys:\n"
            "business_name, tagline, description, tone, primary_color, logo_url, services, location.\n\n"
            f"Business name: {business.business_name}\n"
            f"Category: {business.category}\n"
            f"Address: {business.address_full}\n"
            f"Postcode: {business.postcode}\n"
            f"{rating_info}"
        )

        last_exc: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                response = await client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=500,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )

                raw_text = _extract_text_from_response(response)
                if not raw_text:
                    raise ValueError("Empty response from Claude")
                if raw_text.startswith("```"):
                    lines = raw_text.split("\n")
                    raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
                parsed, _ = json.JSONDecoder().raw_decode(raw_text)
                if not isinstance(parsed, dict):
                    raise ValueError("Claude did not return an object")
                return _normalize_context(parsed, business)
            except (json.JSONDecodeError, ValueError) as exc:
                last_exc = exc
                logger.warning(
                    "Claude scrape attempt %d/3 failed for %s: %s",
                    attempt, business.business_name, exc,
                )
                if attempt < 3:
                    await asyncio.sleep(2)

        logger.error("All Claude scrape attempts failed for %s: %s", business.business_name, last_exc)
        return _minimal_context(business)
    except Exception as exc:
        logger.error("Claude extraction failed for %s: %s", business.business_name, exc)
        return _minimal_context(business)


async def scrape_business_context(business: Business) -> dict:
    try:
        socket.getaddrinfo("google.com", 80)
        logger.info("DNS resolution working")
    except Exception as e:
        logger.error(f"DNS resolution failed: {e}")

    context = await _infer_with_claude(business)
    if not context:
        return _minimal_context(business)
    return context
