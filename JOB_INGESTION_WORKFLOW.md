# Job Ingestion and Deduplication Workflow

## Overview

The Career Copilot system implements a sophisticated job ingestion pipeline that:
1. **Scrapes jobs** from multiple sources (APIs, RSS feeds, web scrapers)
2. **Deduplicates** jobs using advanced matching algorithms
3. **Stores unique jobs** in PostgreSQL with fingerprint indexing
4. **Prevents duplicate storage** across users and time periods

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    JOB SOURCES                               │
├──────────────────┬──────────────────┬───────────────────────┤
│   EU Scrapers    │    Job APIs      │     RSS Feeds         │
│  - RapidAPI      │  - Adzuna        │  - RemoteOK           │
│  - The Muse      │  - GitHub Issues │  - Stack Overflow     │
│  - Firecrawl     │  - USAJobs       │  - WeWorkRemotely     │
│  - Adzuna        │                  │                        │
│  - Arbeitnow     │                  │                        │
└──────────────────┴──────────────────┴───────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           JobScrapingService (Aggregation)                   │
│  - Collects jobs from all sources                            │
│  - Normalizes job data to common format                      │
│  - Returns List[Dict[str, Any]]                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│      JobDeduplicationService (Uniqueness Check)              │
│                                                               │
│  Strategy 1: URL Matching                                    │
│   - Normalize URLs (remove query params, fragments)          │
│   - Exact match on normalized URLs                           │
│                                                               │
│  Strategy 2: Fingerprint Matching                            │
│   - Create MD5 hash of normalized title+company+location     │
│   - Exact match on fingerprints                              │
│                                                               │
│  Strategy 3: Fuzzy Matching (optional)                       │
│   - Calculate similarity ratios for title/company            │
│   - Match if company ≥ 0.8 AND title ≥ 0.85                  │
│                                                               │
│  Returns: (unique_jobs, deduplication_stats)                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            Database Storage (PostgreSQL)                     │
│                                                               │
│  jobs table:                                                  │
│   - id (primary key)                                          │
│   - user_id (indexed)                                         │
│   - title, company, location                                  │
│   - job_fingerprint (MD5 hash, indexed)                       │
│   - application_url (indexed)                                 │
│   - created_at (indexed)                                      │
│                                                               │
│  Composite Index:                                             │
│   ix_jobs_user_company_title_location                        │
│   (user_id, company, title, location)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Deduplication Strategies

### 1. **URL-Based Deduplication** (Highest Priority)
- **Most reliable** method
- Normalizes URLs to remove query params and fragments
- Example:
  ```python
  "https://example.com/job/123?ref=abc" → "example.com/job/123"
  "https://example.com/job/123#apply" → "example.com/job/123"
  ```
- If normalized URLs match → **Duplicate**

### 2. **Fingerprint-Based Deduplication**
- Creates MD5 hash from normalized values
- Normalization process:
  ```python
  Company: "Google Inc." → "google"
  Title: "Senior Software Engineer (Remote)" → "senior software engineer"
  Location: "San Francisco, CA" → "san francisco ca"
  
  Fingerprint = MD5(company + title + location)
  ```
- Same fingerprint → **Duplicate**

### 3. **Fuzzy Matching** (Optional, enabled by default)
- Uses similarity ratios (0.0 to 1.0)
- Thresholds:
  - Company similarity ≥ 0.8
  - Title similarity ≥ 0.85
  - Location similarity considered for edge cases
- Example:
  ```python
  Job 1: "Senior Software Engineer" at "Google Inc."
  Job 2: "Software Engineer" at "Google"
  
  Company similarity: 0.92 ✓
  Title similarity: 0.88 ✓
  → Duplicate!
  ```

### 4. **Strict Mode**
- Disables fuzzy matching
- Only uses URL and fingerprint matching
- Use for high-precision requirements

---

## Normalization Rules

### Company Names
- Remove common suffixes: inc, corp, llc, ltd, limited, gmbh, ag, etc.
- Remove punctuation: commas, periods, hyphens
- Convert to lowercase
- Remove extra whitespace

**Examples:**
```
"Google Inc." → "google"
"Microsoft Corporation" → "microsoft"
"Stripe, LLC" → "stripe"
"Tech-Company, Inc." → "tech company"
```

### Job Titles
- Remove content in parentheses/brackets
- Remove special characters
- Remove noise words: remote, hybrid, urgent, apply now, etc.
- Convert to lowercase
- Remove extra whitespace

**Examples:**
```
"Senior Software Engineer (Remote)" → "senior software engineer"
"Data Scientist - ML" → "data scientist ml"
"Urgent - Backend Developer" → "backend developer"
```

### Locations
- Remove punctuation
- Convert to lowercase
- Normalize city, state format

