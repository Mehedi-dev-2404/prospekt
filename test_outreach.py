import asyncio
import logging

from config import settings
from models.business import Business
from pipeline.outreach import send_outreach_email

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main() -> None:
    business = Business(
        business_name="403 Barber Lane Brixton",
        category="barbershop",
        address_full="403 Coldharbour Ln, London SW9 8LQ",
        postcode="SW9 8LQ",
        email_primary=settings.GMAIL_FROM_EMAIL,
        has_website=True,
        website_url="https://www.403barberlane.com",
        google_rating=5.0,
        google_review_count=499,
    )

    context = {
        "business_name": "403 Barber Lane Brixton",
        "category": "barbershop",
        "location": "403 Coldharbour Ln, London SW9 8LQ",
        "tagline": "Precision cuts and fresh fades in the heart of Brixton.",
        "description": (
            "403 Barber Lane is a top-rated barbershop on Coldharbour Lane, Brixton. "
            "Known for sharp fades, classic cuts, and a welcoming vibe, it holds a perfect "
            "5-star rating from nearly 500 Google reviews."
        ),
        "tone": "confident, community-focused",
        "primary_color": "#1A1A1A",
        "services": [
            "Skin fades",
            "Classic cuts",
            "Line-ups & edge work",
            "Beard trims",
            "Hot towel shaves",
        ],
        "google_rating": 5.0,
        "google_review_count": 499,
    }

    demo_url = "https://403-barber-lane-brixton-5juqnp479.vercel.app"

    print(f"Sending to: {business.email_primary}")
    print(f"Demo URL:   {demo_url}")
    print()

    ok = asyncio.run(
        send_outreach_email(business=business, context=context, demo_url=demo_url)
    )

    print(f"Succeeded: {ok}")


if __name__ == "__main__":
    main()
