# API Reference

Career Copilot exposes a FastAPI-based `/api/v1` surface backed by PostgreSQL, Redis, Celery workers, and multi-provider LLM integrations. This document summarizes the major route groups, conventions, and supporting tooling.

## Generating the OpenAPI Spec

The canonical schema is generated directly from the FastAPI application and stored alongside the frontend for typed API clients.

```bash
python scripts/generate_openapi_docs.py   # Writes frontend/openapi.json
```

Import `frontend/openapi.json` into Postman, Stoplight, or Spectral for contract testing, or serve it via `npx openapi-format frontend/openapi.json --html` for a browsable reference.

## Authentication & Users (`backend/app/api/v1/auth.py`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/register` | Create a credentialed user account and return a JWT access token. |
| `POST` | `/api/v1/auth/login` | Exchange username/email + password for a short-lived JWT. |
| `POST` | `/api/v1/auth/logout` | Stateless acknowledgement used by the frontend to clear local tokens. |
| `GET`  | `/api/v1/auth/me` | Fetch the authenticated user resolved by `get_current_user`. |
| `GET`  | `/api/v1/auth/oauth/google/login` | Redirect to Google OAuth consent. |
| `GET`  | `/api/v1/auth/oauth/google/callback` | Handle OAuth callback, mint tokens, and link accounts. |

Tokens are validated by `decode_access_token`; admin-only routes depend on `get_admin_user` which enforces `User.is_admin` unless `DISABLE_AUTH=true` for dev environments.

## Jobs & Market Data (`backend/app/api/v1/jobs.py`, `market.py`, `linkedin_jobs.py`)

| Method | Path | Highlights |
|--------|------|------------|
| `GET`  | `/api/v1/jobs` | Paginated list of tracked jobs (newest first) scoped to the authenticated user. |
| `POST` | `/api/v1/jobs` | Create/import a job with metadata (title, company, salary, remote option, tech stack, etc.). |
| `GET`  | `/api/v1/jobs/{job_id}` | Fetch a single job with full description + derived previews. |
| `PATCH`| `/api/v1/jobs/{job_id}` | Update any mutable fields (status, salary bands, notes, application URL). |
| `DELETE`| `/api/v1/jobs/{job_id}` | Permanently remove a job. |
| `GET`  | `/api/v1/jobs/search` | Advanced filters (location, salary, tech stack, remote only) with cache-backed responses. |
| `GET`  | `/api/v1/jobs/recommendations` | Quick recommendation algorithm that blends saved jobs with skill overlap scoring. |
| `GET`  | `/api/v1/jobs/insights` | Aggregated stats for dashboards (counts by status, salary histograms, etc.). |

Supplementary routers (`market`, `linkedin_jobs`) surface curated market snapshots and third-party job feeds for ingestion pipelines.

## Applications & Pipelines (`backend/app/api/v1/applications.py`, `bulk_operations.py`, `import_data.py`, `export.py`)

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/v1/applications` | List applications with status filters, sort options, pagination, and Kanban metadata. |
| `POST` | `/api/v1/applications` | Create a new application attached to an existing job or ad-hoc entry. |
| `PATCH`| `/api/v1/applications/{application_id}` | Update status, interviews, feedback, or attachments. |
| `DELETE`| `/api/v1/applications/{application_id}` | Delete an application (soft-delete if enabled). |
| `POST` | `/api/v1/applications/{application_id}/status` | Shortcut endpoint for status transitions (used by bulk actions + timeline UI). |
| `POST` | `/api/v1/bulk_operations/applications/status` | Batch update statuses for multiple IDs. |
| `POST` | `/api/v1/import/applications` | CSV/JSON ingestion with validation + deduplication. |
| `GET`  | `/api/v1/export/applications.{csv|xlsx|pdf}` | Export filtered applications for reporting. |

## Recommendations, AI Content & Resume Tools (`backend/app/api/v1/recommendations.py`, `enhanced_recommendations.py`, `resume.py`)

- `GET /api/v1/recommendations/jobs` – Personalized job matches with `match_score`, remote flag, and tech stack details.
- `GET /api/v1/recommendations/skills-gap` – Computes skill coverage vs. top market skills; powers the Skill Gap Analysis tab.
- `POST /api/v1/resume/upload` – Accepts PDF/DOCX resumes, launches async parsing, and returns `upload_id` + parsing status.
- `GET /api/v1/resume/{upload_id}/status` – Poll endpoint used by the Resume Upload UI to surface extraction progress + profile suggestions.
- `POST /api/v1/content/generate` (see service wiring) – Multi-mode generator that supports `cover_letter`, `resume_tailoring`, and `email_template` categories with prompt/tone controls.
- `POST /api/v1/enhanced-recommendations/run` – Triggers deeper AI workflows (semantic matching, multi-source ranking) via Celery tasks.

All AI-facing routes invoke `LLMService`, which picks a provider based on `task_category` (analysis, generation, comparison) and respects rate limits defined in `config/llm_config.json`.

## Notifications & Collaboration (`backend/app/api/v1/notifications.py`, `websocket_notifications.py`, `social.py`)

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/v1/notifications` | Fetch paginated notification feed with read/unread state. |
| `POST` | `/api/v1/notifications/mark-read` | Batch mark IDs as read. |
| `GET`  | `/api/v1/notifications/settings` | Retrieve push/email preferences. |
| `PATCH`| `/api/v1/notifications/settings` | Update categories, quiet hours, and channels. |
| `GET`  | `/api/v1/notifications/socket-token` | Mint a short-lived token for the websocket notification channel (`/api/v1/ws/notifications`). |
| `GET`  | `/api/v1/social/activity` | Activity feeds, shared resumes/jobs, leaderboard stats. |

## System Health & Operations (`backend/app/api/v1/health.py`, `job_ingestion.py`, `feedback.py`, `help_articles.py`)

- `GET /health` – Readiness probe (database + Redis ping).
- `GET /api/v1/job-ingestion/status` – Surface Celery job ingestion metrics and queue depth.
- `POST /api/v1/job-ingestion/run` – Kick off targeted scrapers (LinkedIn, LandingJobs, EU Tech boards, etc.).
- `POST /api/v1/feedback` – Accepts in-product feedback with optional screenshot references.
- `GET /api/v1/help-articles` – CMS-driven help content consumed by the in-app Help Center.

## Error Codes & Conventions

- Errors follow FastAPI’s `{ "detail": "message" }` structure unless a richer schema is specified.
- Validation failures emit the standard `422` payload (`detail` array with `loc`, `msg`, `type`).
- Auth failures respond with `401` + `WWW-Authenticate: Bearer`; RBAC violations surface `403` and `"Admin access required"`.
- Long-running tasks (scraping, AI pipelines) return `202 Accepted` with `task_id` tracked in Celery/Redis.

## Versioning & Stability

- All production routes reside under `/api/v1`. Introduce `/api/v2` for breaking changes and keep `/api/v1` backward compatible until decommissioned.
- Schema evolution is managed via Alembic migrations; keep Pydantic response models in sync.
- Websocket contracts are defined in `backend/app/api/websockets.py` and mirrored by the frontend `RealtimeProvider`.

For the most accurate view, regenerate `frontend/openapi.json` and explore it via your preferred OpenAPI viewer.
