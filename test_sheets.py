import asyncio

from models.business import Business
from sheets.poller import poll_approval_status
from sheets.sync import sync_businesses_to_sheets


def main() -> None:
    businesses = [
        Business(
            business_name="Shoreditch Brew House",
            category="restaurant",
            address_full="45 Redchurch St, Shoreditch, London E2 7DJ, UK",
            postcode="E2 7DJ",
            has_website=True,
            website_url="https://shoreditchbrewhouse.co.uk",
            website_score=72,
            email_primary="hello@shoreditchbrewhouse.co.uk",
            phone_primary="+44 20 7123 4567",
            google_rating=4.6,
            google_review_count=238,
            campaign_status="pending",
            notes="Great reviews; strong candidate.",
        ),
        Business(
            business_name="East End Cycle Repair",
            category="bike shop",
            address_full="12 Bethnal Green Rd, London E1 6GY, UK",
            postcode="E1 6GY",
            has_website=False,
            website_url=None,
            website_score=None,
            email_primary="info@eastendcycles.co.uk",
            phone_primary="+44 20 7001 9988",
            google_rating=4.3,
            google_review_count=89,
            campaign_status="pending",
            notes="No website; might be a good outreach angle.",
        ),
        Business(
            business_name="Brick Lane Dental Studio",
            category="dentist",
            address_full="101 Brick Ln, London E1 6SE, UK",
            postcode="E1 6SE",
            has_website=True,
            website_url="https://bricklanedental.co.uk",
            website_score=54,
            email_primary="reception@bricklanedental.co.uk",
            phone_primary="+44 20 7456 1122",
            google_rating=4.8,
            google_review_count=164,
            campaign_status="pending",
            notes="Good fit for demo landing page.",
        ),
        Business(
            business_name="Hackney Fitness Works",
            category="gym",
            address_full="7 Great Eastern St, London EC2A 3EJ, UK",
            postcode="EC2A 3EJ",
            has_website=True,
            website_url="https://hackneyfitnessworks.com",
            website_score=38,
            email_primary="team@hackneyfitnessworks.com",
            phone_primary=None,
            google_rating=4.1,
            google_review_count=57,
            campaign_status="pending",
            notes="Website looks dated; high improvement potential.",
        ),
        Business(
            business_name="Canal Side Flowers",
            category="florist",
            address_full="22 Kingsland Rd, London E2 8AA, UK",
            postcode="E2 8AA",
            has_website=False,
            website_url=None,
            website_score=None,
            email_primary="orders@canalsideflowers.co.uk",
            phone_primary="+44 20 7999 3344",
            google_rating=4.5,
            google_review_count=41,
            campaign_status="pending",
            notes="Seasonal demand; good local brand.",
        ),
    ]

    job_id = "job-test-123"

    ok = asyncio.run(sync_businesses_to_sheets(businesses, job_id))
    result = asyncio.run(poll_approval_status(job_id))

    print(f"Sync result: {ok}")
    print(f"Approved: {result.get('approved')}")
    print(f"Rejected: {result.get('rejected')}")


if __name__ == "__main__":
    main()

