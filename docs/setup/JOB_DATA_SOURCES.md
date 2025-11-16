# Job Data Sources & Web Scraping (Local-Only)

This guide explains how to run Career Copilot entirely on localhost, pick job data providers that actually issue developer credentials, and enable the built-in ScraperManager so you can collect jobs even without LinkedIn/Indeed/GitHub partnerships.

---

## 1. Local infrastructure checklist

You can stay 100% local—no cloud accounts required—by running the stack exactly like in development:

1. **Start dependencies** (Docker recommended):
   ```bash
   docker compose up -d postgres redis chroma
   ```
2. **Apply database migrations** (first run only):
   ```bash
   cd backend && alembic upgrade head
   ```
3. **Launch backend & workers** (new terminal tabs, or use `make dev-setup`):
   ```bash
   cd backend && uvicorn app.main:app --reload --port 8002
   cd backend && celery -A app.core.celery_app worker --loglevel=info --concurrency=2
   cd backend && celery -A app.core.celery_app beat --loglevel=info
   ```
4. **Launch the frontend** (optional for scraping tests, required for UI):
   ```bash
   cd frontend && npm run dev
   ```

> **Tip:** If you do not want Celery automation, you can still trigger scraping manually via the API (`POST /api/v1/jobs/scrape`) or by calling `JobManagementSystem.scrape_jobs` inside a shell.

---

## 2. API-based providers that actually issue credentials

You dont need official LinkedIn/Indeed/GitHub partnerships. The stack already supports (or can easily be extended with) APIs that hand out keys to individual developers:

