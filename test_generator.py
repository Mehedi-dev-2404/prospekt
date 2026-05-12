import asyncio
from uuid import uuid4

from models.business import Business
from pipeline.generator import generate_landing_page


async def main():
    business = Business(
        business_id=uuid4(),
        business_name="Sunrise Plumbing",
        category="Plumbing",
        address_full="42 High Street, Manchester, M1 2AB",
        postcode="M1 2AB",
        phone_primary="0161 123 4567",
        email_primary="hello@sunriseplumbing.co.uk",
        google_rating=4.8,
        google_review_count=127,
    )

    context = {
        "services": [
            "Emergency Repairs",
            "Boiler Installation",
            "Drain Unblocking",
            "Bathroom Fitting",
            "Leak Detection",
        ],
        "primary_color": "#0ea5e9",
        "tone": "friendly and professional",
    }

    html = await generate_landing_page(business, context)

    with open("test_output.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("Done. Output saved to test_output.html")


if __name__ == "__main__":
    asyncio.run(main())
