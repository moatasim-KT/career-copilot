# API Documentation

## Overview

Career Copilot provides a comprehensive RESTful API for managing job applications, user profiles, and AI-powered content generation.

- **Base URL**: `http://localhost:8000`
- **API Version**: v1
- **Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)

## Authentication

### JWT Authentication

All API endpoints (except public ones) require JWT authentication.

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### Using Token

```http
GET /api/v1/jobs
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Endpoints

### Jobs

#### List Jobs

```http
GET /api/v1/jobs?skip=0&limit=20&location=Berlin&source=linkedin
```

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 20, max: 100)
- `location` (string): Filter by location
- `source` (string): Filter by source (linkedin, indeed, stepstone, etc.)
- `is_active` (bool): Filter by active status

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Senior Data Scientist",
      "company": "TechCorp GmbH",
      "location": "Berlin, Germany",
      "description": "We are looking for...",
      "source": "linkedin",
      "url": "https://linkedin.com/jobs/...",
      "scraped_at": "2025-11-07T10:00:00Z",
      "is_active": true
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

#### Get Job Details

```http
GET /api/v1/jobs/{job_id}
```

**Response:**
```json
{
  "id": 1,
  "title": "Senior Data Scientist",
  "company": "TechCorp GmbH",
  "location": "Berlin, Germany",
  "description": "Detailed job description...",
  "requirements": ["Python", "Machine Learning", "SQL"],
  "salary_range": "€70,000 - €90,000",
  "source": "linkedin",
  "url": "https://linkedin.com/jobs/...",
  "scraped_at": "2025-11-07T10:00:00Z",
  "is_active": true
}
```

#### Search Jobs

```http
POST /api/v1/jobs/search
Content-Type: application/json

{
  "query": "machine learning engineer",
  "location": "Berlin",
  "skills": ["Python", "TensorFlow"],
  "min_salary": 60000
}
```

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "title": "Machine Learning Engineer",
      "company": "AI Startup",
      "relevance_score": 0.95,
      "match_details": {
        "matched_skills": ["Python", "TensorFlow"],
        "missing_skills": ["PyTorch"]
      }
    }
  ],
  "total": 10
}
```

### Applications

#### List Applications

```http
GET /api/v1/applications?skip=0&limit=20&status=pending
```

**Query Parameters:**
- `skip` (int): Number of records to skip
- `limit` (int): Maximum records to return
- `status` (string): Filter by status (pending, applied, interviewing, rejected, accepted)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "job_id": 123,
      "job_title": "Senior Data Scientist",
      "company": "TechCorp GmbH",
      "status": "applied",
      "applied_at": "2025-11-01T14:30:00Z",
      "last_updated": "2025-11-02T09:00:00Z"
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 20
}
```

#### Create Application

```http
POST /api/v1/applications
Content-Type: application/json

{
  "job_id": 123,
  "cover_letter": "Dear Hiring Manager...",
  "custom_resume": "path/to/resume.pdf",
  "notes": "Applied via company website"
}
```

**Response:**
```json
{
  "id": 1,
  "job_id": 123,
  "status": "pending",
  "applied_at": "2025-11-07T10:00:00Z",
  "message": "Application created successfully"
}
```

#### Update Application Status

```http
PUT /api/v1/applications/{application_id}
Content-Type: application/json

{
  "status": "interviewing",
  "notes": "Phone interview scheduled for next week"
}
```

**Response:**
```json
{
  "id": 1,
  "status": "interviewing",
  "last_updated": "2025-11-07T10:00:00Z",
  "message": "Application updated successfully"
}
```

### AI Services

#### Generate Resume

```http
POST /api/v1/ai/resume/generate
Content-Type: application/json

{
  "job_id": 123,
  "template": "modern",
  "include_skills": true,
  "highlight_experience": true
}
```

**Response:**
```json
{
  "resume_url": "/uploads/resumes/user_1_job_123.pdf",
  "preview_text": "MOATASIM FAROOQUE\nSenior Data Scientist...",
  "generated_at": "2025-11-07T10:00:00Z"
}
```

#### Generate Cover Letter

```http
POST /api/v1/ai/cover-letter/generate
Content-Type: application/json

{
  "job_id": 123,
  "tone": "professional",
  "length": "medium"
}
```

**Response:**
```json
{
  "cover_letter": "Dear Hiring Manager,\n\nI am writing to express...",
  "word_count": 350,
  "generated_at": "2025-11-07T10:00:00Z"
}
```

#### Analyze Job Match

```http
POST /api/v1/ai/analyze-match
Content-Type: application/json

{
  "job_id": 123,
  "user_id": 1
}
```

**Response:**
```json
{
  "match_score": 0.85,
  "strengths": [
    "Strong Python skills",
    "Relevant ML experience"
  ],
  "gaps": [
    "Limited cloud experience",
    "No Scala knowledge"
  ],
  "recommendations": [
    "Highlight your PyTorch projects",
    "Mention AWS certification pursuit"
  ]
}
```

### User Profile

#### Get User Profile

```http
GET /api/v1/users/me
```

**Response:**
```json
{
  "id": 1,
  "email": "moatasim@example.com",
  "full_name": "Moatasim Farooque",
  "skills": ["Python", "Machine Learning", "SQL"],
  "experience_years": 5,
  "education": [
    {
      "degree": "Master's in Computer Science",
      "institution": "University Name",
      "year": 2018
    }
  ],
  "preferences": {
    "locations": ["Berlin", "Munich"],
    "job_types": ["Full-time"],
    "remote": true
  }
}
```

#### Update User Profile

```http
PUT /api/v1/users/me
Content-Type: application/json

