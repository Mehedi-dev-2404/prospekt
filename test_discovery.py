import asyncio

from pipeline.discovery import discover_businesses


def main() -> None:
    businesses = asyncio.run(discover_businesses("Shoreditch, London", "restaurants"))

    print(f"Businesses found: {len(businesses)}")
    for business in businesses:
        print(
            f"- Name: {business.business_name} | "
            f"Address: {business.address_full} | "
            f"Has Website: {business.has_website}"
        )


if __name__ == "__main__":
    main()
