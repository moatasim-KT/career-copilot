# Performance Scripts

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Testing Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

Comprehensive performance testing and optimization tools for Career Copilot.

## Quick Start

```bash
# Ensure backend and database are running
docker-compose up -d

# Run performance tests
python performance_optimization_suite.py

# With custom parameters
python performance_optimization_suite.py --users 50 --requests 10 --verbose
```

## Scripts

### `performance_optimization_suite.py`

Comprehensive performance testing suite that validates:
- API endpoint performance under concurrent load
- Database query performance
- Cost efficiency and free-tier compliance
- Database index optimization opportunities

**Usage:**
```bash
python performance_optimization_suite.py [OPTIONS]

Options:
  --backend-url URL    Backend API URL (default: http://localhost:8000)
  --output FILE        Output report filename
  --users N            Number of concurrent users (default: 50)
  --requests N         Requests per user (default: 10)
  --verbose, -v        Enable verbose logging
```

**Exit Codes:**
- `0` - Tests passed (score ≥ 75)
- `1` - Tests completed, improvements recommended
- `2` - Tests incomplete (services unavailable)

**Example Output:**
```
============================================================
ENVIRONMENT CHECK
============================================================
Backend URL: http://localhost:8000
Backend Available: ✅
Database Available: ✅

============================================================
PERFORMANCE TEST SUMMARY
============================================================
Total Duration: 45.23s
Tests Completed: 2
Performance Score: 78.5/100
Free Tier Compliant: False
Estimated Monthly Cost: $0.00
Recommendations: 5

Report saved to: performance_optimization_report_20251116_100149.json
```

## Prerequisites

### Required Services

1. **Backend API** (port 8000)
   ```bash
   cd backend && uvicorn app.main:app --reload
   ```

2. **PostgreSQL Database**
   ```bash
   docker-compose up -d postgres
   ```

### Optional Services

- **Redis** (port 6379) - For cache performance tests
  ```bash
  docker-compose up -d redis
  ```

## Test Scenarios

### Light Load (Development)
```bash
python performance_optimization_suite.py --users 10 --requests 5
```

### Normal Load (Typical Usage)
```bash
python performance_optimization_suite.py --users 50 --requests 10
```

### Heavy Load (Peak Hours)
```bash
python performance_optimization_suite.py --users 100 --requests 20
```

### Stress Test (Capacity Planning)
```bash
python performance_optimization_suite.py --users 200 --requests 30
```

## Understanding Results

### Performance Score

Score is calculated from:
- **Error Rate**: <5% is good
- **Response Time**: <2s average is good
- **Throughput**: >10 req/s is good
- **Cost Efficiency**: Free tier compliance

### Key Metrics

| Metric            | Good      | Needs Improvement |
| ----------------- | --------- | ----------------- |
| Success Rate      | >95%      | <95%              |
| Avg Response Time | <2s       | >2s               |
| 95th Percentile   | <5s       | >5s               |
| Error Rate        | <5%       | >5%               |
| Throughput        | >10 req/s | <10 req/s         |

### Report Structure

The generated JSON report includes:

```json
{
  "summary": {
    "overall_performance_score": 78.5,
    "free_tier_compliant": false,
    "estimated_monthly_cost": 0.00,
    "tests_completed": 2,
    "recommendations_generated": 5
  },
  "performance_metrics": [...],
  "cost_analysis": {...},
  "database_analysis": {...},
  "optimization_recommendations": [...]
}
```

## Common Issues

### Backend Not Available

**Error:**
```
❌ Backend API not available at http://localhost:8000
```

**Solution:**
```bash
cd backend && uvicorn app.main:app --reload --port 8000
```

### Database Not Available

**Error:**
```
❌ Database engine not initialized
```

**Solutions:**
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Configure .env
echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/career_copilot" >> backend/.env

# Run migrations
cd backend && alembic upgrade head
```

### High Error Rate

**Symptoms:** Error rate >5%

**Possible Causes:**
- Database connection pool exhausted
- Missing dependencies
- Backend server overloaded

**Solutions:**
1. Check backend logs
2. Reduce test load (`--users 10`)
3. Ensure all services running
4. Check database connection settings

### Slow Response Times

**Symptoms:** Average response time >2s

**Causes:**
- Missing database indexes
- No caching layer
- Expensive operations

**Solutions:**
1. Review index recommendations in report
2. Implement Redis caching
3. Optimize database queries
4. Use async operations

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run Performance Tests
  run: |
    python scripts/performance/performance_optimization_suite.py \
      --users 20 \
      --requests 10 \
      --output performance_report.json

- name: Upload Report
  uses: actions/upload-artifact@v3
  with:
    name: performance-report
    path: performance_report.json
```

### Pre-Commit Hook

```bash
# .git/hooks/pre-push
#!/bin/bash
python scripts/performance/performance_optimization_suite.py --users 10 --requests 5
if [ $? -eq 1 ]; then
    echo "Performance degradation detected. Review recommendations."
fi
```

## Development

### Adding New Tests

1. Create test method in `PerformanceOptimizationSuite` class
2. Return `PerformanceMetrics` object
3. Add to `run_comprehensive_performance_tests()`
4. Update recommendations in `generate_optimization_recommendations()`

Example:
```python
def test_cache_performance(self) -> PerformanceMetrics:
    """Test Redis cache performance"""
    if not self._redis_available():
        return self._create_skipped_metrics("Cache Performance", "Redis not available")
    
    # Run cache tests...
    return metrics
```

### Custom Recommendations

```python
recommendations.append({
    "category": "performance",
    "priority": "high",
    "title": "Custom Recommendation",
    "description": "Detailed description",
    "recommendation": "Actionable steps",
    "impact": "Expected improvement"
})
```

## Related Documentation

- [Performance Testing Guide](../../docs/performance/PERFORMANCE_TESTING_GUIDE.md) - Comprehensive guide
- [API Documentation](../../docs/api/README.md) - Endpoint details
- [Database Schema](../../docs/architecture/database-schema.md) - Table structures
- [Deployment Guide](../../docs/deployment/README.md) - Production setup

## Support

For issues or questions:
1. Check the [Performance Testing Guide](../../docs/performance/PERFORMANCE_TESTING_GUIDE.md)
2. Review generated report recommendations
3. Check backend logs: `docker-compose logs backend`
4. Enable verbose mode: `--verbose`