**Examples:**
```
"San Francisco, CA" → "san francisco ca"
"Remote - USA" → "remote usa"
"New York, NY" → "new york ny"
```

---

## Workflow: Job Ingestion for User

```python
async def ingest_jobs_for_user(user_id: int, max_jobs: int = 50):
    """
    Complete job ingestion workflow with deduplication
    """
    
    # Step 1: Scrape jobs from multiple sources
    all_jobs = []
    all_jobs.extend(await scrape_from_rss_feeds())
    all_jobs.extend(await scrape_from_apis())
    all_jobs.extend(await scrape_from_web_scrapers())
    
    # Step 2: Deduplicate against existing database jobs
    unique_jobs, stats = deduplication_service.deduplicate_against_db(
        jobs=all_jobs,
        user_id=user_id,
        days_lookback=30,  # Check last 30 days
        strict_mode=False   # Enable fuzzy matching
    )
    
    # Step 3: Save unique jobs to database
    for job_data in unique_jobs:
        job = Job(**job_data, user_id=user_id)
        
        # Generate fingerprint for future deduplication
        job.job_fingerprint = create_job_fingerprint(
            job.title,
            job.company,
            job.location
        )
        
        db.add(job)
    
    db.commit()
    
    return {
        "jobs_found": len(all_jobs),
        "jobs_saved": len(unique_jobs),
        "duplicates_filtered": len(all_jobs) - len(unique_jobs)
    }
```

---

## Database Schema

### Migration: `add_job_deduplication_index`

```sql
-- Add fingerprint column
ALTER TABLE jobs 
ADD COLUMN job_fingerprint VARCHAR(32);

-- Create index on fingerprint
CREATE INDEX ix_jobs_job_fingerprint 
ON jobs(job_fingerprint);

-- Create composite index for duplicate checking
CREATE INDEX ix_jobs_user_company_title_location 
ON jobs(user_id, company, title, location);

-- Create index on application URL
CREATE INDEX ix_jobs_application_url 
ON jobs(application_url);
```

### Benefits:
1. **Fast duplicate checks** using indexed fingerprints
2. **Efficient queries** with composite index
3. **URL-based deduplication** with application_url index
4. **Historical tracking** - fingerprints persist for data analysis

---

## API Usage Examples

### Example 1: Basic Job Ingestion

```python
from app.services.job_scraping_service import JobScrapingService

scraping_service = JobScrapingService(db)

# Ingest jobs for specific user
result = await scraping_service.ingest_jobs_for_user(
    user_id=123,
    max_jobs=50
)

print(f"Found: {result['jobs_found']}")
print(f"Saved: {result['jobs_saved']}")
print(f"Filtered: {result['duplicates_filtered']}")
```

### Example 2: Manual Deduplication

```python
from app.services.job_deduplication_service import JobDeduplicationService

dedup_service = JobDeduplicationService(db)

# Check if jobs are duplicates
is_dup, reason = dedup_service.are_jobs_duplicate(
    job1_title="Senior Software Engineer",
    job1_company="Google Inc.",
    job1_location="San Francisco, CA",
    job1_url="https://careers.google.com/job/123",
    job2_title="Software Engineer",
    job2_company="Google",
    job2_location="SF",
    job2_url="https://careers.google.com/job/123",
    strict_mode=False
)

print(f"Duplicate: {is_dup}, Reason: {reason}")
# Output: Duplicate: True, Reason: duplicate_url
```

### Example 3: Bulk Database Cleanup

```python
dedup_service = JobDeduplicationService(db)

# Find and remove duplicates in existing database
results = dedup_service.bulk_deduplicate_database_jobs(
    user_id=123,  # Optional: limit to specific user
    batch_size=100
)

print(f"Total jobs: {results['total_jobs']}")
print(f"Duplicates found: {results['duplicates_found']}")
print(f"Duplicates removed: {results['duplicates_removed']}")
```

### Example 4: Filter Jobs Before Saving

```python
# New jobs from scraping
new_jobs = [
    {"title": "Software Engineer", "company": "Google", "location": "SF", "url": "..."},
    {"title": "Data Scientist", "company": "Microsoft", "location": "Seattle", "url": "..."},
    # ... more jobs
]

# Get existing jobs from DB
existing_jobs = db.query(Job).filter(Job.user_id == user_id).all()

# Filter duplicates
unique_jobs, stats = dedup_service.filter_duplicate_jobs(
    jobs=new_jobs,
    existing_jobs=existing_jobs,
    strict_mode=False
)

print(f"Unique jobs to save: {len(unique_jobs)}")
print(f"Duplicates by URL: {stats['duplicates_by_url']}")
print(f"Duplicates by fingerprint: {stats['duplicates_by_fingerprint']}")
print(f"Duplicates by fuzzy match: {stats['duplicates_by_fuzzy']}")
```

