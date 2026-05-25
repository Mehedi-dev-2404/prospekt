# Prospekt

Local businesses are consistently underserved by web agencies — they lack the budget for custom builds and the technical literacy to evaluate proposals. Prospekt automates the full top-of-funnel for a web design agency: it discovers local businesses via Google Places, scores their existing web presence using a multimodal Claude vision assessment, builds a personalised demo landing page, deploys it to a public URL, and sends a cold outreach email — all without human involvement until a curated approval step in Google Sheets. Interested replies are classified by Claude and escalated to Slack in real time.

## Technical Design

### The human-in-the-loop approval gate

The most consequential design decision in this system is where to place human oversight and what form it should take.

An end-to-end fully automated pipeline is technically possible but practically unacceptable: sending cold emails to unvetted targets at scale invites spam complaints, wastes resources building pages for businesses that are already well-served, and removes all quality control from outreach copy. The alternative extreme — pausing and awaiting manual review between every stage — destroys throughput.

The chosen design inserts a single approval gate at the point of highest leverage: after discovery and scoring, before any content is generated or any email is sent. Discovered businesses are written to a named Google Sheets tab (keyed by job ID), where an operator marks each row `Approve` or `Reject` in a dedicated column. The pipeline holds at `awaiting_batch_approval` and polls the sheet on a 2-minute interval for up to 24 hours. Only approved rows proceed to page generation, deployment, and outreach.

Google Sheets was chosen deliberately over a custom admin UI. It requires no additional authentication surface, no frontend code to maintain, supports inline notes and sorting, and is already the tool operators use for CRM-adjacent work. The tradeoff is that the polling approach introduces latency (up to 2 minutes between approval and pipeline resumption) and has no push notification when the operator is done — both acceptable in a workflow that is already human-paced.

A second approval gate exists at the page review stage (`awaiting_page_approval`), following the same polling pattern. This allows the generated HTML to be previewed via the `/pipeline/preview/{business_id}` endpoint before deployment proceeds.

### Scoring via multimodal Claude

Rather than using heuristics (PageSpeed scores, mobile viewport tags, DOM analysis), the scorer captures a viewport screenshot via headless Chromium using Playwright, compresses it to a JPEG at 60% quality capped at 1280×800, and sends it to `claude-sonnet-4-6` with a structured prompt requesting a 0–100 JSON score and plain-text reason. This approach evaluates the visual and structural quality a human would perceive — which is exactly what the sales pitch is based on — rather than technical metrics the prospect is unlikely to understand. The cost of a single scoring call is negligible relative to the downstream outreach effort.

### Asynchronous pipeline execution

The FastAPI endpoint at `POST /pipeline/run` accepts a job request and immediately returns a job ID. The full pipeline runs as a FastAPI `BackgroundTask`, freeing the HTTP connection. All blocking operations — Supabase writes, Google Sheets sync, and the gspread poller — are dispatched via `asyncio.to_thread` to avoid blocking the event loop. This means a single process can hold multiple concurrent jobs in their approval-waiting state without thread exhaustion.

## Architecture

```
POST /pipeline/run
        |
        v
  Orchestrator (background task)
        |
        +-- Discovery       Google Places Text Search + Details API
        |                   -> BusinessCreate list
        |
        +-- Scoring         Playwright screenshot -> Claude vision -> 0-100 score
        |                   (per business with website)
        |
        +-- Context scrape  Claude Haiku inference from business metadata
        |                   -> structured context dict (tagline, services, tone, colour)
        |
        +-- Supabase save   businesses table insert
        |
        +-- Sheets sync     gspread writes job-keyed worksheet
        |                   approval_status column left blank for operator
        |
        +-- Approval poll   2-min interval, up to 24h
        |   (awaiting_batch_approval)
        |
        +-- Email discovery Hunter.io domain search -> info@ fallback
        |
        +-- Page generation Claude Haiku copywriting -> HTML template fill
        |                   demo_html saved to Supabase
        |
        +-- Page approval   preview endpoint + Sheets poll
        |   (awaiting_page_approval)
        |
        +-- Deployment      Vercel API v13 -> poll readyState -> disable SSO
        |                   demo_url saved to Supabase + Sheets
        |
        +-- Outreach        Claude Haiku cold email copy -> Gmail API send
        |
        +-- Monitor         Gmail reply search -> Claude classification
                            interested -> Slack webhook alert
```

