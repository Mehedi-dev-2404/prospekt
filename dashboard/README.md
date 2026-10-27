# Prospekt Dashboard

Ops dashboard for the Prospekt pipeline (Next.js App Router, deployed on Vercel, backed by Supabase).

## What it does

- **Jobs** (`/jobs`, `/jobs/[jobId]`): review pipeline runs and the businesses each one discovered.
- **Businesses** (`/businesses`): all discovered businesses; approve or reject them for outreach.
- **Demo pages**: approve generated demo pages before they are used in outreach.
- **Campaign tracker**: follow outreach status per business.
- **Run** (`/run`): trigger a new pipeline run (location + optional category) via the backend.

The Python orchestrator polls Supabase for `approval_status` and `demo_approved`, so decisions made here unblock the pipeline.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase key used server-side |
| `BACKEND_URL` | Base URL of the Prospekt FastAPI backend (`POST /pipeline/run`) |
| `DASHBOARD_PASSWORD` | Password for the login page |
| `SESSION_SECRET` | HMAC secret used to sign the session cookie |

## Development

```bash
npm install
npm run dev     # http://localhost:3000
npm run lint
npx tsc --noEmit
```

## Deployment

Deployed to Vercel as `prospekt-dashboard`. Set the variables above in the Vercel project, then `vercel --prod`.

Auth is a single shared password; unauthenticated requests are redirected to `/login` by `middleware.ts`.
