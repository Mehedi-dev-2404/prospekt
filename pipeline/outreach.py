import json
import logging

import httpx
from anthropic import AsyncAnthropic

from config import settings
from models.business import Business

MOCK_MODE = True

ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
SENDGRID_API_KEY = settings.SENDGRID_API_KEY
SENDGRID_FROM_EMAIL = settings.SENDGRID_FROM_EMAIL

CLAUDE_MODEL = "claude-sonnet-4-6"
SYSTEM_PROMPT = (
    "You are an expert cold email copywriter. You write short, friendly, personalised cold emails "
    "that get replies. Never sound robotic or salesy."
)

SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"

logger = logging.getLogger(__name__)


def _extract_text_from_response(response: object) -> str:
    content = getattr(response, "content", [])
    text_parts: list[str] = []

    for block in content:
        if getattr(block, "type", None) == "text":
            text_parts.append(getattr(block, "text", ""))

    return "\n".join(part for part in text_parts if part).strip()


async def _draft_email_with_claude(business: Business, context: dict, demo_url: str) -> dict | None:
    business_name = context.get("business_name") or business.business_name
    category = context.get("category") or business.category
    location = context.get("location") or business.address_full or business.postcode
    tagline = context.get("tagline") or ""

    user_prompt = (
        "Write Email 1 of 3 in a cold outreach sequence.\n"
        "Tone: warm, curious, low pressure.\n"
        "Angle: introduce the demo + curiosity hook.\n\n"
        f"Business name: {business_name}\n"
        f"Category: {category}\n"
        f"Location: {location}\n"
        f"Tagline: {tagline}\n"
        f"Demo URL: {demo_url}\n\n"
        "Constraints:\n"
        "- Subject line personalised to their business name and category\n"
        "- Body is 4–5 sentences max\n"
        "- Mention their business name\n"
        "- Reference their specific location\n"
        "- Include the demo URL naturally\n"
        "- End with a soft CTA\n"
        "- Include this opt-out line at the bottom exactly:\n"
        "  Not interested? Just reply with 'unsubscribe' and I won't contact you again.\n\n"
        'Return ONLY a JSON object: {"subject": "<string>", "body": "<string>"}'
    )

    try:
        client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=350,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw = _extract_text_from_response(response)
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None

        subject = str(data.get("subject", "")).strip()
        body = str(data.get("body", "")).strip()
        if not subject or not body:
            return None

        return {"subject": subject, "body": body}
    except Exception as exc:
        logger.error("Claude email drafting failed for %s: %s", business.business_name, exc)
        return None


async def _send_with_sendgrid(to_email: str, subject: str, body: str) -> bool:
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": SENDGRID_FROM_EMAIL},
        "reply_to": {"email": SENDGRID_FROM_EMAIL},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }

    headers = {"Authorization": f"Bearer {SENDGRID_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(SENDGRID_URL, json=payload, headers=headers)
            if resp.status_code in (200, 202):
                return True

            logger.error(
                "SendGrid send failed: status=%s body=%s",
                resp.status_code,
                resp.text,
            )
            return False
    except Exception as exc:
        logger.error("SendGrid request failed: %s", exc)
        return False


async def send_outreach_email(business: Business, context: dict, demo_url: str) -> bool:
    if not business.email_primary:
        return False

    if MOCK_MODE:
        subject = f"Quick question about {business.business_name}"
        body = (
            f"Hi {business.business_name} team,\n\n"
            f"I put together a quick demo site for {business.business_name} ({business.category}) "
            f"based around {context.get('location') or business.postcode}:\n{demo_url}\n\n"
            "If you like the direction, I can tailor it to match your exact style.\n\n"
            "Not interested? Just reply with 'unsubscribe' and I won't contact you again.\n"
        )
        print("=== MOCK OUTREACH EMAIL ===")
        print(f"To: {business.email_primary}")
        print(f"From: {SENDGRID_FROM_EMAIL}")
        print(f"Subject: {subject}")
        print()
        print(body)
        print("===========================")
        return True

    drafted = await _draft_email_with_claude(business, context, demo_url)
    if not drafted:
        return False

    return await _send_with_sendgrid(
        to_email=business.email_primary,
        subject=drafted["subject"],
        body=drafted["body"],
    )
