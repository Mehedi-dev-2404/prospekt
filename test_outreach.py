import asyncio

from models.business import Business
from pipeline.outreach import send_outreach_email


def main() -> None:
    business = Business(
        business_name="Brick Lane Dental Studio",
        category="dentist",
        address_full="101 Brick Lane, London E1 6SE, UK",
        postcode="E1 6SE",
        has_website=True,
        website_url="https://example.com",
        email_primary="owner@example.com",
    )

    # Fake context (based on test_scraper output shape)
    context = {
        "business_name": "Brick Lane Dental Studio",
        "tagline": "Friendly dental care in the heart of East London.",
        "description": (
            "Brick Lane Dental Studio provides modern dental care with a calm, welcoming approach. "
            "From routine check-ups to cosmetic treatments, the focus is on comfort and clear communication."
        ),
        "tone": "friendly",
        "primary_color": "#0EA5E9",
        "logo_url": "https://example.com/assets/logo.png",
        "services": [
            "Dental check-ups",
            "Hygiene & cleaning",
            "Teeth whitening",
            "Cosmetic dentistry",
            "Emergency appointments",
        ],
        "location": "101 Brick Lane, London E1 6SE",
        "category": "dentist",
    }

    ok = asyncio.run(
        send_outreach_email(
            business=business,
            context=context,
            demo_url="https://demo.example.com/brick-lane-dental-studio",
        )
    )

    print(f"Succeeded: {ok}")


if __name__ == "__main__":
    main()
