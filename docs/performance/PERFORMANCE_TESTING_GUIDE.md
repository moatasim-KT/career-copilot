
# Performance Testing Guide

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Migration Guide
- [[DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

This guide explains how to run and interpret performance tests for the Career Copilot platform.

## Quick Start

### Prerequisites

Before running performance tests, ensure the following services are running:

1. **Backend API Server** (required for API performance tests)
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **PostgreSQL Database** (required for database performance tests)
   ```bash
   # Using Docker Compose (recommended)
   docker-compose up -d postgres
   
   # Or configure DATABASE_URL in .env
   export DATABASE_URL='postgresql://user:password@localhost:5432/career_copilot'
   ```

3. **Redis** (optional, for cache performance tests)
   ```bash
   docker-compose up -d redis
   ```

### Running Performance Tests

```bash
# Full performance test suite
python scripts/performance/performance_optimization_suite.py

# Custom test parameters
python scripts/performance/performance_optimization_suite.py \
  --users 100 \
  --requests 20 \
  --verbose

# Test against different backend URL
python scripts/performance/performance_optimization_suite.py \
  --backend-url http://staging.example.com

# Save report to specific file
python scripts/performance/performance_optimization_suite.py \
  --output my_performance_report.json
```

## Understanding the Output

### Exit Codes

- `0` - All tests passed with performance score ≥ 75
- `1` - Tests completed but performance improvements recommended (score < 75)
- `2` - Tests incomplete due to unavailable services
- Other - Test execution failed

### Performance Score (0-100)

The overall performance score is calculated based on:

- **Error Rate** (max -20 points): High error rates (>5%) reduce score
- **Response Time** (max -15 points): Slow average response times (>1s) reduce score
- **Throughput** (max -10 points): Low throughput (<10 req/s) reduces score
- **Cost Efficiency** (max -20 points): Free-tier violations reduce score

**Score Interpretation:**
- **90-100**: Excellent performance
- **75-89**: Good performance with minor optimizations needed
- **50-74**: Moderate performance, optimization recommended
- **Below 50**: Poor performance, significant improvements needed

### Test Components

#### 1. Concurrent User Load Test

Simulates multiple users accessing the API simultaneously.

**Metrics:**
- Total requests and success rate
- Average, median, 95th, and 99th percentile response times
- Throughput (requests per second)
- Error rate percentage

**Thresholds:**
- ✅ Error rate < 5%
- ✅ Average response time < 2s
- ✅ 95th percentile < 5s

#### 2. Database Query Performance

Tests common database queries used in the application.

**Tests Include:**
- User count and retrieval queries
- Job listing queries
- Analytics queries
- Complex JOIN operations

**Thresholds:**
- ✅ Average query time < 100ms
- ✅ 95th percentile < 500ms

#### 3. Database Index Analysis

Analyzes existing database indexes and suggests optimizations.

**Checks:**
- Existing indexes on each table
- Missing indexes for common query patterns
- Unused indexes (future enhancement)

#### 4. Cost Efficiency Validation

Estimates monthly costs based on usage patterns.

**Assumptions:**
- 100 active users per day
- 50 jobs per user
- 10 recommendations per user
- 5 analytics queries per user
- 2 applications per user
- 2 email notifications per user

**Free Tier Limits (Cloud Functions):**
- 2,000,000 invocations/month
- 400,000 GB-seconds compute time/month
- 1GB storage
- 1GB network egress

#### 5. Optimization Recommendations

Generates actionable recommendations based on test results.

**Categories:**
- **Reliability**: Error handling, retries, circuit breakers
- **Performance**: Caching, query optimization, CDN
- **Database**: Indexing, connection pooling
- **Cost**: Resource optimization, batch processing

## Common Issues and Solutions

### Issue: Backend API Not Available

**Symptoms:**
```
❌ Backend API not available at http://localhost:8000
API performance tests will be skipped
```

**Solution:**
```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Run tests
python scripts/performance/performance_optimization_suite.py
```

### Issue: Database Not Available

**Symptoms:**
```
❌ Database engine not initialized
Database tests will be skipped
```

**Solutions:**

1. **Using Docker Compose (recommended):**
   ```bash
   docker-compose up -d postgres
   ```

2. **Configure DATABASE_URL:**
   ```bash
   # backend/.env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/career_copilot
   ```

3. **Run migrations:**
   ```bash
   cd backend
   alembic upgrade head
   ```

### Issue: High Error Rate

**Symptoms:**
- Error rate > 5%
- Many 500 or 502 responses

**Possible Causes:**
- Database connection pool exhausted
- Backend server overloaded
- Missing dependencies or services

**Solutions:**
1. Check backend logs for errors
2. Increase database connection pool size
3. Ensure all dependencies (Redis, ChromaDB) are running
4. Reduce concurrent users in test (`--users 10`)

### Issue: Slow Response Times

**Symptoms:**
- Average response time > 2s
- 95th percentile > 5s

**Possible Causes:**
- Missing database indexes
- N+1 query problems
- No caching layer
- Expensive AI/LLM calls

**Solutions:**
1. Review database index recommendations in report
2. Implement Redis caching for frequently accessed data
3. Use async operations for LLM calls
4. Add database query monitoring (APM)

## Continuous Integration

### GitHub Actions Integration

```yaml
# .github/workflows/performance-tests.yml
name: Performance Tests

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM

jobs:
  performance:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      
      - name: Run migrations
        run: |
          cd backend && alembic upgrade head
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
      
      - name: Start backend
        run: |
          cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 5
      
      - name: Run performance tests
        run: |
          python scripts/performance/performance_optimization_suite.py \
            --users 20 \
            --requests 10 \
            --output performance_report.json
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: performance-report
          path: performance_report.json
      
      - name: Check performance threshold
        run: |
          SCORE=$(jq '.summary.overall_performance_score' performance_report.json)
          if (( $(echo "$SCORE < 75" | bc -l) )); then
            echo "::warning::Performance score ($SCORE) below threshold (75)"
            exit 1
          fi
```

## Best Practices

### Development Testing

1. **Start with minimal load:**
   ```bash
   python scripts/performance/performance_optimization_suite.py --users 5 --requests 3
   ```

2. **Gradually increase load:**
   ```bash
   python scripts/performance/performance_optimization_suite.py --users 25 --requests 5
   ```

3. **Full production simulation:**
   ```bash
   python scripts/performance/performance_optimization_suite.py --users 100 --requests 20
   ```

### Baseline Establishment

1. Run tests on clean database with sample data
2. Record baseline metrics
3. Compare future tests against baseline
4. Track performance trends over time

### Load Testing Scenarios

| Scenario    | Users | Requests | Description         |
| ----------- | ----- | -------- | ------------------- |
| Light Load  | 10    | 5        | Development testing |
| Normal Load | 50    | 10       | Typical usage       |
| Heavy Load  | 100   | 20       | Peak hours          |
| Stress Test | 200   | 30       | Capacity planning   |

## Interpreting the Report

### Sample Report Structure

```json
{
  "summary": {
    "test_duration": 45.23,
    "tests_completed": 2,
    "recommendations_generated": 5,
    "free_tier_compliant": false,
    "estimated_monthly_cost": 12.50,
    "overall_performance_score": 68.5
  },
  "performance_metrics": [
    {
      "test_name": "Concurrent User Load",
      "duration": 23.45,
      "total_requests": 500,
      "success_count": 475,
      "error_count": 25,
      "avg_response_time": 1.234,
      "p95_response_time": 3.456,
      "throughput": 21.3,
      "error_rate": 5.0
    }
  ],
  "cost_analysis": {
    "function_invocations": 33030,
    "compute_time_gb_seconds": 6604.8,
    "estimated_monthly_cost": 12.50,
    "free_tier_compliance": false
  },
  "optimization_recommendations": [
    {
      "category": "performance",
      "priority": "high",
      "title": "Implement Redis Caching",
      "description": "No caching layer detected",
      "recommendation": "Add Redis for frequently accessed data",
      "impact": "Reduced database load and faster responses"
    }
  ]
}
```

### Key Metrics to Monitor

1. **Success Rate** (target: >95%)
2. **Average Response Time** (target: <2s)
3. **95th Percentile Response Time** (target: <5s)
4. **Throughput** (target: >10 req/s)
5. **Cost per User** (target: <$0.10)

## Advanced Usage

### Custom Test Scenarios

Create custom test scripts by importing the suite:

```python
from scripts.performance.performance_optimization_suite import PerformanceOptimizationSuite

suite = PerformanceOptimizationSuite("http://localhost:8000")

# Run specific tests
metrics = suite.test_concurrent_user_load(num_users=100, requests_per_user=20)
print(f"Throughput: {metrics.throughput} req/s")

# Custom recommendations
recommendations = suite.generate_optimization_recommendations()
for rec in recommendations:
    if rec['priority'] == 'high':
        print(f"[HIGH] {rec['title']}: {rec['recommendation']}")
```

### Profiling Specific Endpoints

For detailed profiling of specific endpoints, use the `py-spy` profiler:

```bash
# Install py-spy
pip install py-spy

# Profile backend server
py-spy record -o profile.svg -- python -m uvicorn app.main:app

# View profile
open profile.svg
```

## Troubleshooting

### Enable Verbose Logging

```bash
python scripts/performance/performance_optimization_suite.py --verbose
```

### Check Individual Services

```bash
# Test backend health
curl http://localhost:8000/health

# Test database connection
python backend/scripts/verification/verify_db_connection.py

# Check Redis
redis-cli ping
```

### Docker Compose Issues

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs postgres

# Restart services
docker-compose restart
```

## Related Documentation

- [[API]] - Backend API documentation
- [[database-schema]] - Database schema
- [[deployment/README]] - Deployment guide
- [[monitoring/README]] - Monitoring setup