**Data stores:**
- `jobs` table — pipeline run state and counters
- `businesses` table — full business record including demo HTML, email tracking, campaign status, and opt-out flag

## Tech Stack

- **Python 3.12** with `asyncio`
- **FastAPI** — HTTP API and webhook receiver
- **Anthropic Claude** — `claude-sonnet-4-6` for visual scoring; `claude-haiku-4-5` for context inference, copywriting, and reply classification
- **Playwright** — headless Chromium for website screenshots
- **Supabase** — PostgreSQL-backed persistence via the Python client
- **Google Places API** — business discovery (Text Search + Details)
- **gspread** — Google Sheets read/write for the approval workflow
- **Gmail API** — outbound email via OAuth 2.0 credentials
- **Hunter.io** — contact email discovery by domain
- **Vercel API v13** — static HTML deployment with readyState polling
- **Slack Webhooks** — pipeline status notifications and lead escalation alerts
- **Pydantic v2 + pydantic-settings** — request/response validation and typed settings
- **httpx** — async HTTP client for all external API calls
- **Pillow** — screenshot compression before Claude vision upload
- **uvicorn** — ASGI server; deployed to Railway via `nixpacks.toml`

## Key Features

- Pipeline is fully non-blocking: each job runs as a FastAPI background task; the caller receives a job ID immediately
- Approval gate uses a long-poll loop (120s interval, 288 max attempts = 24h window) against a live Google Sheet, requiring no webhook infrastructure on the operator side
- Claude visual scorer uses a viewport-constrained JPEG (1280×800, 60% quality) to cap token cost while preserving enough fidelity for design quality assessment
- Context inference falls back through three retry attempts with 2-second backoff before degrading to a minimal context object derived from business metadata alone
- Email copy post-processes Claude output to strip any placeholder syntax (`{{FIRST_NAME}}`, `{{BUSINESS_NAME}}`, etc.) that leaks through, before sending
- Vercel deployer polls `readyState` up to 10 times with 3-second intervals and disables SSO/password protection on the project immediately after `READY`
- Unsubscribe requests received via webhook set `opted_out: true` on the business record
- Slack trigger webhook (`/webhooks/slack`) accepts Slack slash command form data, allowing pipeline runs to be initiated directly from a Slack channel
- All Supabase writes run through `asyncio.to_thread` to avoid blocking the event loop during I/O-bound operations
- Job status exposed with 11 discrete states (`created`, `discovering`, `scoring`, `awaiting_batch_approval`, `building`, `awaiting_page_approval`, `deploying`, `outreaching`, `monitoring`, `completed`, `failed`)

## Getting Started

### Prerequisites

- Python 3.12
- A Supabase project with `jobs` and `businesses` tables
- Google Cloud project with Places API and Sheets API enabled; a service account with the credentials JSON
- A Gmail OAuth 2.0 client (credentials + refresh token stored as JSON strings in env)
- Vercel account with an API token
- Slack app with an incoming webhook URL

### Local setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/prospekt.git
   cd prospekt
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the Playwright browser:
   ```bash
   playwright install chromium --with-deps
   ```

5. Copy the example environment file and populate it:
   ```bash
   cp .env.example .env
   ```

6. Start the server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

The API will be available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

### Environment variables

