import asyncio

from models.business import Business
from pipeline.monitor import monitor_replies


def main() -> None:
    business = Business(
        business_name="Brick Lane Dental Studio",
        category="dentist",
        address_full="101 Brick Lane, London E1 6SE, UK",
        postcode="E1 6SE",
        email_primary="owner@example.com",
        demo_url="https://demo.example.com/brick-lane-dental-studio",
        has_website=True,
        website_url="https://example.com",
    )

    for i in range(3):
        result = asyncio.run(monitor_replies(business))
        print(f"Run {i + 1}: {result}")


if __name__ == "__main__":
    main()

