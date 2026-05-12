import asyncio
import logging
import re

import httpx

from config import settings

MOCK_MODE = False

VERCEL_API_TOKEN = settings.VERCEL_API_TOKEN
VERCEL_DEPLOYMENTS_URL = "https://api.vercel.com/v13/deployments"

logger = logging.getLogger(__name__)


def _slugify_business_name(business_name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", business_name.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug:
        slug = "prospekt-site"
    return slug[:50]


def _format_url(url_value: str) -> str:
    if not url_value:
        return ""
    if url_value.startswith("http://") or url_value.startswith("https://"):
        return url_value
    return f"https://{url_value}"


async def deploy_landing_page(business_name: str, html: str) -> str | None:
    slug = _slugify_business_name(business_name)

    if MOCK_MODE:
        return f"https://mock-{slug}.vercel.app"

    if not html.strip():
        logger.error("Deployment aborted: empty HTML content for business '%s'.", business_name)
        return None

    headers = {"Authorization": f"Bearer {VERCEL_API_TOKEN}"}
    payload = {
        "name": slug,
        "files": [{"file": "index.html", "data": html}],
        "projectSettings": {"framework": None},
        "target": "production",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            create_response = await client.post(
                VERCEL_DEPLOYMENTS_URL,
                headers=headers,
                json=payload,
            )
            create_response.raise_for_status()
            deployment = create_response.json()

            deployment_id = deployment.get("id")
            if not deployment_id:
                logger.error("Vercel deployment response missing id: %s", deployment)
                return None

            deployment_url = deployment.get("url")
            deployment_status_url = f"{VERCEL_DEPLOYMENTS_URL}/{deployment_id}"

            for attempt in range(10):
                status_response = await client.get(deployment_status_url, headers=headers)
                status_response.raise_for_status()
                status_payload = status_response.json()

                ready_state = status_payload.get("readyState")
                deployment_url = status_payload.get("url", deployment_url)

                if ready_state == "READY":
                    if deployment_url:
                        return _format_url(deployment_url)
                    logger.error("Deployment READY but URL missing: %s", status_payload)
                    return None

                if ready_state == "ERROR":
                    logger.error("Vercel deployment failed: %s", status_payload)
                    return None

                if attempt < 9:
                    await asyncio.sleep(3)

            logger.error(
                "Vercel deployment timed out after max attempts for business '%s'.",
                business_name,
            )
            return None
    except Exception as exc:
        logger.error("Failed to deploy landing page for '%s': %s", business_name, exc)
        return None
