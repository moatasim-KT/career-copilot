# Job Deduplication Quick Reference

## 🚀 Quick Commands

```bash
# Monitor system health
python scripts/monitor_deduplication.py

# Backfill missing fingerprints (dry run first!)
python scripts/backfill_job_fingerprints.py --dry-run
python scripts/backfill_job_fingerprints.py

# Run end-to-end test
python scripts/test_deduplication_e2e.py

# Check unit tests
pytest backend/tests/unit/test_job_deduplication_service.py -v
```

## 📊 Key Metrics

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Fingerprint Coverage | >95% | 90-95% | <90% |
| Duplicate Rate | 10-30% | 30-50% | >50% |
| Processing Time | <5s | 5-10s | >10s |

## 🔍 Troubleshooting Checklist

**Issue: Low Fingerprint Coverage**
```bash
python scripts/backfill_job_fingerprints.py
```

**Issue: Too Many Duplicates**
```bash
python scripts/monitor_deduplication.py
# Review "Duplicate Patterns Analysis"
```

**Issue: Deduplication Not Working**
```bash
pytest backend/tests/unit/test_job_deduplication_service.py -v
python scripts/test_deduplication_e2e.py
```

## 📁 Important Files

- `backend/app/services/job_deduplication_service.py` - Core service
- `backend/app/services/job_scraping_service.py` - Integration
- `backend/alembic/versions/ae995c518187_*.py` - Migration
- `DEDUPLICATION_OPERATIONS_GUIDE.md` - Full documentation

## 🎯 Deduplication Strategies

1. **URL Match** → Exact match after normalization
2. **Fingerprint** → MD5(title + company + location)
3. **Fuzzy Match** → Similarity: company≥0.80, title≥0.85

## 💾 Database

```sql
-- Check fingerprint coverage
SELECT 
  COUNT(*) as total,
  COUNT(job_fingerprint) as with_fp,
  COUNT(*) - COUNT(job_fingerprint) as without_fp
FROM jobs;

-- Find duplicates
SELECT job_fingerprint, COUNT(*) as count
FROM jobs
WHERE job_fingerprint IS NOT NULL
GROUP BY job_fingerprint
HAVING COUNT(*) > 1;
```

## ⚙️ Configuration

**Similarity Thresholds:**
- Company: 0.80
- Title: 0.85
- Location: 0.50 (for difference check)

**Defaults:**
- Lookback period: 30 days
- Batch size: 1000 jobs
- Strict mode: False (fuzzy matching ON)

## 📅 Maintenance Schedule

- **Daily:** Monitor logs for errors
- **Weekly:** Run `monitor_deduplication.py`
- **Monthly:** Review duplicate patterns, run E2E test
- **Quarterly:** Analyze trends, adjust thresholds if needed
