# Analytics Component Reference

## Overview

The Analytics component provides comprehensive job application tracking, user behavior analysis, and performance metrics. It includes event collection, caching, processing, querying, and reporting capabilities with a multi-service architecture.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Layer     │    │  Service Layer   │    │  Data Layer     │
│                 │    │                  │    │                 │
│ • analytics.py  │◄──►│ • Analytics      │◄──►│ • analytics.py  │
│ • dashboard.py  │    │   Service Facade │    │ • application   │
│ • metrics.py    │    │ • Cache Service  │    │ • job           │
│                 │    │ • Processing     │    │ • user          │
│                 │    │ • Query Service  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              ▲
                              │
                       ┌─────────────────┐
                       │   Caching       │
                       │                 │
                       │ • Redis Cache   │
                       │ • In-Memory     │
                       │ • TTL Management│
                       └─────────────────┘
```

## Core Files

### API Layer
- **Analytics API**: [[../../backend/app/api/v1/analytics.py|analytics.py]] - Main analytics endpoints
- **Extended Analytics**: [[../../backend/app/api/v1/analytics_extended.py|analytics_extended.py]] - Advanced analytics features
- **Dashboard API**: [[../../backend/app/api/v1/dashboard.py|dashboard.py]] - Dashboard data endpoints
- **Metrics API**: [[../../backend/app/api/v1/metrics.py|metrics.py]] - Performance metrics

### Service Layer
- **Analytics Facade**: [[../../backend/app/services/analytics_service_facade.py|analytics_service_facade.py]] - Unified analytics interface
- **Core Analytics**: [[../../backend/app/services/analytics_service.py|analytics_service.py]] - Main analytics service
- **Comprehensive Analytics**: [[../../backend/app/services/comprehensive_analytics_service.py|comprehensive_analytics_service.py]] - Advanced analytics calculations
- **Cache Service**: [[../../backend/app/services/analytics_cache_service.py|analytics_cache_service.py]] - Redis/in-memory caching
- **Collection Service**: [[../../backend/app/services/analytics_collection_service.py|analytics_collection_service.py]] - Event collection
- **Processing Service**: [[../../backend/app/services/analytics_processing_service.py|analytics_processing_service.py]] - Data processing
- **Query Service**: [[../../backend/app/services/analytics_query_service.py|analytics_query_service.py]] - Data querying
- **Reporting Service**: [[../../backend/app/services/analytics_reporting_service.py|analytics_reporting_service.py]] - Report generation

### Data Layer
- **Analytics Model**: [[../../backend/app/models/analytics.py|analytics.py]] - Analytics event storage
- **Application Model**: [[../../backend/app/models/application.py|application.py]] - Application tracking
- **Job Model**: [[../../backend/app/models/job.py|job.py]] - Job data
- **User Model**: [[../../backend/app/models/user.py|user.py]] - User profiles

## Database Schema

### Analytics Table
```sql
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),  -- Nullable for system analytics
    type VARCHAR NOT NULL,                 -- Event type (e.g., 'user_login', 'job_view')
    data JSONB NOT NULL,                   -- Event data with metadata
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_analytics_user_id (user_id),
    INDEX idx_analytics_type (type),
    INDEX idx_analytics_generated_at (generated_at)
);
```

### Application Table (Analytics Context)
```sql
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    job_id INTEGER REFERENCES jobs(id) NOT NULL,
    status VARCHAR NOT NULL,               -- 'applied', 'interviewing', 'rejected', etc.
    applied_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_applications_user_id (user_id),
    INDEX idx_applications_status (status),
    INDEX idx_applications_applied_date (applied_date)
);
```

## Key Services

### Analytics Service Facade
```python
# From analytics_service_facade.py
class AnalyticsServiceFacade:
    def __init__(self, db: Session | None = None):
        self.collection = AnalyticsCollectionService(db=db)
        self.processing = AnalyticsProcessingService(db=db)
        self.query = AnalyticsQueryService(db=db)
        self.reporting = AnalyticsReportingService(db=db)

    async def collect_event(self, event_type: str, data: dict) -> bool:
        return await self.collection.collect_event(event_type, data)

    async def get_user_metrics(self, user_id: int) -> dict:
        return await self.query.get_user_metrics(user_id)

    async def generate_report(self, report_type: str, user_id: int) -> dict:
        return await self.reporting.generate_report(report_type, user_id)
