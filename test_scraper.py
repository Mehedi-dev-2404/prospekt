import asyncio

from models.business import Business
from pipeline.scraper import scrape_business_context


def print_context(title: str, context: dict) -> None:
    print(title)
    for key, value in context.items():
        print(f"{key}: {value}")
    print("-" * 50)


def main() -> None:
    business_with_website = Business(
        business_name="Example Bistro",
        category="restaurant",
        address_full="10 Example Street, London EC1A 1BB, UK",
        postcode="EC1A 1BB",
        has_website=True,
        website_url="https://example.com",
    )

    business_without_website = Business(
        business_name="Sharp Fade Studio",
        category="barbershop",
        address_full="22 Sample Road, London E2 8AA, UK",
        postcode="E2 8AA",
        has_website=False,
        website_url=None,
    )

    context_with_website = asyncio.run(scrape_business_context(business_with_website))
    context_without_website = asyncio.run(scrape_business_context(business_without_website))

    print_context("Business 1 (has_website=True):", context_with_website)
    print_context("Business 2 (has_website=False):", context_without_website)


if __name__ == "__main__":
    main()
