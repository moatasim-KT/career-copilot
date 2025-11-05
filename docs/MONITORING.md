# Career Copilot Monitoring & Observability

This document describes the monitoring and observability setup for Career Copilot.

## Overview

The application provides multiple layers of observability:

1. **Prometheus Metrics** - Time-series metrics for performance monitoring
2. **OpenTelemetry Traces** - Distributed tracing for request flows
3. **Application Logs** - Structured logging with correlation IDs
4. **Health Checks** - Real-time component status

## Prometheus Metrics

### Available Metrics

The `/metrics` endpoint exposes the following Prometheus metrics:

#### HTTP Metrics
- `http_requests_total` - Total HTTP requests by method, endpoint, and status
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_progress` - Current in-flight requests

#### Application Metrics
- `contract_analysis_duration_seconds` - Job application analysis duration
- `contract_analysis_total` - Total analyses by status
- `ai_service_request_duration_seconds` - AI provider latency
- `ai_service_requests_total` - AI requests by provider, model, status
- `ai_service_rate_limit_errors_total` - Rate limit errors by provider

#### Infrastructure Metrics
- `database_connection_errors_total` - Database connection failures
- `redis_connection_errors_total` - Redis connection failures
- `cache_hits_total` - Cache hits by type
- `cache_misses_total` - Cache misses by type
- `active_users` - Current active user count

### Accessing Metrics

**Local Development:**
```bash
curl http://localhost:8002/metrics
```

**Production:**
```bash
curl https://api.career-copilot.com/metrics
```

### Prometheus Setup

#### Local Prometheus

1. **Install Prometheus:**
   ```bash
   # macOS
   brew install prometheus
   
   # Linux
   wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
   tar xvf prometheus-*.tar.gz
   cd prometheus-*
   ```

2. **Configure scrape target:**
   
   Use the provided config at `monitoring/prometheus/prometheus.yml`:
   ```yaml
   scrape_configs:
     - job_name: 'career-copilot-api'
       scrape_interval: 10s
       static_configs:
         - targets: ['localhost:8002']
       metrics_path: '/metrics'
   ```

3. **Start Prometheus:**
   ```bash
   prometheus --config.file=monitoring/prometheus/prometheus.yml
   ```

4. **Access UI:**
   
   Open http://localhost:9090 in your browser.

#### Example Queries

**Request rate (per second):**
```promql
rate(http_requests_total[5m])
```

**95th percentile latency:**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Error rate:**
```promql
rate(http_requests_total{status=~"5.."}[5m])
```

**Cache hit ratio:**
```promql
sum(rate(cache_hits_total[5m])) / 
(sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))
```

**AI service latency by provider:**
```promql
rate(ai_service_request_duration_seconds_sum[5m]) / 
rate(ai_service_request_duration_seconds_count[5m])
```

## OpenTelemetry Tracing

### Configuration

Enable tracing in `backend/.env`:

```bash
ENABLE_OPENTELEMETRY=true
OTLP_ENDPOINT=http://localhost:4317
SERVICE_NAME=career-copilot-api
```

### Collector Setup

#### Using Jaeger (All-in-One)

```bash
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

Access UI: http://localhost:16686

#### Using OpenTelemetry Collector

Create `otel-collector-config.yaml`:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  batch:
    timeout: 10s

exporters:
  logging:
    loglevel: debug
  jaeger:
    endpoint: localhost:14250
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging, jaeger]
```

Run collector:
```bash
docker run -v $(pwd)/otel-collector-config.yaml:/etc/otel-collector-config.yaml \
  -p 4317:4317 \
  otel/opentelemetry-collector:latest \
  --config=/etc/otel-collector-config.yaml
```

### Manual Instrumentation

For custom spans in your code:

```python
from app.core.telemetry import get_tracer, create_span

tracer = get_tracer(__name__)

# Context manager style
with create_span("process_resume", user_id=123) as span:
    # Your code here
    result = process_resume(file)
    span.set_attribute("resume.pages", result.pages)
    span.set_attribute("resume.parsed", True)

# Manual start/end
span = tracer.start_span("fetch_jobs")
try:
    jobs = fetch_jobs_from_api()
    span.set_attribute("job.count", len(jobs))
finally:
    span.end()
