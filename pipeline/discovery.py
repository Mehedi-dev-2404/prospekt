import logging
import re
from typing import Any
from urllib.parse import quote_plus

import httpx

from config import settings
from models.business import BusinessCreate

MOCK_MODE = False

GOOGLE_PLACES_API_KEY = settings.GOOGLE_PLACES_API_KEY
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

logger = logging.getLogger(__name__)

# Broad UK postcode matcher, e.g. "EC1A 1BB", "W1A 0AX", "M1 1AE"
UK_POSTCODE_PATTERN = re.compile(
    r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b",
    re.IGNORECASE,
)


def _extract_postcode(address: str) -> str:
    if not address:
        return ""

    match = UK_POSTCODE_PATTERN.search(address)
    if not match:
        return ""

    postcode = re.sub(r"\s+", " ", match.group(1).strip().upper())
    if len(postcode) > 3 and " " not in postcode:
        # Normalize postcodes that arrive without space, e.g. "EC1A1BB" -> "EC1A 1BB"
        postcode = f"{postcode[:-3]} {postcode[-3:]}"
    return postcode


async def _fetch_place_details(client: httpx.AsyncClient, place_id: str) -> dict[str, Any]:
    response = await client.get(
        DETAILS_URL,
        params={
            "place_id": place_id,
            "fields": "website,formatted_phone_number",
            "key": GOOGLE_PLACES_API_KEY,
        },
    )
    response.raise_for_status()

    payload = response.json()
    if payload.get("status") not in ("OK", "ZERO_RESULTS"):
        raise ValueError(f"Google Place Details error: {payload.get('status')}")

    return payload.get("result", {})


def _build_mock_businesses(location: str, category: str = None) -> list[BusinessCreate]:
    fallback_category = category or "general"
    mock_rows = [
        {
            "business_name": "Shoreditch Brew House",
            "address_full": "45 Redchurch St, Shoreditch, London E2 7DJ, UK",
            "postcode": "E2 7DJ",
            "category": category or "cafes",
            "website_url": "https://shoreditchbrewhouse.co.uk",
            "has_website": True,
            "phone_primary": "+44 20 7123 4567",
            "google_maps_url": "https://www.google.com/maps/place/?q=place_id:mock_place_1",
            "google_rating": 4.6,
            "google_review_count": 238,
        },
        {
            "business_name": "East End Cycle Repair",
            "address_full": "12 Bethnal Green Rd, London E1 6GY, UK",
            "postcode": "E1 6GY",
            "category": category or "bike shops",
            "website_url": None,
            "has_website": False,
            "phone_primary": "+44 20 7001 9988",
            "google_maps_url": "https://www.google.com/maps/place/?q=place_id:mock_place_2",
            "google_rating": 4.3,
            "google_review_count": 89,
        },
        {
            "business_name": "Brick Lane Dental Studio",
            "address_full": "101 Brick Ln, London E1 6SE, UK",
            "postcode": "E1 6SE",
            "category": category or "dentists",
            "website_url": "https://bricklanedental.co.uk",
            "has_website": True,
            "phone_primary": "+44 20 7456 1122",
            "google_maps_url": "https://www.google.com/maps/place/?q=place_id:mock_place_3",
            "google_rating": 4.8,
            "google_review_count": 164,
        },
        {
            "business_name": "Hackney Fitness Works",
            "address_full": "7 Great Eastern St, London EC2A 3EJ, UK",
            "postcode": "EC2A 3EJ",
            "category": category or "gyms",
            "website_url": "https://hackneyfitnessworks.com",
            "has_website": True,
            "phone_primary": None,
            "google_maps_url": "https://www.google.com/maps/place/?q=place_id:mock_place_4",
            "google_rating": 4.1,
            "google_review_count": 57,
        },
        {
            "business_name": "Canal Side Flowers",
            "address_full": "22 Kingsland Rd, London E2 8AA, UK",
            "postcode": "E2 8AA",
            "category": fallback_category,
            "website_url": None,
            "has_website": False,
            "phone_primary": "+44 20 7999 3344",
            "google_maps_url": "https://www.google.com/maps/place/?q=place_id:mock_place_5",
            "google_rating": 4.5,
            "google_review_count": 41,
        },
    ]

    # BusinessCreate currently accepts core fields; extra fields are ignored by Pydantic defaults.
    return [BusinessCreate(**row) for row in mock_rows]


async def discover_businesses(location: str, category: str = None) -> list[BusinessCreate]:
    if MOCK_MODE:
        return _build_mock_businesses(location=location, category=category)

    query_category = category or "businesses"
    query = f"{query_category} in {location}"
    discovered: list[BusinessCreate] = []

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            search_response = await client.get(
                TEXT_SEARCH_URL,
                params={"query": query, "key": GOOGLE_PLACES_API_KEY},
            )
            search_response.raise_for_status()
            search_payload = search_response.json()

            if search_payload.get("status") not in ("OK", "ZERO_RESULTS"):
                logger.error(
                    "Google Places Text Search failed: status=%s query=%s",
                    search_payload.get("status"),
                    query,
                )
                return []

            for result in search_payload.get("results", []):
                try:
                    place_id = result.get("place_id")
                    if not place_id:
                        continue

                    details = await _fetch_place_details(client=client, place_id=place_id)

                    business_name = result.get("name", "").strip()
                    address_full = result.get("formatted_address", "").strip()
                    postcode = _extract_postcode(address_full)
                    website_url = details.get("website")
                    phone_primary = details.get("formatted_phone_number")

                    payload = {
                        "business_name": business_name,
                        "address_full": address_full,
                        "postcode": postcode or "",
                        "category": category or "general",
                        "website_url": website_url,
                        "has_website": bool(website_url),
                        "phone_primary": phone_primary,
                        "google_maps_url": (
                            f"https://www.google.com/maps/place/?q=place_id:{quote_plus(place_id)}"
                        ),
                        "google_rating": result.get("rating"),
                        "google_review_count": result.get("user_ratings_total"),
                    }

                    if not payload["business_name"] or not payload["address_full"]:
                        continue

                    discovered.append(BusinessCreate(**payload))
                except Exception as parse_error:
                    logger.warning(
                        "Skipping business due to parsing failure: %s",
                        parse_error,
                    )
                    continue
    except Exception as api_error:
        logger.error("Business discovery failed for '%s': %s", location, api_error)
        return []

    return discovered
