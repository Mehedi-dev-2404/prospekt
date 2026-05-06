import base64
import json
import logging
import random

from anthropic import AsyncAnthropic
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from config import settings
from models.business import Business

MOCK_MODE = True

ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_SYSTEM_PROMPT = "You are a web design quality assessor. Score websites objectively."
CLAUDE_USER_PROMPT = (
    "Analyze this website screenshot and score it from 0 to 100 based on:\n"
    "1) visual design quality (modern vs outdated),\n"
    "2) mobile responsiveness indicators,\n"
    "3) clear navigation and structure,\n"
    "4) professional appearance,\n"
    "5) whether it appears to need improvement.\n\n"
    'Return ONLY a JSON object exactly like: {"score": <int>, "reason": "<string>"}'
)
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

logger = logging.getLogger(__name__)


async def _capture_screenshot(url: str) -> bytes:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=DEFAULT_USER_AGENT,
            )
            page = await context.new_page()

            await page.goto(url, wait_until="networkidle", timeout=10_000)
            screenshot_bytes = await page.screenshot(full_page=True, type="png")

            await context.close()
            await browser.close()
            return screenshot_bytes
    except (PlaywrightTimeoutError, Exception) as exc:
        logger.error("Failed to capture website screenshot for %s: %s", url, exc)
        raise


def _extract_text_from_response(response: object) -> str:
    content = getattr(response, "content", [])
    text_parts: list[str] = []

    for block in content:
        if getattr(block, "type", None) == "text":
            text_parts.append(getattr(block, "text", ""))

    return "\n".join(part for part in text_parts if part).strip()


async def _score_with_claude(screenshot_bytes: bytes) -> tuple[int, str]:
    try:
        client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        image_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=256,
            system=CLAUDE_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": CLAUDE_USER_PROMPT},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_b64,
                            },
                        },
                    ],
                }
            ],
        )

        raw_text = _extract_text_from_response(response)
        data = json.loads(raw_text)
        score = int(data.get("score", 0))
        reason = str(data.get("reason", "")).strip()

        if score < 0 or score > 100:
            score = max(0, min(score, 100))

        if not reason:
            reason = "No reason provided"

        return score, reason
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Claude JSON response: %s", exc)
        return 0, "Parse error"
    except Exception as exc:
        logger.error("Claude scoring failed: %s", exc)
        return 0, "Scoring failed"


async def score_business(business: Business) -> tuple[int, str]:
    if not business.has_website or not business.website_url:
        return 0, "No website found"

    if MOCK_MODE:
        score = random.randint(20, 85)
        return score, "Mock assessment suggests the site could improve structure and visual polish."

    try:
        screenshot_bytes = await _capture_screenshot(business.website_url)
    except Exception:
        return 0, "Screenshot failed"

    return await _score_with_claude(screenshot_bytes)