```

## Health Checks

### Unified Health Endpoint

**Endpoint:** `GET /api/v1/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-03T09:51:10.000Z",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 12.5
    },
    "cache": {
      "status": "healthy",
      "latency_ms": 3.2
    },
    "scheduler": {
      "status": "healthy",
      "jobs": 4
    },
    "celery_workers": {
      "status": "unhealthy",
      "error": "No workers available"
    }
  }
}
```

**Status Codes:**
- `200` - All critical components healthy
- `503` - One or more critical components unhealthy

### Component Status

| Component | Critical | Description |
|-----------|----------|-------------|
| Database | ✅ Yes | PostgreSQL connection and query execution |
| Cache | ⚠️ No | Redis availability (degrades gracefully) |
| Scheduler | ⚠️ No | APScheduler job status |
| Celery Workers | ⚠️ No | Background task workers (optional) |

## Grafana Dashboards

### Setup

1. **Install Grafana:**
   ```bash
   brew install grafana  # macOS
   ```

2. **Start Grafana:**
   ```bash
   brew services start grafana
   ```

3. **Access:** http://localhost:3000 (admin/admin)

4. **Add Prometheus data source:**
   - Configuration → Data Sources → Add Prometheus
   - URL: `http://localhost:9090`

5. **Import dashboard:**
   - Use dashboard ID `1860` for Node Exporter
   - Create custom dashboard for Career Copilot metrics

### Custom Dashboard Panels

**API Performance:**
- Query: `rate(http_requests_total[5m])`
- Visualization: Time series graph
- Legend: `{{method}} {{endpoint}}`

**Error Rate:**
- Query: `sum(rate(http_requests_total{status=~"5.."}[5m])) by (endpoint)`
- Visualization: Time series with threshold alerts

**AI Service Latency:**
- Query: `histogram_quantile(0.95, rate(ai_service_request_duration_seconds_bucket[5m]))`
- Visualization: Heatmap by provider

## Alerting

### Prometheus Alerts

Create `monitoring/prometheus/alerts/api.yml`:

```yaml
groups:
  - name: api_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "95th percentile latency is {{ $value }}s"
      
      - alert: DatabaseDown
        expr: up{job="career-copilot-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API is down"
```

### Alertmanager

Configure notifications in `monitoring/alertmanager/config.yml`:

```yaml
route:
  receiver: 'slack'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 3h

receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

## Log Aggregation

All logs include:
- **Correlation ID** - Tracks requests across services
- **Timestamp** - ISO 8601 format
- **Level** - DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Context** - User ID, endpoint, etc.

### Log Format

```json
{
  "timestamp": "2025-11-03T09:51:10.123Z",
  "level": "INFO",
  "correlation_id": "7869b4bf-2ab7-4692-a52c-beca604b058d",
  "user_id": 123,
  "endpoint": "/api/v1/jobs",
  "method": "GET",
  "status": 200,
  "duration_ms": 45.2,
  "message": "Request completed successfully"
}
```

## Production Checklist

- [ ] Prometheus scraping enabled
- [ ] Grafana dashboards configured
- [ ] Alertmanager notifications set up
- [ ] OpenTelemetry exporter configured (optional)
- [ ] Log retention policy defined
- [ ] Health check monitoring active
- [ ] Metric retention tuned (default 15 days)
- [ ] Alert thresholds validated
- [ ] Dashboard access restricted

## Troubleshooting

### Metrics not appearing

1. Check `/metrics` endpoint is accessible:
   ```bash
   curl http://localhost:8002/metrics
   ```

2. Verify Prometheus scrape target in UI:
   - http://localhost:9090/targets
   - Should show `career-copilot-api` as UP

3. Check logs for middleware errors:
   ```bash
   tail -f logs/backend/app.log | grep MetricsMiddleware
   ```

### Traces not showing in Jaeger

1. Verify OpenTelemetry enabled:
   ```bash
   grep ENABLE_OPENTELEMETRY backend/.env
   ```

2. Check OTLP endpoint reachable:
   ```bash
   nc -zv localhost 4317
   ```

3. Look for telemetry initialization in logs:
   ```bash
   grep "OpenTelemetry configured" logs/backend/app.log
   ```

### High cardinality warnings

If Prometheus complains about high cardinality:

1. Review metric labels (avoid user IDs, UUIDs)
2. Aggregate labels in queries instead
3. Use relabeling in prometheus.yml

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [FastAPI Metrics Best Practices](https://fastapi.tiangolo.com/advanced/middleware/)