{
  "full_name": "Moatasim Farooque",
  "skills": ["Python", "Machine Learning", "Deep Learning"],
  "preferences": {
    "locations": ["Berlin", "Amsterdam"],
    "remote": true
  }
}
```

**Response:**
```json
{
  "id": 1,
  "message": "Profile updated successfully",
  "updated_at": "2025-11-07T10:00:00Z"
}
```

### Analytics

#### Get Application Statistics

```http
GET /api/v1/analytics/applications/stats
```

**Response:**
```json
{
  "total_applications": 50,
  "by_status": {
    "pending": 5,
    "applied": 20,
    "interviewing": 10,
    "rejected": 12,
    "accepted": 3
  },
  "response_rate": 0.60,
  "average_response_time_days": 7.5,
  "success_rate": 0.06
}
```

#### Get Job Market Insights

```http
GET /api/v1/analytics/market/insights?location=Berlin
```

**Response:**
```json
{
  "total_jobs": 1500,
  "trending_skills": [
    {"skill": "Python", "count": 890},
    {"skill": "Machine Learning", "count": 650}
  ],
  "average_salary": 75000,
  "top_companies": [
    {"company": "TechCorp", "job_count": 45}
  ],
  "growth_trend": "increasing"
}
```

### Job Scraping

#### Trigger Manual Scrape

```http
POST /api/v1/scraping/trigger
Content-Type: application/json

{
  "sources": ["linkedin", "indeed"],
  "location": "Berlin",
  "keywords": ["data scientist"]
}
```

**Response:**
```json
{
  "task_id": "abc-123-def-456",
  "status": "queued",
  "message": "Scraping task queued successfully"
}
```

#### Get Scraping Status

```http
GET /api/v1/scraping/status/{task_id}
```

**Response:**
```json
{
  "task_id": "abc-123-def-456",
  "status": "completed",
  "jobs_scraped": 150,
  "sources_completed": ["linkedin", "indeed"],
  "started_at": "2025-11-07T10:00:00Z",
  "completed_at": "2025-11-07T10:15:00Z"
}
```

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "timestamp": "2025-11-07T10:00:00Z"
}
```

### Error Codes

- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `409` - Conflict (duplicate resource)
- `422` - Unprocessable Entity (semantic errors)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error
- `503` - Service Unavailable

## Rate Limiting

- **Default**: 60 requests per minute per IP
- **Authenticated**: 120 requests per minute per user
- **Scraping**: 10 requests per minute

**Headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699358400
```

## Pagination

All list endpoints support pagination:

```http
GET /api/v1/jobs?skip=20&limit=10
```

**Response includes:**
```json
{
  "items": [...],
  "total": 150,
  "skip": 20,
  "limit": 10,
  "has_more": true
}
```

## Filtering & Sorting

```http
GET /api/v1/jobs?sort_by=scraped_at&order=desc&filter[location]=Berlin
```

**Supported:**
- `sort_by`: Field to sort by
- `order`: `asc` or `desc`
- `filter[field]`: Filter by field value

## Webhooks (Future Feature)

Subscribe to events:

```http
POST /api/v1/webhooks
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["application.created", "job.matched"],
  "secret": "webhook_secret_key"
}
```

## WebSocket (Future Feature)

Real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/notifications');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New notification:', data);
};
```

## Code Examples

### Python

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={'email': 'user@example.com', 'password': 'password123'}
)
token = response.json()['access_token']

# Get jobs
headers = {'Authorization': f'Bearer {token}'}
jobs = requests.get(
    'http://localhost:8000/api/v1/jobs',
    headers=headers,
    params={'location': 'Berlin', 'limit': 10}
)
print(jobs.json())
```

### JavaScript/TypeScript

```typescript
// Login
const login = async () => {
  const response = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'user@example.com', password: 'password123' })
  });
  const { access_token } = await response.json();
  return access_token;
};

// Get jobs
const getJobs = async (token: string) => {
  const response = await fetch('http://localhost:8000/api/v1/jobs?location=Berlin', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};
```

### cURL

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Get jobs
curl http://localhost:8000/api/v1/jobs?location=Berlin \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Interactive Documentation

Visit these URLs when the backend is running:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **OpenAPI Schema**: <http://localhost:8000/openapi.json>

## Next Steps

- [Installation Guide](../setup/INSTALLATION.md) - Set up the API
- [Development Guide](../development/DEVELOPMENT.md) - Develop with the API
- [Architecture](../architecture/ARCHITECTURE.md) - Understand the system
- [Troubleshooting](../troubleshooting/COMMON_ISSUES.md) - Common API issues