| Variable | Description | Example |
|---|---|---|
| `SUPABASE_URL` | Supabase project URL | `https://xxxx.supabase.co` |
| `SUPABASE_KEY` | Supabase service role key | `eyJ...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |
| `GOOGLE_PLACES_API_KEY` | Google Places API key | `AIza...` |
| `GOOGLE_SHEETS_ID` | ID of the target Google Sheet | `1BxiM...` |
| `GOOGLE_CREDENTIALS_PATH` | Local path to service account JSON | `credentials.json` |
| `GOOGLE_CREDENTIALS_JSON` | Full service account JSON as a string (used in production) | `{"type":"service_account",...}` |
| `GMAIL_CREDENTIALS_PATH` | Local path to Gmail OAuth2 client secrets | `gmail_credentials.json` |
| `GMAIL_TOKEN_JSON` | Serialised Gmail OAuth2 token (access + refresh) as a string | `{"token":"...","refresh_token":"..."}` |
| `GMAIL_FROM_EMAIL` | Sender address for outreach emails | `you@example.com` |
| `VERCEL_API_TOKEN` | Vercel personal access token | `abc123...` |
| `VERCEL_TEAM_ID` | Vercel team ID (optional, for team accounts) | `team_xyz` |
| `HUNTER_API_KEY` | Hunter.io API key (optional; falls back to `info@domain` if absent) | `abc123...` |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | `https://hooks.slack.com/services/...` |
| `APP_ENV` | Runtime environment | `development` |
| `APP_HOST` | Bind host | `0.0.0.0` |
| `APP_PORT` | Bind port | `8000` |

## API Reference

### Health check

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Returns service name and version |

**Response:**
```json
{"status": "ok", "app": "Prospekt", "version": "1.0.0"}
```

---

### Pipeline

| Method | Path | Description |
|---|---|---|
| `POST` | `/pipeline/run` | Start a pipeline run for a location and category |
| `GET` | `/pipeline/status/{job_id}` | Get the current state of a job |
| `GET` | `/pipeline/jobs` | List up to 50 recent jobs, optionally filtered by status |
| `GET` | `/pipeline/preview/{business_id}` | Render the generated demo HTML for a business |
| `POST` | `/pipeline/cancel/{job_id}` | Cancel a running job |

**POST `/pipeline/run` — request body:**
```json
{
  "location": "Brixton, London",
  "category": "barbershops"
}
```

**POST `/pipeline/run` — response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "created",
  "message": "Pipeline started"
}
```

**GET `/pipeline/status/{job_id}` — response fields:**

| Field | Type | Description |
|---|---|---|
| `job_id` | UUID | Unique job identifier |
| `status` | string | Current pipeline stage |
| `businesses_found` | int | Total businesses discovered |
| `businesses_approved` | int | Businesses approved in Sheets |
| `businesses_rejected` | int | Businesses rejected in Sheets |
| `pages_built` | int | Demo pages generated |
| `pages_approved` | int | Pages approved for deployment |
| `emails_sent` | int | Outreach emails dispatched |
| `replies_received` | int | Replies detected via Gmail |
| `leads_escalated` | int | Replies classified as interested |
| `error_message` | string or null | Set on `failed` status |

---

### Webhooks

| Method | Path | Description |
|---|---|---|
| `POST` | `/webhooks/reply` | Inbound email reply handler (form-encoded) |
| `POST` | `/webhooks/slack` | Slack slash command trigger |
| `POST` | `/webhooks/unsubscribe` | Mark a business contact as opted out |

**POST `/webhooks/reply` — form fields:**

| Field | Description |
|---|---|
| `from` | Sender email address |
| `subject` | Email subject line |
| `text` | Plain text body |

**POST `/webhooks/slack` — form fields (Slack slash command payload):**

| Field | Description |
|---|---|
| `text` | Command text, parsed as `[location] [category]` |
| `user_name` | Slack username of the requester |

**POST `/webhooks/unsubscribe` — request body:**
```json
{"email": "contact@example.com"}
```

## Running Tests

```bash
python -m pytest test_discovery.py test_scorer.py test_scraper.py test_generator.py test_deployer.py test_outreach.py test_monitor.py test_orchestrator.py test_sheets.py -v
```

Individual module tests can be run directly as scripts:

```bash
python test_orchestrator.py
python test_scorer.py
```

## Project Status

In active development. Core pipeline stages are functional end-to-end. Approval polling and Gmail OAuth flow are production-tested; multi-sequence follow-up emails (emails 2 and 3) are scaffolded in the data model but not yet implemented in the outreach stage.

## License

See [LICENSE](LICENSE).