```

### Analytics Cache Service
```python
# From analytics_cache_service.py
class AnalyticsCacheService:
    def __init__(self, redis_url: Optional[str] = None):
        # Redis with fallback to in-memory cache
        self.redis_client = redis.from_url(redis_url) if redis_url else None
        self._memory_cache = {}
        self._cache_timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        # Try Redis first, then memory cache
        if self.redis_client:
            return self.redis_client.get(key)
        return self._memory_cache.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        # Set with TTL in both caches
        if self.redis_client:
            self.redis_client.setex(key, ttl_seconds, json.dumps(value))
        self._memory_cache[key] = value
        self._cache_timestamps[key] = datetime.now()
```

### Comprehensive Analytics Service
```python
# From comprehensive_analytics_service.py
class ComprehensiveAnalyticsService:
    def __init__(self, db: AsyncSession, use_cache: bool = True):
        self.db = db
        self.use_cache = use_cache
        self.cache = get_analytics_cache() if use_cache else None
        self._cache_ttl = timedelta(minutes=5)

    async def get_application_counts_by_status(self, user_id: int) -> List[ApplicationStatusCount]:
        cache_key = f"app_counts_{user_id}"
        if self.use_cache and self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        # Calculate from database
        result = await self.db.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )

        counts = [ApplicationStatusCount(status=status, count=count)
                 for status, count in result.all()]

        if self.use_cache and self.cache:
            await self.cache.set(cache_key, counts, ttl_seconds=int(self._cache_ttl.total_seconds()))

        return counts
```

## API Endpoints

| Method | Endpoint | Description | Implementation |
|--------|----------|-------------|----------------|
| GET | `/api/v1/analytics/summary` | Basic analytics summary | [[../../backend/app/api/v1/analytics.py#get_analytics_summary\|get_analytics_summary()]] |
| GET | `/api/v1/analytics/trends` | Application trends over time | [[../../backend/app/api/v1/analytics.py#get_application_trends\|get_application_trends()]] |
| GET | `/api/v1/analytics/skills` | Skill gap analysis | [[../../backend/app/api/v1/analytics.py#get_skill_analysis\|get_skill_analysis()]] |
| GET | `/api/v1/analytics/comprehensive` | Full analytics dashboard | [[../../backend/app/api/v1/analytics_extended.py#get_comprehensive_analytics\|get_comprehensive_analytics()]] |
| GET | `/api/v1/dashboard/summary` | Dashboard summary data | [[../../backend/app/api/v1/dashboard.py#get_dashboard_summary\|get_dashboard_summary()]] |
| GET | `/api/v1/metrics/performance` | Performance metrics | [[../../backend/app/api/v1/metrics.py#get_performance_metrics\|get_performance_metrics()]] |

## Event Collection

### Event Types
- **User Events**: `user_login`, `user_registration`, `profile_update`
- **Job Events**: `job_view`, `job_save`, `job_apply`
- **Application Events**: `application_created`, `application_updated`, `application_status_change`
- **System Events**: `system_health_check`, `cache_hit`, `cache_miss`

### Event Collection
```python
# From analytics_collection_service.py
async def collect_event(self, event_type: str, data: dict, user_id: int = None) -> bool:
    try:
        analytics = Analytics(
            user_id=user_id,
            type=event_type,
            data={
                "event_data": data,
                "timestamp": datetime.now(UTC).isoformat(),
                "event_type": event_type,
                "processed": False
            }
        )
        self.db.add(analytics)
        await self.db.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to collect event: {e}")
        await self.db.rollback()
        return False
```

## Caching Strategy

### Multi-Level Caching
1. **Redis Cache**: Distributed caching for production
2. **In-Memory Cache**: Fallback for development/single-instance
3. **Database Cache**: Last resort with query optimization

### Cache Keys
```python
# Standardized cache key generation
def make_cache_key(prefix: str, user_id: int, **params) -> str:
    key_parts = [prefix, str(user_id)]
    for k, v in sorted(params.items()):
        key_parts.append(f"{k}:{v}")
    return ":".join(key_parts)

