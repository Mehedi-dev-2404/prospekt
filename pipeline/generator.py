import logging
from html import escape

from anthropic import AsyncAnthropic

from config import settings
from database import supabase
from models.business import Business

MOCK_MODE = False

ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
CLAUDE_MODEL = "claude-sonnet-4-6"
SYSTEM_PROMPT = (
    "You are an expert web designer. You create beautiful, modern, single-file HTML/CSS "
    "landing pages for local businesses. You only return raw HTML with no explanation, "
    "no markdown, no code blocks."
)

logger = logging.getLogger(__name__)


def _minimal_html(business_name: str) -> str:
    safe_name = escape(business_name or "Local Business")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{safe_name}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
    .wrap {{ max-width: 900px; margin: 0 auto; padding: 2rem 1rem; }}
    .banner {{ background: #e2e8f0; text-align: center; padding: .5rem; font-size: .9rem; }}
    h1 {{ margin-top: 1rem; }}
  </style>
</head>
<body>
  <div class="banner">This is a demo website created by OmniCode Creations</div>
  <main class="wrap">
    <h1>{safe_name}</h1>
    <p>Welcome to our website.</p>
  </main>
</body>
</html>"""


def _mock_html(business: Business, context: dict) -> str:
    business_name = escape(context.get("business_name") or business.business_name)
    category = escape(context.get("category") or business.category)
    tagline = escape(context.get("tagline") or f"Trusted {business.category} services")
    primary_color = escape(context.get("primary_color") or "#2563EB")
    location = escape(context.get("location") or business.address_full or "Local area")
    services = context.get("services") or [business.category]
    service_items = "\n".join(
        f"<li>{escape(str(service))}</li>" for service in services[:5]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{business_name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet" />
  <style>
    :root {{ --brand: {primary_color}; --bg: #f8fafc; --text: #0f172a; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); }}
    .banner {{ background: #e2e8f0; text-align: center; font-size: .9rem; padding: .55rem; }}
    .hero {{
      padding: 5rem 1.25rem 3rem;
      color: white;
      background: radial-gradient(circle at top right, #ffffff22, transparent 45%), var(--brand);
    }}
    .container {{ max-width: 1100px; margin: 0 auto; }}
    .hero h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 3.4rem); }}
    .hero p {{ margin-top: .8rem; max-width: 56ch; opacity: .95; }}
    .card {{
      background: white; border-radius: 16px; padding: 1.25rem; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    }}
    .section {{ padding: 2.5rem 1.25rem; }}
    .grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    ul {{ margin: 0; padding-left: 1.2rem; line-height: 1.8; }}
    footer {{ text-align: center; padding: 2rem 1rem; color: #475569; }}
  </style>
</head>
<body>
  <div class="banner">This is a demo website created by OmniCode Creations</div>
  <header class="hero">
    <div class="container">
      <h1>{business_name}</h1>
      <p>{tagline}</p>
    </div>
  </header>
  <main class="container">
    <section class="section">
      <div class="grid">
        <article class="card">
          <h2>Services</h2>
          <ul>{service_items}</ul>
        </article>
        <article class="card">
          <h2>About</h2>
          <p>{business_name} is a trusted {category} business focused on high-quality outcomes and great customer experience.</p>
        </article>
        <article class="card">
          <h2>Contact & Location</h2>
          <p>{location}</p>
        </article>
      </div>
    </section>
  </main>
  <footer>&copy; {business_name}. All rights reserved.</footer>
</body>
</html>"""


async def _generate_with_claude(business: Business, context: dict) -> str:
    business_name = context.get("business_name") or business.business_name
    category = context.get("category") or business.category
    tagline = context.get("tagline") or ""
    description = context.get("description") or ""
    tone = context.get("tone") or "professional"
    primary_color = context.get("primary_color") or "#2563EB"
    services = context.get("services") or [category]
    location = context.get("location") or business.address_full or business.postcode

    if isinstance(services, list):
        services_lines = "\n".join(f"- {str(service)}" for service in services[:5])
    else:
        services_lines = f"- {str(services)}"

    user_prompt = (
        "Create a complete single-file HTML page.\n"
        "Return only raw HTML.\n\n"
        f"Business name: {business_name}\n"
        f"Category: {category}\n"
        f"Tagline: {tagline}\n"
        f"Description: {description}\n"
        f"Tone: {tone}\n"
        f"Primary color: {primary_color}\n"
        f"Location: {location}\n"
        "Services:\n"
        f"{services_lines}\n\n"
        "Requirements:\n"
        "- Include hero section with business name and tagline\n"
        "- Include services section listing services\n"
        "- Include about section with description\n"
        "- Include contact/location section\n"
        "- Include footer\n"
        "- Embed CSS in the same HTML file (Google Fonts links allowed)\n"
        "- Make it mobile responsive using flexbox and/or grid\n"
        "- Use primary color for color scheme\n"
        "- Professional, modern design\n"
        "- No JavaScript required\n"
        "- No placeholder images; use CSS shapes/gradients\n"
        '- Add subtle top banner text: "This is a demo website created by OmniCode Creations"\n'
    )

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    html_parts: list[str] = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            html_parts.append(getattr(block, "text", ""))

    html = "\n".join(part for part in html_parts if part).strip()
    if not html.rstrip().endswith("</html>"):
        html += "\n</body></html>"
    return html


async def generate_landing_page(business: Business, context: dict) -> str:
    if MOCK_MODE:
        return _mock_html(business, context)

    try:
        html = await _generate_with_claude(business, context)
        if html:
            supabase.table("businesses").update({"demo_html": html}).eq(
                "business_id", str(business.business_id)
            ).execute()
            return html
    except Exception as exc:
        logger.error("Landing page generation failed for %s: %s", business.business_name, exc)

    return _minimal_html(business.business_name)
