import json
import logging
from typing import Any, Optional

import httpx
from anthropic import AsyncAnthropic

from config import settings
from models.business import Business

MOCK_MODE = True

ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
SYSTEM_PROMPT = (
    "You are a business analyst. Extract structured information from website content."
)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
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


def _mock_context(business: Business) -> dict:
    return {
        "business_name": business.business_name,
        "tagline": f"Trusted {business.category} specialists serving local customers.",
        "description": (
            f"{business.business_name} is a local {business.category} brand known for reliable service "
            f"and customer-focused delivery. They emphasize practical outcomes, transparent communication, "
            "and a polished customer experience."
        ),
        "tone": "friendly",
        "primary_color": "#0EA5E9",
        "logo_url": "https://example.com/assets/logo.png",
        "services": [
            f"{business.category.title()} consulting",
            f"{business.category.title()} installation",
            "Maintenance and support",
            "Custom packages",
            "Free quote and assessment",
        ],
        "location": business.address_full or business.postcode or "London",
    }


async def _fetch_website_html(url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(
            timeout=10.0,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except Exception as exc:
        logger.warning("Failed to fetch website HTML for %s: %s", url, exc)
        return None


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


async def _infer_with_claude(
    business: Business,
    html: Optional[str],
) -> dict:
    try:
        client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

        if html:
            truncated_html = html[:3000]
            user_prompt = (
                "Extract structured business context from the following website HTML snippet.\n"
                "Return ONLY a JSON object with exactly these keys:\n"
                "business_name, tagline, description, tone, primary_color, logo_url, services, location.\n\n"
                f"Business hint name: {business.business_name}\n"
                f"Business hint category: {business.category}\n\n"
                "HTML snippet:\n"
                f"{truncated_html}"
            )
        else:
            user_prompt = (
                "No website HTML is available. Infer structured business context from the following details.\n"
                "Return ONLY a JSON object with exactly these keys:\n"
                "business_name, tagline, description, tone, primary_color, logo_url, services, location.\n\n"
                f"Business name: {business.business_name}\n"
                f"Category: {business.category}\n"
                f"Address: {business.address_full}\n"
                f"Postcode: {business.postcode}"
            )

        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_text = _extract_text_from_response(response)
        parsed = json.loads(raw_text)
        if not isinstance(parsed, dict):
            raise ValueError("Claude did not return an object")
        return _normalize_context(parsed, business)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Claude JSON response for %s: %s", business.business_name, exc)
        return _minimal_context(business)
    except Exception as exc:
        logger.error("Claude extraction failed for %s: %s", business.business_name, exc)
        return _minimal_context(business)


async def scrape_business_context(business: Business) -> dict:
    if MOCK_MODE:
        return _mock_context(business)

    html: Optional[str] = None
    if business.website_url:
        html = await _fetch_website_html(business.website_url)

    # If fetch fails, we still ask Claude to infer from business metadata.
    context = await _infer_with_claude(business, html)
    if not context:
        return _minimal_context(business)
    return context
