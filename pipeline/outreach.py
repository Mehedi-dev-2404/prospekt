import base64
import json
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from anthropic import AsyncAnthropic
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import settings
from models.business import Business

MOCK_MODE = False

ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
GMAIL_FROM_EMAIL = settings.GMAIL_FROM_EMAIL

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
SYSTEM_PROMPT = (
    "You are an expert cold email copywriter. You write short, friendly, personalised cold emails "
    "that get replies. Never sound robotic or salesy."
)

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
        f"- Use the business name '{business_name}' directly in the email — do NOT use any placeholder syntax like {{{{BUSINESS_NAME}}}}, [BUSINESS_NAME], or similar\n"
        "- Do NOT use any placeholder syntax like {{{{FIRST_NAME}}}}, {{{{YOUR_NAME}}}}, [NAME], or any other {{{{...}}}} or [[...]] patterns — write the actual values directly\n"
        "- The recipient's first name is unknown, so open with a friendly greeting like 'Hi there,' or 'Hello,'\n"
        "- Reference their specific location\n"
        "- Include the demo URL naturally\n"
        "- End with a soft CTA\n"
        "- Sign off as 'The OmniCode Creations Team' — do not use a personal name or placeholder\n"
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
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
        data = json.loads(raw.strip())
        if not isinstance(data, dict):
            return None

        subject = str(data.get("subject", "")).strip()
        body = str(data.get("body", "")).strip()
        if not subject or not body:
            return None

        # Safety: replace any leftover placeholder patterns Claude may have used
        import re

        def _fix_placeholders(text: str) -> str:
            text = re.sub(r"\{\{FIRST_NAME\}\}", "there", text, flags=re.IGNORECASE)
            text = re.sub(r"\{\{BUSINESS_NAME\}\}", business_name, text, flags=re.IGNORECASE)
            text = re.sub(r"\{\{YOUR_NAME\}\}", "The OmniCode Creations Team", text, flags=re.IGNORECASE)
            text = re.sub(r"\{\{[^}]*\}\}", "", text)  # remove any other {{...}}
            return text

        subject = _fix_placeholders(subject)
        body = _fix_placeholders(body)

        return {"subject": subject, "body": body}
    except Exception as exc:
        logger.error("Claude email drafting failed for %s: %s", business.business_name, exc)
        return None


def _build_gmail_service():
    token_json = settings.GMAIL_TOKEN_JSON
    if not token_json:
        raise ValueError("GMAIL_TOKEN_JSON env var is not set")

    token_data = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(token_data)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("gmail", "v1", credentials=creds)


def _send_with_gmail(to_email: str, subject: str, body: str) -> bool:
    try:
        service = _build_gmail_service()

        message = MIMEMultipart()
        message["From"] = GMAIL_FROM_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True
    except Exception as exc:
        logger.error("Gmail send failed: %s", exc)
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
        print(f"From: {GMAIL_FROM_EMAIL}")
        print(f"Subject: {subject}")
        print()
        print(body)
        print("===========================")
        return True

    drafted = await _draft_email_with_claude(business, context, demo_url)
    if not drafted:
        return False

    return _send_with_gmail(
        to_email=business.email_primary,
        subject=drafted["subject"],
        body=drafted["body"],
    )
