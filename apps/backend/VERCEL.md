# Deploying the backend on Vercel (serverless)

The same FastAPI app in this directory runs on both Render (long-lived uvicorn)
and Vercel Functions (native Python runtime). Render remains the primary backend
until you decide to cut over; this deployment is independent.

## Import the project

1. In Vercel: **Add New → Project** and import
   `pasha01118/Advanced-Code-Garage`.
2. Set **Root Directory** to `apps/backend`. This is the key setting — it puts
   `requirements.txt`, `app/main.py`, `.python-version` and `vercel.json` at the
   project root.
3. Framework preset: FastAPI (auto-detected). Leave Build Command and Output
   Directory empty; Vercel installs `requirements.txt` and loads `app:app` from
   `app/main.py`.
4. Add the environment variables below, then deploy.

`.python-version` pins Python 3.12, which Vercel supports. `vercel.json` keeps
the bundle small by excluding tests, SQL and dev files.

## Environment variables

Copy these from the Render service (same names, same values):

| Variable | Notes |
| --- | --- |
| `SUPABASE_URL` | `https://sdmvjjvvzbwnccwaeomh.supabase.co` |
| `SUPABASE_ANON_KEY` | (or `SUPABASE_PUBLISHABLE_KEY`) |
| `SUPABASE_SERVICE_ROLE_KEY` | required — service-role bypasses RLS |
| `SECRET_KEY` | generate a fresh one for this project |
| `USER_KEY_ENCRYPTION_KEY` | |
| `APP_BOOTSTRAP_TOKEN` | |
| `ADMIN_RESET_TOKEN` | |
| `ADMIN_USER_IDS` | |
| `GOOGLE_AI_STUDIO_KEY` | |
| `GOOGLE_AI_STUDIO_PROXY` | |
| `GOOGLE_AI_STUDIO_PROXY_TOKEN` | |
| `OLLAMA_BASE_URL` | keep `http://localhost:11434` unless using a remote host |
| `FRONTEND_URLS` | include the deployed frontend origin |
| `ENVIRONMENT` | `production` |
| `SENTINEL_INTERVAL_SECONDS` | informational on serverless |
| `CRON_SECRET` | new random secret; Vercel Cron sends it as `Authorization: Bearer …` |
| `GITHUB_APP_ID` | numeric GitHub App ID |
| `GITHUB_APP_SLUG` | App URL slug (informational) |
| `GITHUB_APP_PRIVATE_KEY` | PEM private key; literal `\n` escapes are accepted |
| `GITHUB_APP_WEBHOOK_SECRET` | used to verify `X-Hub-Signature-256` |
| `VAULT_KEK_VERSION` | current repository-secrets key version, e.g. `v1` |
| `VAULT_PREVIOUS_KEKS` | `v1:<old-secret>,…` while rotating a KEK |
| `GITHUB_API_BASE_URL` | `https://api.github.com`, or your GitHub Enterprise `/api/v3` URL |

`USER_KEY_ENCRYPTION_KEY` should be a dedicated 32+ character secret in
production. It protects both AI provider keys and repository secrets; never
reuse a placeholder value.

`VERCEL=1` is set automatically by the platform and must not be added manually.

## GitHub App setup

1. Create a GitHub App with **Contents: Read & write**, **Pull requests:
   Read & write**, **Metadata: Read-only**, and **Webhooks** enabled.
2. Subscribe to `installation`, `installation_repositories`, `repository`,
   and `push` events.
3. Set the webhook URL to the deployed backend:
   `https://agc-backend-ix19.onrender.com/api/v1/github/webhook` while Render is
   primary. Copy the webhook secret into `GITHUB_APP_WEBHOOK_SECRET`.
4. Generate a private key, store its PEM text in `GITHUB_APP_PRIVATE_KEY`, and
   set `GITHUB_APP_ID`. Literal `\n` escapes in the PEM are accepted.
5. Install the App on the target account/organization. The first webhook
   registers the installation; an admin can then call
   `POST /api/v1/github/installations/{id}/sync` (or use **Repositories → Sync**
   in the dashboard).
6. Apply `sql/0006_github_vault.sql` and `sql/0007_repo_ops.sql` before using
   repositories, the secrets vault, or Git operations.
7. An admin must call `POST /api/v1/github/installations/{id}/sync` after
   installing the App. Sync grants the acting admin `owner` on the discovered
   repositories; other users need an explicit role from
   `POST /api/v1/repositories/{id}/permissions`.

Repository file, branch, PR, diff and customization endpoints use the GitHub
REST API with short-lived installation tokens. Requests are bounded and finish
within a single function invocation, so they work on both Render and Vercel.
Long-running background pipelines should stay on a Render worker.

No personal access token is stored. Installation tokens are minted on demand
from the App private key and are never sent to the browser.

## What changes on serverless

- **Sentinel loop:** the in-process 60-second loop is disabled. `vercel.json`
  schedules `GET /api/cron/sentinel` daily (Vercel Cron on Hobby is daily at
  most). On Pro/Enterprise you can use a finer schedule, e.g.
  `"*/5 * * * *"`. The endpoint returns 503 until `CRON_SECRET` is set.
- **Project pipelines:** instead of a detached background task, project
  creation awaits the pipeline before responding, so a finished project is
  never lost when the invocation ends.
- **SSE streams:** `/api/v1/logs/stream` and `/api/v1/admin/sentinel/stream`
  are capped by `maxDuration` (300s). The frontend already reconnects with
  backoff, so a dropped stream is transparent to users.
- **Per-instance state:** rate-limit buckets, JWKS/model caches and the in-process
  event buses live in one function instance. Rate limiting is best-effort, and
  live log events are only seen by streams on the same instance.
- **Migrations:** still manual. Apply `sql/*.sql` with
  `scripts/apply_migrations.py` against your database; nothing runs them at
  startup on either platform. `0006_github_vault.sql` creates the GitHub App
  and encrypted-secrets tables.

## Verify

```bash
curl https://<your-project>.vercel.app/health
curl https://<your-project>.vercel.app/openapi.json   # 44 paths
```

Vercel Web Analytics for this project is enabled in the Vercel dashboard
(**Analytics** tab) — no npm package is needed. `@vercel/analytics` is already
installed in `apps/frontend`, which is where browser-side tracking belongs.