# Examples:
# "analytics:summary:123"
# "analytics:trends:123:period:last_30_days"
# "analytics:skills:123:category:technical"
```

### TTL Management
- **Dashboard Data**: 5 minutes
- **Trend Analysis**: 15 minutes
- **Skill Analysis**: 30 minutes
- **Performance Metrics**: 1 minute

## Analytics Types

### User Engagement Analytics
- **Login Frequency**: Daily/weekly/monthly active users
- **Feature Usage**: Most used features, time spent
- **Goal Progress**: Application goals vs. actual progress
- **Retention Metrics**: User churn and retention rates

### Application Analytics
- **Success Rates**: Interview/application conversion rates
- **Status Distribution**: Applications by status (applied, interviewing, rejected)
- **Timeline Analysis**: Average time to response/interview
- **Company Analysis**: Performance by company size/industry

### Market Analytics
- **Skill Demand**: Most requested skills in job postings
- **Salary Trends**: Average salaries by role/location
- **Industry Growth**: Job posting trends by industry
- **Geographic Distribution**: Job opportunities by location

### Performance Analytics
- **System Performance**: Response times, error rates
- **Cache Performance**: Hit rates, miss rates
- **Database Performance**: Query times, connection pooling
- **API Usage**: Endpoint usage patterns

## Data Processing Pipeline

### 1. Event Collection
```python
# Raw events stored in analytics table
{
    "user_id": 123,
    "type": "job_view",
    "data": {
        "event_data": {"job_id": 456, "source": "linkedin"},
        "timestamp": "2024-01-15T10:30:00Z",
        "event_type": "job_view",
        "processed": false
    }
}
```

### 2. Event Processing
```python
# Events processed and enriched
async def process_events(self, batch_size: int = 100):
    unprocessed = await self.db.execute(
        select(Analytics)
        .where(Analytics.data.op("->>")("processed") == "false")
        .limit(batch_size)
    )

    for event in unprocessed:
        # Enrich with additional context
        event.data["processed"] = True
        event.data["processed_at"] = datetime.now(UTC).isoformat()
        event.data["enriched_data"] = await self._enrich_event(event)

    await self.db.commit()
```

### 3. Aggregation & Reporting
```python
# Aggregated metrics calculated on demand
async def calculate_user_metrics(self, user_id: int) -> dict:
    # Application counts by status
    status_counts = await self.db.execute(
        select(Application.status, func.count(Application.id))
        .where(Application.user_id == user_id)
        .group_by(Application.status)
    )

    # Job view trends
    job_views = await self.db.execute(
        select(func.date(Analytics.generated_at), func.count(Analytics.id))
        .where(
            and_(
                Analytics.user_id == user_id,
                Analytics.type == "job_view"
            )
        )
        .group_by(func.date(Analytics.generated_at))
        .order_by(func.date(Analytics.generated_at))
    )

    return {
        "application_status_counts": dict(status_counts.all()),
        "job_view_trends": job_views.all(),
        "total_applications": sum(status_counts.values()),
        "total_job_views": sum(count for _, count in job_views.all())
    }
```

## Configuration

### Environment Variables
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
ANALYTICS_CACHE_TTL_MINUTES=5

# Analytics Settings
ANALYTICS_BATCH_SIZE=100
ANALYTICS_PROCESSING_INTERVAL_MINUTES=15
ANALYTICS_RETENTION_DAYS=365

# Performance Monitoring
ANALYTICS_ENABLE_METRICS=true
ANALYTICS_METRICS_INTERVAL_SECONDS=60
```

### Service Configuration
```python
# From core/config.py
class AnalyticsSettings(BaseSettings):
    redis_url: Optional[str] = None
    cache_ttl_minutes: int = 5
    batch_size: int = 100
    processing_interval_minutes: int = 15
    retention_days: int = 365
    enable_metrics: bool = True
    metrics_interval_seconds: int = 60
```

## Monitoring & Performance

### Cache Performance Metrics
- **Hit Rate**: Percentage of cache hits vs. total requests
- **Miss Rate**: Percentage of cache misses requiring database queries
- **Average Response Time**: Time to retrieve cached vs. fresh data
- **Memory Usage**: Redis memory consumption trends

### Database Performance
- **Query Times**: Average time for analytics queries
- **Connection Pool**: Active/idle connections
- **Index Usage**: Query plans and index effectiveness
- **Data Growth**: Analytics table size and growth rate

### API Performance
- **Response Times**: P95 response times for analytics endpoints
- **Error Rates**: Failed request percentages
- **Throughput**: Requests per second by endpoint
- **Concurrent Users**: Active analytics sessions

## Testing

