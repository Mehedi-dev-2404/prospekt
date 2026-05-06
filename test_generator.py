import asyncio

from models.business import Business
from pipeline.generator import generate_landing_page
from pipeline.scraper import scrape_business_context


def main() -> None:
    business = Business(
        business_name="Brick Lane Dental Studio",
        category="dentist",
        address_full="101 Brick Lane, London E1 6SE",
        postcode="E1 6SE",
        has_website=True,
        website_url="https://example.com",
    )

    context = asyncio.run(scrape_business_context(business))
    html = asyncio.run(generate_landing_page(business, context))

    with open("test_output.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("Done — open test_output.html to preview")


if __name__ == "__main__":
    main()
