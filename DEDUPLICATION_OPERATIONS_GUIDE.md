# Job Deduplication System - Operations Guide

This guide provides instructions for operating and monitoring the job deduplication system in production.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Scripts and Tools](#scripts-and-tools)
3. [Monitoring](#monitoring)
4. [Maintenance](#maintenance)
5. [Troubleshooting](#troubleshooting)

---

## Overview

The job deduplication system prevents duplicate jobs from being saved to the database using three strategies:

1. **URL Matching** - Exact match after normalization
2. **Fingerprint Matching** - MD5 hash of (title + company + location)
3. **Fuzzy Matching** - Similarity-based detection (company ≥0.80, title ≥0.85)

All new jobs automatically receive a fingerprint, and deduplication happens during the ingestion process.

---

## Scripts and Tools

### 1. Monitor Deduplication Metrics

**Location:** `backend/scripts/monitor_deduplication.py`

**Purpose:** Provides comprehensive insights into deduplication performance and statistics.

**Usage:**
```bash
# View metrics for last 7 days (default)
python scripts/monitor_deduplication.py

# View metrics for last 30 days
python scripts/monitor_deduplication.py --days 30
```

**Output:**
- Overall statistics (total jobs, fingerprint coverage, duplicates)
- Recent activity (daily breakdown)
- Duplicate patterns (most duplicated jobs)
- URL-based duplicates
- Per-user coverage statistics
- Recommendations for action

**When to Use:**
- Daily/weekly monitoring of system health
- After major data imports
- When investigating performance issues
- Before running cleanup operations

---

### 2. Backfill Job Fingerprints

**Location:** `backend/scripts/backfill_job_fingerprints.py`

**Purpose:** Generates fingerprints for existing jobs that don't have them (migration tool).

**Usage:**
```bash
# Dry run (see what would be changed)
python scripts/backfill_job_fingerprints.py --dry-run

# Run backfill with default batch size (1000)
python scripts/backfill_job_fingerprints.py

# Run with custom batch size
python scripts/backfill_job_fingerprints.py --batch-size 500
```

**Options:**
- `--dry-run` - Show what would be done without making changes
- `--batch-size N` - Process N jobs per batch (default: 1000)

**Output:**
- Current status (jobs with/without fingerprints)
- Processing progress
- Errors (if any)
- Final verification

**When to Use:**
- After initial migration to deduplication system
- When fingerprint coverage drops unexpectedly
- After database restoration
- When adding new users with existing job data

---

### 3. End-to-End Testing

**Location:** `backend/scripts/test_deduplication_e2e.py`

**Purpose:** Comprehensive test of the entire deduplication workflow.

**Usage:**
```bash
python scripts/test_deduplication_e2e.py
```

**Test Phases:**
1. **Phase 1:** Initial job scraping with deduplication
2. **Phase 2:** Re-scraping to verify duplicate filtering
3. **Phase 3:** Fingerprint validation
4. **Phase 4:** Bulk deduplication analysis

**Output:**
- Detailed results for each phase
- Statistics on jobs found, saved, and filtered
- Fingerprint validation for recent jobs
- Bulk deduplication check results
- Final summary with recommendations

**When to Use:**
- After system updates or code changes
- Weekly regression testing
- Before major releases
- When investigating deduplication issues

---

## Monitoring

### Daily Monitoring Checklist

```bash
# 1. Run monitoring script
python scripts/monitor_deduplication.py

# 2. Check for:
#    - Fingerprint coverage is > 95%
#    - No unusual spike in duplicates
#    - All users have good coverage
```

### Key Metrics to Track

| Metric | Healthy Range | Action if Outside Range |
|--------|---------------|------------------------|
| Fingerprint Coverage | > 95% | Run backfill script |
| Potential Duplicates | < 5% of total | Investigate duplicate patterns |
| Daily Duplicate Rate | 10-30% | Check API configurations |
| New Jobs Per Day | Varies by user | Monitor for API issues |

### Alerts to Set Up

1. **Low Fingerprint Coverage** (< 90%)
   - Indicates backfill needed or ingestion issue

2. **High Duplicate Rate** (> 50%)
   - May indicate scraper configuration issue

3. **No New Jobs for 24h**
   - Possible API failure or rate limiting

---

## Maintenance

### Weekly Tasks

```bash
# 1. Monitor system health
python scripts/monitor_deduplication.py --days 7

# 2. Review recommendations and take action
```

### Monthly Tasks

```bash
# 1. Run comprehensive monitoring
python scripts/monitor_deduplication.py --days 30

# 2. Check for long-term duplicate patterns
# 3. Verify backfill coverage

# 4. Optional: Run E2E test
python scripts/test_deduplication_e2e.py
```

### Database Cleanup (As Needed)

If monitoring reveals duplicates in the database:

```python
# Use the JobDeduplicationService to find duplicates
from app.services.job_deduplication_service import JobDeduplicationService
from app.core.database import SessionLocal

db = SessionLocal()
service = JobDeduplicationService(db)

# Analyze duplicates (doesn't delete)
results = service.bulk_deduplicate_database_jobs(user_id=None)  # All users
print(f"Found {results['duplicates_found']} duplicates")

# Review results before deletion
# Implement deletion logic if needed (not automatic for safety)
```

---

## Troubleshooting

### Issue: Jobs Missing Fingerprints

**Symptoms:**
- Monitoring shows < 95% coverage
- New jobs being saved without fingerprints

**Diagnosis:**
```bash
python scripts/monitor_deduplication.py
# Check "With fingerprint" percentage
```

**Solution:**
```bash
# Option 1: Run backfill
python scripts/backfill_job_fingerprints.py

# Option 2: Check code integration
# Verify JobScrapingService is using deduplication_service
```

---

### Issue: Too Many Duplicates

**Symptoms:**
- Monitoring shows high duplicate count
- Users report seeing duplicate jobs

**Diagnosis:**
```bash
python scripts/monitor_deduplication.py
# Review "Duplicate Patterns Analysis" section
```

**Solution:**
1. Check if duplicates are from same source (API returning duplicates)
2. Verify normalization is working correctly
3. Review similarity thresholds (may need adjustment)
4. Consider cleaning up existing duplicates

---

### Issue: Deduplication Not Working

**Symptoms:**
- Same jobs appearing multiple times
- Duplicate count is 0 but users see duplicates

**Diagnosis:**
```bash
# Run E2E test
python scripts/test_deduplication_e2e.py

# Check logs for deduplication service
grep -r "deduplication" backend/logs/
```

**Solution:**
1. Verify deduplication service is integrated in job ingestion
2. Check that fingerprints are being generated
3. Review database indexes (run migration if needed)
4. Verify normalization functions are working

---

### Issue: Performance Degradation

**Symptoms:**
- Slow job ingestion
- Database queries taking too long

**Diagnosis:**
```sql
-- Check index usage
EXPLAIN ANALYZE SELECT * FROM jobs 
WHERE job_fingerprint = 'abc123...';

-- Check index health
SELECT * FROM pg_indexes WHERE tablename = 'jobs';
```

**Solution:**
1. Verify indexes exist:
   - `ix_jobs_job_fingerprint`
   - `ix_jobs_application_url`
   - `ix_jobs_user_company_title_location`
2. Run `ANALYZE jobs;` to update statistics
3. Consider adjusting `lookback_days` parameter

---

## Best Practices

### 1. Regular Monitoring
- Run monitoring script at least weekly
- Track trends over time
- Act on recommendations promptly

### 2. Backfill Strategy
- Always run with `--dry-run` first
- Use smaller batch sizes for large datasets
- Monitor database performance during backfill

### 3. Testing
- Run E2E test after code changes
- Test with small user sample before full deployment
- Validate fingerprint generation is working

### 4. Database Maintenance
- Keep indexes healthy with regular `ANALYZE`
- Monitor index sizes and fragmentation
- Plan for data retention and archival

---

## Reference

### Configuration

**Deduplication Thresholds** (in `job_deduplication_service.py`):
```python
COMPANY_SIMILARITY_THRESHOLD = 0.80
TITLE_SIMILARITY_THRESHOLD = 0.85
LOCATION_SIMILARITY_THRESHOLD = 0.50  # For difference check
```

**Default Settings**:
- Lookback period: 30 days
- Batch size (backfill): 1000 jobs
- Strict mode: False (fuzzy matching enabled)

### Database Schema

**New Column:**
- `job_fingerprint` - VARCHAR(32), indexed

**New Indexes:**
- `ix_jobs_job_fingerprint`
- `ix_jobs_user_company_title_location` (composite)
- `ix_jobs_application_url`

---

## Support

For issues or questions:
1. Check this guide first
2. Review `JOB_INGESTION_WORKFLOW.md` for technical details
3. Run diagnostics with monitoring and E2E test scripts
4. Check application logs for errors

---

**Last Updated:** November 4, 2025
**Version:** 1.0