### Unit Tests
```python
# Test analytics service
def test_collect_event(db: Session):
    service = AnalyticsService(db)
    success = service.collect_event("test_event", {"key": "value"}, user_id=1)
    assert success == True

    # Verify event stored
    event = db.query(Analytics).filter(Analytics.type == "test_event").first()
    assert event is not None
    assert event.data["event_data"]["key"] == "value"
```

### Integration Tests
```python
# Test full analytics pipeline
async def test_analytics_pipeline(db: AsyncSession):
    facade = AnalyticsServiceFacade(db)

    # Collect event
    await facade.collect_event("job_view", {"job_id": 123})

    # Process events
    await facade.processing.process_batch()

    # Query metrics
    metrics = await facade.query.get_user_metrics(1)
    assert "job_views" in metrics
```

### Performance Tests
```python
# Test caching performance
def test_cache_performance():
    cache = AnalyticsCacheService()

    # Benchmark cache operations
    start_time = time.time()
    for i in range(1000):
        cache.set(f"key_{i}", f"value_{i}")
        assert cache.get(f"key_{i}") == f"value_{i}"
    end_time = time.time()

    avg_time = (end_time - start_time) / 1000
    assert avg_time < 0.001  # Less than 1ms per operation
```

**Test Files:**
- [[../../backend/tests/test_analytics.py|test_analytics.py]] - Core analytics tests
- [[../../backend/tests/test_analytics_cache.py|test_analytics_cache.py]] - Cache service tests
- [[../../backend/tests/test_comprehensive_analytics.py|test_comprehensive_analytics.py]] - Comprehensive analytics tests

## Scaling Considerations

### Horizontal Scaling
- **Event Sharding**: Distribute events across multiple databases
- **Cache Clustering**: Redis cluster for distributed caching
- **Worker Pools**: Multiple Celery workers for processing

### Data Archiving
- **Cold Storage**: Move old analytics data to cheaper storage
- **Data Aggregation**: Pre-compute common metrics
- **Retention Policies**: Automatic cleanup of old data

### Performance Optimization
- **Query Optimization**: Database indexes and query planning
- **Batch Processing**: Process events in batches
- **Async Operations**: Non-blocking analytics calculations

## Related Components

- **Jobs**: [[jobs-component|Jobs Component]] - Job data source for analytics
- **Applications**: [[applications-component|Applications Component]] - Application tracking data
- **Dashboard**: [[../../backend/app/api/v1/dashboard.py|Dashboard API]] - Analytics visualization
- **Caching**: [[../../backend/app/services/cache_service.py|Cache Service]] - General caching infrastructure

## Common Patterns

### Cache-First Pattern
```python
async def get_analytics_with_cache(self, user_id: int, metric_type: str) -> dict:
    cache_key = f"analytics:{metric_type}:{user_id}"

    # Try cache first
    if self.cache:
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

    # Calculate fresh data
    data = await self._calculate_metrics(user_id, metric_type)

    # Cache result
    if self.cache:
        await self.cache.set(cache_key, data, ttl_seconds=300)

    return data
```

### Event-Driven Analytics
```python
# Event-driven metric updates
async def handle_application_event(self, event: dict):
    event_type = event["type"]
    user_id = event["user_id"]

    if event_type == "application_created":
        # Update application count cache
        await self._invalidate_user_cache(user_id, "application_counts")

    elif event_type == "application_status_changed":
        # Update status distribution cache
        await self._invalidate_user_cache(user_id, "status_distribution")
        # Trigger success rate recalculation
        await self._recalculate_success_rates(user_id)
```

### Batch Processing Pattern
```python
# Efficient batch processing
async def process_analytics_batch(self, batch_size: int = 1000):
    while True:
        # Get unprocessed events
        events = await self.db.execute(
            select(Analytics)
            .where(Analytics.data.op("->>")("processed") == "false")
            .limit(batch_size)
        )

        if not events:
            break

        # Process in bulk
        processed_events = []
        for event in events:
            processed_event = await self._process_single_event(event)
            processed_events.append(processed_event)

        # Bulk update
        await self.db.execute(
            update(Analytics)
            .where(Analytics.id.in_([e.id for e in processed_events]))
            .values(data=bindparam("data"))
        )

        await self.db.commit()
```

---

*See also: [[../api/API.md#analytics|Analytics API Docs]], [[../../backend/app/services/analytics_cache_service.py|Cache Implementation]], [[../../backend/app/models/analytics.py|Analytics Data Model]]*"