| Provider | Base Endpoint | How to get access | Built-in status | Notes |
| --- | --- | --- | --- | --- |
| **Adzuna** | `https://api.adzuna.com/v1/api/jobs/{country}/search/1` | Create a free account at [developer.adzuna.com](https://developer.adzuna.com/) for `ADZUNA_APP_ID` / `ADZUNA_APP_KEY`. | ✅ Native (`JobManagementSystem._scrape_adzuna`) | Excellent EU coverage, personal keys OK.<br>Set `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` in `backend/.env`. |
| **RapidAPI JSearch** | `https://jsearch.p.rapidapi.com/search` | Subscribe to the JSearch API via [RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO/api/jsearch). | ✅ Native (`RapidAPIJSearchScraper`) | Aggregates LinkedIn/Indeed/Glassdoor legally.<br>Expose `RAPIDAPI_JSEARCH_KEY`. |
| **The Muse** | `https://www.themuse.com/api/public/jobs` | Optional key from [The Muse developer portal](https://www.themuse.com/developers/api/v2). | ✅ Native (`TheMuseScraper`) | Key increases rate limit but is not mandatory; configure `THEMUSE_API_KEY` if you have it. |
| **USAJOBS** | `https://data.usajobs.gov/api/search` | Register at [developer.usajobs.gov](https://developer.usajobs.gov/) to receive a `User-Agent` + API key. | ⚠️ Partial (legacy REST helper) | Add a custom scraper or extend `JobManagementSystem.apis["usajobs"]` to include your credentials. |
| **Jooble** | `https://jooble.org/api/{API_KEY}` | Claim a free dev key at [jooble.org/api/about](https://jooble.org/api/about). | 🛠️ DIY (use `BaseScraper`) | Simple JSON API; easiest new provider to add if you want more data. |
| **Landing.jobs** | `https://landing.jobs/feed` | Public RSS feed, no auth. | ✅ Native (`LandingJobsScraper`) | Filters for EU relocation + visa-friendly postings, skips remote-only listings. |
| **EU Tech Jobs** | `https://eutechjobs.com/feed` | Public RSS feed, no auth. | ✅ Native (`EUTechJobsScraper`) | EU-only feed with relocation notes; tuned for on-site hires. |
| **EuroTechJobs** | `https://www.eurotechjobs.com/jobs/machine-learning.rss` | Public RSS feed, no auth. | ✅ Native (`EuroTechJobsScraper`) | Focused on continental ML/AI roles with relocation info. |
| **AI Jobs (ai-jobs.net)** | `https://ai-jobs.net/rss` | Public RSS feed, no auth. | ✅ Native (`AIJobsNetScraper`) | Filters for EU cities + DS/ML keywords, skips remote-only listings. |
| **DataCareer.eu** | `https://www.datacareer.eu/jobs?format=rss` | Public RSS feed, no auth. | ✅ Native (`DataCareerScraper`) | Curated onsite data roles across DACH + broader EU. |
| **EU company career pages** | `playwright://eu-company-careers` | No API—uses local Playwright browser. | ✅ Native (`EUCompanyPlaywrightScraper`) | Scans curated sponsors (Spotify, Adyen, Wise, etc.). Requires `playwright install chromium`. |
| **Firecrawl** | `https://api.firecrawl.dev/v2` | Request a key at [firecrawl.dev](https://www.firecrawl.dev/). | ✅ Native (`FirecrawlScraper`) | Handles JS-heavy career pages (Google, DeepMind, Stripe, etc.). Set `FIRECRAWL_API_KEY`. |

Additional European-friendly feeds (Arbeitnow, BerlinStartupJobs, Relocate.me, EURES) are already wired into `ScraperManager` and do **not** need credentials.

---

## 3. Configure the built-in ScraperManager

1. Copy the new environment block from `backend/.env.example` and adjust values:
   ```env
   # scraper toggles
   SCRAPING_MAX_RESULTS_PER_SITE=50
   SCRAPING_MAX_CONCURRENT=3
   SCRAPING_ENABLE_ARBEITNOW=true
   SCRAPING_ENABLE_BERLINSTARTUPJOBS=true
   SCRAPING_ENABLE_RELOCATEME=true
   SCRAPING_ENABLE_EURES=true
   SCRAPING_ENABLE_LANDINGJOBS=true
   SCRAPING_ENABLE_EUTECHJOBS=true
   SCRAPING_ENABLE_EUROTECHJOBS=true
   SCRAPING_ENABLE_AIJOBSNET=true
   SCRAPING_ENABLE_DATACAREER=true
   SCRAPING_ENABLE_FIRECRAWL=true
   SCRAPING_ENABLE_EU_PLAYWRIGHT=false # toggle on after installing Playwright browsers

   # API keys
   RAPIDAPI_JSEARCH_KEY=...
   ADZUNA_APP_ID=...
   ADZUNA_APP_KEY=...
   THEMUSE_API_KEY=...
   FIRECRAWL_API_KEY=...
   ```
2. Restart the backend (settings are loaded at process start).
3. Verify available scrapers by running the test helper:
   ```bash
   cd backend && poetry run python scripts/testing/test_new_scrapers.py
   ```
   The script prints a PASS/FAIL matrix, so you immediately know whether each provider is reachable with your keys.

### Playwright (headless Chromium) setup

Install the browser runtime once per machine:

```bash
cd backend && playwright install chromium
```

This powers the `EUCompanyPlaywrightScraper`, which opens curated EU sponsor sites (Spotify, Adyen, Wise, N26, etc.), extracts onsite engineering roles, and ignores remote-only postings. Keep the toggle off unless you need these listings—headless Chromium launches add a few seconds to each scrape.

The ScraperManager combines:
- **API scrapers:** Adzuna, RapidAPI JSearch, The Muse.
- **Public/OSS feeds:** Arbeitnow, BerlinStartupJobs, Relocate.me, EURES, Landing.jobs, EU Tech Jobs.
- **Headless/browser scrapers:** Playwright (Spotify/Adyen/etc.) and Firecrawl for heavier JS career portals.

Everything goes through `JobManagementSystem.scrape_jobs`, which normalizes data, deduplicates, and stores jobs.

---

## 4. Triggering job collection

### Manual API call
1. Ensure backend, Celery worker, and Redis are running.
2. `POST /api/v1/jobs/scrape` with a JSON body such as:
   ```json
   {
     "skills": ["data science", "python"],
       "locations": ["Berlin", "Munich"],
     "max_jobs": 100
   }
   ```
3. Watch the worker logs; ingested jobs appear under your test user.

### Scheduled automation
1. Flip the flags:
   ```env
   ENABLE_JOB_SCRAPING=true
   ENABLE_SCHEDULER=true
   ```
2. Keep `celery beat` running. The default schedule (see `app/tasks/scheduled_tasks.py`) scrapes each morning, deduplicates, and pushes notifications.

---

## 5. Extending with new APIs

To integrate another friendly provider:
1. Create a scraper in `backend/app/services/scraping/your_scraper.py` by subclassing `BaseScraper` (see `RemotiveScraper` example in the docs below).
2. Add a toggle to `ScraperManager` and to `.env` (pattern already in place for Firecrawl/Arbeitnow/EURES).
3. Declare required credentials in `UnifiedSettings` so they load via env vars.
4. Add a short integration test (copy `backend/tests/integration/test_job_scraper_integration.py`).

For providers that expose RSS feeds (Remotive, EU Tech Jobs, Landing.jobs), you can also use `RSSFeedService` without writing a scraper—just add the feed URL to `config/application.yaml`.

---

## 6. Troubleshooting

- **403/401 errors**: usually missing/incorrect API key headers. Double-check casing of env vars, then restart the backend.
- **Empty responses**: make sure your search keywords include EU-friendly roles (`data scientist`, `backend engineer`). Many APIs default to US markets.
- **Celery not running**: job scraping tasks queue but never start. Confirm `celery -A app.core.celery_app worker` is in a live terminal.
- **Deduplication removing everything**: lower the similarity threshold temporarily via `JOB_DEDUP_THRESHOLD` in the settings or reduce the number of overlapping feeds.

By combining the credential-friendly APIs above with the ScraperManager, you can build a rich job feed on localhost without any proprietary partnerships.