---

## Performance Optimizations

### 1. **Indexed Fingerprints**
- MD5 hashes stored in database
- Indexed for fast lookups
- Reduces duplicate checks from O(n²) to O(n)

### 2. **Composite Indexes**
```sql
ix_jobs_user_company_title_location (user_id, company, title, location)
```
- Efficient for exact match queries
- Covers most common duplicate scenarios

### 3. **Batch Processing**
```python
# Process jobs in batches
for i in range(0, len(jobs), batch_size):
    batch = jobs[i:i + batch_size]
    process_batch(batch)
```

### 4. **Days Lookback Limit**
- Only checks jobs from last N days (default: 30)
- Reduces comparison set size
- Improves query performance

### 5. **Early Exit Strategies**
```python
# Check URL first (fastest)
if url_matches:
    return True, "duplicate_url"

# Then fingerprint (fast)
if fingerprint_matches:
    return True, "duplicate_fingerprint"

# Finally fuzzy match (slower)
if fuzzy_matches:
    return True, "fuzzy_match"
```

---

## Deduplication Statistics

The service tracks detailed statistics for each deduplication run:

```python
{
    "total_input": 100,
    "duplicates_removed": 35,
    "unique_output": 65,
    "duplicates_within_batch": 10,
    "duplicates_against_db": 25,
    "duplicates_by_url": 15,
    "duplicates_by_fingerprint": 12,
    "duplicates_by_fuzzy": 8
}
```

---

## Testing

Run the comprehensive test suite:

```bash
# Test deduplication service
pytest backend/tests/unit/test_job_deduplication_service.py -v

# Test job scraping service integration
pytest backend/tests/integration/test_job_scraper_integration.py -v

# Run all job-related tests
pytest backend/tests -k "job" -v
```

---

## Migration Guide

### Apply the Migration

```bash
cd backend
alembic upgrade head
```

### Backfill Fingerprints for Existing Jobs

```python
from app.services.job_deduplication_service import JobDeduplicationService
from app.models.job import Job

dedup_service = JobDeduplicationService(db)

# Get all jobs without fingerprints
jobs = db.query(Job).filter(Job.job_fingerprint == None).all()

for job in jobs:
    job.job_fingerprint = dedup_service.create_job_fingerprint(
        job.title,
        job.company,
        job.location
    )

db.commit()
print(f"Backfilled {len(jobs)} fingerprints")
```

---

## Best Practices

### 1. **Always Use Deduplication Service**
```python
# ❌ Don't save jobs without checking
for job in scraped_jobs:
    db.add(Job(**job))

# ✅ Do filter duplicates first
unique_jobs, stats = dedup_service.deduplicate_against_db(scraped_jobs, user_id)
for job in unique_jobs:
    db.add(Job(**job))
```

### 2. **Generate Fingerprints on Save**
```python
# Always generate fingerprint when creating jobs
job = Job(**job_data)
job.job_fingerprint = dedup_service.create_job_fingerprint(
    job.title, job.company, job.location
)
db.add(job)
```

### 3. **Use Appropriate Lookback Period**
```python
# Short lookback for frequently posted jobs
dedup_service.deduplicate_against_db(jobs, user_id, days_lookback=7)

# Longer lookback for stable markets
dedup_service.deduplicate_against_db(jobs, user_id, days_lookback=90)
```

### 4. **Enable/Disable Fuzzy Matching Based on Use Case**
```python
# Strict matching for high-precision requirements
unique_jobs, stats = dedup_service.filter_duplicate_jobs(
    jobs, existing_jobs, strict_mode=True
)

# Fuzzy matching for better recall
unique_jobs, stats = dedup_service.filter_duplicate_jobs(
    jobs, existing_jobs, strict_mode=False
)
```

---

## Monitoring

Track deduplication effectiveness:

```python
# Log deduplication stats
logger.info(f"Deduplication rate: {stats['duplicates_removed'] / stats['total_input'] * 100:.1f}%")
logger.info(f"URL matches: {stats['duplicates_by_url']}")
logger.info(f"Fingerprint matches: {stats['duplicates_by_fingerprint']}")
logger.info(f"Fuzzy matches: {stats['duplicates_by_fuzzy']}")
```

---

## Summary

✅ **Multi-strategy deduplication** (URL, fingerprint, fuzzy)  
✅ **Advanced normalization** (company, title, location)  
✅ **Database indexes** for fast lookups  
✅ **Comprehensive statistics** tracking  
✅ **Flexible configuration** (strict/fuzzy modes)  
✅ **Batch processing** support  
✅ **Well-tested** with unit and integration tests  

**Result:** Only unique jobs stored in database, optimized performance, detailed tracking!
