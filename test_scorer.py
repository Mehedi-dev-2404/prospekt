import asyncio

from models.business import Business
from pipeline.scorer import score_business


def main() -> None:
    business_with_site = Business(
        business_name="Example Website Ltd",
        category="services",
        address_full="1 Example Street, London EC1A 1BB, UK",
        postcode="EC1A 1BB",
        has_website=True,
        website_url="https://example.com",
    )

    business_without_site = Business(
        business_name="No Site Corner Shop",
        category="retail",
        address_full="2 Sample Road, London E1 6GY, UK",
        postcode="E1 6GY",
        has_website=False,
        website_url=None,
    )

    score_1, reason_1 = asyncio.run(score_business(business_with_site))
    score_2, reason_2 = asyncio.run(score_business(business_without_site))

    print(f"With website -> score: {score_1}, reason: {reason_1}")
    print(f"Without website -> score: {score_2}, reason: {reason_2}")


if __name__ == "__main__":
    main()
