# Enhanced Analytics Quick Reference

## Quick Start

### Get Comprehensive Analytics Summary

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/comprehensive-summary?days=90"
```

### Get Trend Analysis

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/trends"
```

### Get Skill Gap Analysis

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/skill-gap-analysis"
```

## Endpoints

| Endpoint | Method | Description | Cache TTL |
|----------|--------|-------------|-----------|
| `/api/v1/analytics/comprehensive-summary` | GET | Complete analytics with all metrics | 5 min |
| `/api/v1/analytics/trends` | GET | Trend analysis with custom date ranges | 5 min |
| `/api/v1/analytics/skill-gap-analysis` | GET | Skill gap analysis with recommendations | 5 min |
| `/api/v1/analytics/cache` | DELETE | Clear user's analytics cache | N/A |
| `/api/v1/analytics/cache/stats` | GET | Get cache performance statistics | N/A |

## Key Metrics

### Comprehensive Summary Includes:

- **Basic Counts**: Total jobs, total applications
- **Status Breakdown**: Applications by status (applied, interview, offer, etc.)
- **Rate Metrics**: Interview rate, offer rate, acceptance rate
- **Trends**: Daily, weekly, monthly trends with direction and % change
- **Top Skills**: Most common skills in jobs with percentages
- **Top Companies**: Most applied-to companies with counts
- **Time-based**: Daily, weekly, monthly application counts
- **Goals**: Daily goal and progress tracking

### Trend Analysis Includes:

- **Direction**: up, down, or neutral for each period
- **Percentage Change**: % change from previous period
- **Time Series Data**: Data points for visualization
- **Custom Date Ranges**: Flexible analysis periods

### Skill Gap Analysis Includes:

- **User Skills**: Current skills from profile
- **Market Skills**: Top skills in demand (from jobs)
- **Missing Skills**: Skills to learn
- **Coverage %**: Percentage of market skills user has
- **Recommendations**: Personalized learning suggestions

## Query Parameters

### Comprehensive Summary

- `days` (optional): Analysis period in days (1-365, default: 90)

### Trend Analysis

- `start_date` (optional): Start date (YYYY-MM-DD, default: 30 days ago)
- `end_date` (optional): End date (YYYY-MM-DD, default: today)

## Response Times

| Endpoint | First Request | Cached Request |
|----------|--------------|----------------|
| Comprehensive Summary | < 3s | < 100ms |
| Trend Analysis | < 2s | < 100ms |
| Skill Gap Analysis | < 2s | < 100ms |

## Cache Management

### Clear Cache

```bash
curl -X DELETE "http://localhost:8000/api/v1/analytics/cache"
```

### Get Cache Stats

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/cache/stats"
```

## Database Indexes

The following indexes are automatically created for optimal performance:

- `idx_applications_user_applied_date` - For date-based queries
- `idx_applications_user_status` - For status-based analytics
- `idx_applications_user_date_status` - For complex queries
- `idx_jobs_user_company` - For company analytics
- `idx_jobs_user_created_at` - For date-based job queries
- `idx_jobs_tech_stack_gin` - For tech stack queries
- `idx_users_skills_gin` - For skills queries

## Configuration

### Redis (Optional)

Set in environment or `.env`:

```bash
REDIS_URL=redis://localhost:6379/0
```

If Redis is not available, the system automatically uses in-memory caching.

## Testing

Run tests:

```bash
pytest tests/test_enhanced_analytics.py -v
```

Run with coverage:

```bash
pytest tests/test_enhanced_analytics.py --cov=app.services.comprehensive_analytics_service --cov-report=html
```

## Common Use Cases

### Dashboard Analytics

```python
# Get complete dashboard data
response = await client.get("/api/v1/analytics/comprehensive-summary?days=90")
data = response.json()

# Display key metrics
print(f"Total Applications: {data['total_applications']}")
print(f"Interview Rate: {data['rates']['interview_rate']}%")
print(f"Daily Goal Progress: {data['daily_goal_progress']}%")
```

### Trend Visualization

```python
# Get trend data for charts
response = await client.get("/api/v1/analytics/trends")
data = response.json()

# Plot time series
for point in data['time_series_data']:
    print(f"{point['date']}: {point['count']} applications")
```

### Skill Recommendations

```python
# Get personalized skill recommendations
response = await client.get("/api/v1/analytics/skill-gap-analysis")
data = response.json()

# Show recommendations
for rec in data['analysis']['recommendations']:
    print(f"💡 {rec}")
```

## Troubleshooting

### Slow Response Times

1. Check if indexes are applied:
   ```sql
   SELECT * FROM pg_indexes WHERE tablename = 'applications';
   ```

2. Check cache hit rate:
   ```bash
   curl http://localhost:8000/api/v1/analytics/cache/stats
   ```

3. Clear cache and retry:
   ```bash
   curl -X DELETE http://localhost:8000/api/v1/analytics/cache
   ```

### Missing Data

1. Verify data exists in database
2. Clear cache to force refresh
3. Check date ranges in query parameters

### Cache Not Working

1. Check Redis connection: `redis-cli ping`
2. System automatically falls back to in-memory cache
3. Check cache stats endpoint for backend type

## Performance Tips

1. **Use Caching**: Repeated requests are served from cache (< 100ms)
2. **Appropriate Time Ranges**: Use shorter periods for faster responses
3. **Clear Cache After Updates**: Clear cache after bulk data imports
4. **Monitor Cache Stats**: Check hit rates to optimize cache strategy

## Integration Examples

### Frontend Integration

```typescript
// Fetch comprehensive analytics
const analytics = await fetch('/api/v1/analytics/comprehensive-summary?days=90')
  .then(res => res.json());

// Display metrics
console.log(`Interview Rate: ${analytics.rates.interview_rate}%`);
console.log(`Weekly Trend: ${analytics.trends.weekly.direction}`);

// Fetch skill gaps
const skillGaps = await fetch('/api/v1/analytics/skill-gap-analysis')
  .then(res => res.json());

// Show recommendations
skillGaps.analysis.recommendations.forEach(rec => {
  console.log(`Recommendation: ${rec}`);
});
```

### Python Integration

```python
import httpx

async with httpx.AsyncClient() as client:
    # Get analytics
    response = await client.get(
        "http://localhost:8000/api/v1/analytics/comprehensive-summary",
        params={"days": 90}
    )
    analytics = response.json()
    
    # Process data
    print(f"Total Applications: {analytics['total_applications']}")
    print(f"Interview Rate: {analytics['rates']['interview_rate']}%")
```

## Support

For issues or questions:
1. Check the comprehensive implementation summary
2. Review test cases for usage examples
3. Check cache stats for performance issues
4. Verify database indexes are applied
