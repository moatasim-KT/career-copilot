# GROQ API Reference

## Base URL
```
/api/v1/groq
```

## Endpoints

### Optimizer

#### POST `/optimize/completion`
Generate optimized completion using GROQ optimizer.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Your query"}
  ],
  "task_type": "fast_analysis",
  "priority": "balanced",
  "temperature": 0.1,
  "max_tokens": 2000
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "content": "Response text",
    "model": "llama-3.1-8b-instant",
    "processing_time": 1.5,
    "cost": 0.000025,
    "confidence_score": 0.85
  }
}
```

#### GET `/optimize/report`
Get optimization performance report.

**Response:**
```json
{
  "success": true,
  "data": {
    "config": {...},
    "metrics": {
      "cache_hit_rate": 0.35,
      "cost_savings": 0.00015
    }
  }
}
```

#### POST `/optimize/reset`
Reset optimization metrics.

### Router

#### POST `/route/select`
Select optimal model using router.

**Request:**
```json
{
  "task_type": "fast_analysis",
  "strategy": "adaptive",
  "context": {
    "urgency": "high",
    "quality_requirement": "high"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "selected_model": "llama-3.1-8b-instant",
    "confidence": 0.85,
    "reasoning": "Selected using adaptive multi-factor analysis",
    "estimated_cost": 0.00005,
    "estimated_time": 1.2
  }
}
```

#### GET `/route/statistics`
Get routing statistics.

#### POST `/route/reset`
Reset routing metrics.

### Monitor

#### GET `/monitor/dashboard?time_range=24h`
Get monitoring dashboard data.

**Query Parameters:**
- `time_range`: `1h`, `24h`, `7d`, `30d`

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_requests": 150,
      "success_rate": 0.98,
      "total_cost": 0.0045,
      "avg_response_time": 1.2
    }
  }
}
```

#### GET `/monitor/cost-report?period=daily`
Get cost report.

**Query Parameters:**
- `period`: `hourly`, `daily`, `weekly`

#### POST `/monitor/start`
Start continuous monitoring.

#### POST `/monitor/stop`
Stop continuous monitoring.

#### GET `/monitor/export?format=json`
Export monitoring metrics.

### Health

#### GET `/health`
Health check for GROQ services.

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "services": {
    "optimizer": "operational",
    "router": "operational",
    "monitor": "operational"
  }
}
```

## Task Types
- `fast_analysis`
- `reasoning`
- `code_generation`
- `summarization`
- `translation`
- `conversation`
- `classification`

## Routing Strategies
- `performance_based`
- `cost_optimized`
- `quality_focused`
- `load_balanced`
- `adaptive`
- `round_robin`

## Priority Levels
- `speed`
- `quality`
- `cost`
- `balanced`
