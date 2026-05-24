import asyncio
from pipeline.orchestrator import _find_email
from models.business import Business

business = Business(
    business_name="403 Barber Lane Brixton",
    website_url="https://www.403barberlane.com",
    email_primary=None,
    category="barbers",
    address_full="403 Barber Lane, Brixton, London",
    postcode="SW9 8JT",
)

result = asyncio.run(_find_email(business))
print(f"Result: {result}")
