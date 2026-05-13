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
        "public": True,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            logger.info("Creating Vercel deployment for '%s' (slug: %s).", business_name, slug)
            create_response = await client.post(
                VERCEL_DEPLOYMENTS_URL,
                headers=headers,
                json=payload,
            )
            if not create_response.is_success:
                logger.error(
                    "Vercel create deployment failed [%s] for '%s': %s",
                    create_response.status_code,
                    business_name,
                    create_response.text,
                )
                return None
            deployment = create_response.json()

            deployment_id = deployment.get("id")
            if not deployment_id:
                logger.error("Vercel deployment response missing id for '%s': %s", business_name, deployment)
                return None

            deployment_url = deployment.get("url")
            deployment_status_url = f"{VERCEL_DEPLOYMENTS_URL}/{deployment_id}"
            logger.info("Deployment created (id: %s), polling for READY state.", deployment_id)

            for attempt in range(10):
                status_response = await client.get(deployment_status_url, headers=headers)
                if not status_response.is_success:
                    logger.error(
                        "Vercel status poll failed [%s] on attempt %d for '%s': %s",
                        status_response.status_code,
                        attempt + 1,
                        business_name,
                        status_response.text,
                    )
                    return None
                status_payload = status_response.json()

                ready_state = status_payload.get("readyState")
                deployment_url = status_payload.get("url", deployment_url)
                logger.info("Attempt %d: readyState=%s url=%s", attempt + 1, ready_state, deployment_url)

                if ready_state == "READY":
                    if not deployment_url:
                        logger.error("Deployment READY but URL missing for '%s': %s", business_name, status_payload)
                        return None

                    # Disable SSO/password protection on the project
                    patch_url = f"https://api.vercel.com/v9/projects/{slug}"
                    patch_payload = {
                        "ssoProtection": None,
                        "passwordProtection": None,
                    }
                    patch_response = await client.patch(patch_url, headers=headers, json=patch_payload)
                    if not patch_response.is_success:
                        logger.error(
                            "Failed to disable protection on project '%s' [%s]: %s",
                            slug,
                            patch_response.status_code,
                            patch_response.text,
                        )
                    else:
                        logger.info("Protection disabled for project '%s'.", slug)

                    return _format_url(deployment_url)

                if ready_state == "ERROR":
                    logger.error("Vercel deployment errored for '%s': %s", business_name, status_payload)
                    return None

                if attempt < 9:
                    await asyncio.sleep(3)

            logger.error(
                "Vercel deployment timed out after max attempts for business '%s'.",
                business_name,
            )
            return None
    except Exception as exc:
        logger.error("Unhandled exception deploying '%s': %s", business_name, exc, exc_info=True)
        return None
