import base64
import json
import logging
import random
import re
from email.message import Message
from typing import Any, Optional

import httpx
from anthropic import AsyncAnthropic

from config import settings
from models.business import Business

MOCK_MODE = True

ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
SLACK_WEBHOOK_URL = settings.SLACK_WEBHOOK_URL
GMAIL_CREDENTIALS_PATH = settings.GMAIL_CREDENTIALS_PATH

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
CLAUDE_SYSTEM_PROMPT = (
    "You are a sales assistant. Classify email replies as interested or not interested."
)

logger = logging.getLogger(__name__)


def _mock_reply_text(business: Business) -> str:
    interested_templates = [
        f"Hey — thanks for this. The demo looks good. Can we chat next week about costs for {business.business_name}?",
        f"Appreciate you sending this over. We might be interested — what would it take to go live for {business.postcode}?",
        "This is actually pretty timely. Can you share pricing and how long a full build usually takes?",
    ]
    not_interested_templates = [
        "Thanks for reaching out — we're all set right now.",
        "Appreciate it, but not something we're looking at at the moment.",
        "Thanks, please remove me from your list.",
    ]
    if random.random() < 0.5:
        return random.choice(interested_templates)
    return random.choice(not_interested_templates)


def _minimal_result() -> dict:
    return {"replied": False, "classification": None, "reply_content": None}


async def _classify_reply_with_claude(reply_content: str) -> tuple[str, str]:
    """
    Returns (classification, confidence). On failure defaults to ('not_interested','low').
    """
    try:
        client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        user_prompt = (
            "Classify this email reply.\n"
            'Return ONLY a JSON object: {"classification": "interested" | "not_interested", '
            '"confidence": "high" | "medium" | "low", "reason": "<string>"}\n\n'
            f"Reply:\n{reply_content}"
        )

        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=200,
            system=CLAUDE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text_parts: list[str] = []
        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "text":
                text_parts.append(getattr(block, "text", ""))
        raw = "\n".join(part for part in text_parts if part).strip()
        data = json.loads(raw)

        classification = str(data.get("classification", "not_interested")).strip()
        confidence = str(data.get("confidence", "low")).strip()

        if classification not in ("interested", "not_interested"):
            classification = "not_interested"
        if confidence not in ("high", "medium", "low"):
            confidence = "low"

        return classification, confidence
    except Exception as exc:
        logger.error("Claude classification failed: %s", exc)
        return "not_interested", "low"


async def _send_slack_alert(
    business: Business,
    reply_content: str,
    confidence: str,
) -> None:
    if not SLACK_WEBHOOK_URL:
        logger.error("SLACK_WEBHOOK_URL is missing; cannot send Slack alert.")
        return

    demo_url = business.demo_url or "N/A"
    location = business.address_full or business.postcode or "Unknown"
    email = business.email_primary or "Unknown"

    text = (
        "*Prospekt Lead Reply — Interested*\n"
        f"- Business: {business.business_name} ({business.category})\n"
        f"- Location: {location}\n"
        f"- Email: {email}\n"
        f"- Demo URL: {demo_url}\n"
        f"- Reply: {reply_content}\n"
        f"- Confidence: {confidence}\n"
        "\n"
        "Action required: follow up with this lead"
    )

    payload = {"text": text}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(SLACK_WEBHOOK_URL, json=payload)
            if resp.status_code >= 400:
                logger.error("Slack webhook failed: status=%s body=%s", resp.status_code, resp.text)
    except Exception as exc:
        logger.error("Slack webhook request failed: %s", exc)


def _decode_gmail_body(payload: dict[str, Any]) -> Optional[str]:
    """
    Extract plain text from Gmail message payload (best-effort).
    """

    def decode_data(data: str) -> str:
        # Gmail uses URL-safe base64 without padding sometimes
        pad = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode((data + pad).encode("utf-8")).decode(
            "utf-8", errors="replace"
        )

    mime_type = payload.get("mimeType")
    body = payload.get("body", {}) or {}
    data = body.get("data")

    if mime_type == "text/plain" and data:
        return decode_data(data).strip()

    # Multipart: recurse parts
    for part in payload.get("parts", []) or []:
        part_type = part.get("mimeType")
        part_body = part.get("body", {}) or {}
        part_data = part_body.get("data")
        if part_type == "text/plain" and part_data:
            return decode_data(part_data).strip()

    return None


def _has_in_reply_to_header(headers: list[dict[str, str]]) -> bool:
    for h in headers or []:
        if h.get("name", "").lower() == "in-reply-to" and h.get("value"):
            return True
    return False


async def _check_gmail_for_reply(business: Business) -> Optional[str]:
    """
    Returns reply plain text content if found; otherwise None.

    NOTE: This function uses Gmail API. Dependencies are imported lazily so MOCK_MODE
    can run without Gmail packages installed.
    """
    if not GMAIL_CREDENTIALS_PATH:
        logger.error("GMAIL_CREDENTIALS_PATH is not set.")
        return None

    try:
        # Lazy imports to avoid hard dependency for mock/testing.
        from googleapiclient.discovery import build  # type: ignore
        from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore

        # Minimal scope to read messages.
        scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

        flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, scopes=scopes)
        creds = flow.run_local_server(port=0)

        service = build("gmail", "v1", credentials=creds)

        # Search: last 7 days, subject contains business name.
        # Gmail doesn't expose "has In-Reply-To" in query reliably; we'll filter headers after fetching.
        query = f'newer_than:7d subject:"{business.business_name}"'

        results = service.users().messages().list(userId="me", q=query, maxResults=10).execute()
        messages = results.get("messages", []) or []
        if not messages:
            return None

        for msg in messages:
            msg_id = msg.get("id")
            if not msg_id:
                continue
            full = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )

            payload = full.get("payload", {}) or {}
            headers = payload.get("headers", []) or []
            if not _has_in_reply_to_header(headers):
                continue

            text = _decode_gmail_body(payload)
            if text:
                return text

        return None
    except Exception as exc:
        logger.error("Gmail check failed for %s: %s", business.business_name, exc)
        return None


async def monitor_replies(business: Business) -> dict:
    """
    Returns: {"replied": bool, "classification": str|None, "reply_content": str|None}
    """
    if MOCK_MODE:
        if random.random() < 0.5:
            return _minimal_result()

        reply_content = _mock_reply_text(business)
        classification = random.choice(["interested", "not_interested"])
        confidence = random.choice(["high", "medium", "low"])

        if classification == "interested":
            # Print the Slack alert that would be sent.
            demo_url = business.demo_url or "N/A"
            location = business.address_full or business.postcode or "Unknown"
            email = business.email_primary or "Unknown"
            print("=== MOCK SLACK ALERT ===")
            print(f"Business: {business.business_name} ({business.category})")
            print(f"Location: {location}")
            print(f"Email: {email}")
            print(f"Demo URL: {demo_url}")
            print(f"Reply: {reply_content}")
            print(f"Confidence: {confidence}")
            print("Action required: follow up with this lead")
            print("========================")

        return {
            "replied": True,
            "classification": classification,
            "reply_content": reply_content,
        }

    try:
        reply_content = await _check_gmail_for_reply(business)
        if not reply_content:
            return _minimal_result()

        classification, confidence = await _classify_reply_with_claude(reply_content)

        if classification == "interested":
            await _send_slack_alert(business, reply_content, confidence)

        return {
            "replied": True,
            "classification": classification,
            "reply_content": reply_content,
        }
    except Exception:
        # Hard safety net.
        return _minimal_result()
