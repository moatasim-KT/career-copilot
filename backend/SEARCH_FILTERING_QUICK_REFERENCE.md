# Search and Filtering Quick Reference

## Job Search Examples

### Basic Search
```bash
# Search by keyword
curl "http://localhost:8000/api/v1/jobs/search?query=Python"

# Search by company
curl "http://localhost:8000/api/v1/jobs/search?query=Google"
```

### Location Filtering
```bash
# Find jobs in San Francisco
curl "http://localhost:8000/api/v1/jobs/search?location=San%20Francisco"

# Find remote jobs
curl "http://localhost:8000/api/v1/jobs/search?remote_only=true"
```

### Salary Filtering
```bash
# Jobs with minimum salary of $100k
curl "http://localhost:8000/api/v1/jobs/search?min_salary=100000"

# Jobs with salary range $80k-$120k
curl "http://localhost:8000/api/v1/jobs/search?min_salary=80000&max_salary=120000"
```

### Tech Stack Filtering
```bash
# Jobs requiring Python
curl "http://localhost:8000/api/v1/jobs/search?tech_stack=Python"

# Jobs requiring Python OR React
curl "http://localhost:8000/api/v1/jobs/search?tech_stack=Python&tech_stack=React"
```

### Combined Filters
```bash
# Remote Python jobs in SF paying $100k+
curl "http://localhost:8000/api/v1/jobs/search?query=Python&location=San%20Francisco&remote_only=true&min_salary=100000"
```

### Pagination
```bash
# First page (20 results)
curl "http://localhost:8000/api/v1/jobs/search?limit=20&skip=0"

# Second page
curl "http://localhost:8000/api/v1/jobs/search?limit=20&skip=20"
```

## Application Search Examples

### Basic Search
```bash
# Search by job title
curl "http://localhost:8000/api/v1/applications/search?query=Developer"

# Search by company
curl "http://localhost:8000/api/v1/applications/search?query=Google"
```

### Status Filtering
```bash
# Get all applications in interview stage
curl "http://localhost:8000/api/v1/applications/search?status=interview"

# Get all applied applications
curl "http://localhost:8000/api/v1/applications/search?status=applied"
```

### Date Range Filtering
```bash
# Applications from last month
curl "http://localhost:8000/api/v1/applications/search?start_date=2025-10-01&end_date=2025-10-31"

# Applications from this year
curl "http://localhost:8000/api/v1/applications/search?start_date=2025-01-01"
```

### Sorting
```bash
# Sort by created date (newest first)
curl "http://localhost:8000/api/v1/applications/search?sort_by=created_at&sort_order=desc"

# Sort by applied date (oldest first)
curl "http://localhost:8000/api/v1/applications/search?sort_by=applied_date&sort_order=asc"

# Sort by status
curl "http://localhost:8000/api/v1/applications/search?sort_by=status&sort_order=asc"
```

### Combined Filters
```bash
# Interview stage applications from last 30 days, sorted by date
curl "http://localhost:8000/api/v1/applications/search?status=interview&start_date=2025-10-11&sort_by=created_at&sort_order=desc"
```

## Python/JavaScript Examples

### Python (using requests)
```python
import requests

# Job search
response = requests.get(
    "http://localhost:8000/api/v1/jobs/search",
    params={
        "query": "Python Developer",
        "location": "San Francisco",
        "remote_only": True,
        "min_salary": 100000,
        "tech_stack": ["Python", "Django", "AWS"],
        "limit": 20
    }
)
jobs = response.json()

# Application search
response = requests.get(
    "http://localhost:8000/api/v1/applications/search",
    params={
        "status": "interview",
        "start_date": "2025-10-01",
        "sort_by": "created_at",
        "sort_order": "desc"
    }
)
applications = response.json()
```

### JavaScript (using fetch)
```javascript
// Job search
const jobParams = new URLSearchParams({
    query: 'Python Developer',
    location: 'San Francisco',
    remote_only: true,
    min_salary: 100000,
    limit: 20
});
// Add multiple tech_stack values
jobParams.append('tech_stack', 'Python');
jobParams.append('tech_stack', 'Django');

const jobsResponse = await fetch(`/api/v1/jobs/search?${jobParams}`);
const jobs = await jobsResponse.json();

// Application search
const appParams = new URLSearchParams({
    status: 'interview',
    start_date: '2025-10-01',
    sort_by: 'created_at',
    sort_order: 'desc'
});

const appsResponse = await fetch(`/api/v1/applications/search?${appParams}`);
const applications = await appsResponse.json();
```

## Cache Control

### Using Cache (Default)
```bash
# Results will be cached for 15 minutes (jobs) or 5 minutes (applications)
curl "http://localhost:8000/api/v1/jobs/search?query=Python"
```

### Bypassing Cache
```bash
# Force fresh query, bypass cache
curl "http://localhost:8000/api/v1/jobs/search?query=Python&use_cache=false"
```

## Common Use Cases

### 1. Find Remote Python Jobs Paying $100k+
```bash
curl "http://localhost:8000/api/v1/jobs/search?query=Python&remote_only=true&min_salary=100000"
```

### 2. Get All Interview Stage Applications
```bash
curl "http://localhost:8000/api/v1/applications/search?status=interview&sort_by=interview_date&sort_order=asc"
```

### 3. Find Full-Time Jobs in Tech Hub Cities
```bash
# San Francisco
curl "http://localhost:8000/api/v1/jobs/search?location=San%20Francisco&job_type=full-time"

# New York
curl "http://localhost:8000/api/v1/jobs/search?location=New%20York&job_type=full-time"
```

### 4. Track Application Progress This Month
```bash
curl "http://localhost:8000/api/v1/applications/search?start_date=2025-11-01&end_date=2025-11-30&sort_by=created_at&sort_order=desc"
```

### 5. Find Jobs Matching Multiple Skills
```bash
curl "http://localhost:8000/api/v1/jobs/search?tech_stack=Python&tech_stack=React&tech_stack=AWS"
```

## Response Format

### Job Search Response
```json
[
  {
    "id": 1,
    "user_id": 1,
    "company": "TechCorp",
    "title": "Senior Python Developer",
    "location": "San Francisco, CA",
    "description": "Build scalable backend systems",
    "requirements": "5+ years Python experience",
    "responsibilities": "Design and implement APIs",
    "salary_min": 120000,
    "salary_max": 150000,
    "job_type": "full-time",
    "remote_option": "remote",
    "tech_stack": ["Python", "Django", "PostgreSQL", "AWS"],
    "documents_required": ["resume", "cover_letter"],
    "application_url": "https://techcorp.com/apply",
    "source": "manual",
    "status": "not_applied",
    "date_applied": null,
    "notes": "Great company culture",
    "created_at": "2025-11-01T10:00:00",
    "updated_at": "2025-11-01T10:00:00",
    "currency": "USD"
  }
]
```

### Application Search Response
```json
[
  {
    "id": 1,
    "user_id": 1,
    "job_id": 1,
    "status": "interview",
    "applied_date": "2025-11-01",
    "response_date": "2025-11-05",
    "interview_date": "2025-11-10T14:00:00",
    "offer_date": null,
    "notes": "Phone screen went well",
    "interview_feedback": {
      "questions": ["Tell me about yourself", "Explain your experience with Python"],
      "skill_areas": ["Python", "System Design"],
      "notes": "Strong technical skills"
    },
    "follow_up_date": "2025-11-15",
    "created_at": "2025-11-01T09:00:00",
    "updated_at": "2025-11-05T15:30:00"
  }
]
```

## Error Responses

### Invalid Sort Field
```json
{
  "detail": "Invalid sort_by field. Must be one of: created_at, updated_at, applied_date, status"
}
```

### Invalid Date Format
```json
{
  "detail": "Invalid start_date format. Use YYYY-MM-DD"
}
```

## Performance Tips

1. **Use Pagination**: Always use `limit` to avoid large result sets
2. **Enable Caching**: Leave `use_cache=true` for repeated queries
3. **Specific Filters**: More specific filters = faster queries
4. **Index-Friendly Queries**: Location, status, and date filters use indexes
5. **Avoid Wildcards**: Specific search terms are faster than broad searches

## Database Indexes

The following indexes optimize search performance:

### Job Indexes
- `ix_jobs_user_location` - Location searches
- `ix_jobs_user_remote` - Remote job filtering
- `ix_jobs_user_type` - Job type filtering
- `ix_jobs_user_salary` - Salary range queries

### Application Indexes
- `ix_applications_user_status` - Status filtering
- `ix_applications_user_created` - Date range queries
- `ix_applications_user_applied` - Applied date sorting
- `ix_applications_job_user` - Job-application joins

## Troubleshooting

### Slow Queries
1. Check if indexes are created: `alembic current`
2. Verify cache is enabled: Check Redis connection
3. Use more specific filters to reduce result set
4. Consider pagination for large datasets

### Cache Issues
1. Verify Redis is running: `redis-cli ping`
2. Check cache service logs
3. Try bypassing cache: `use_cache=false`
4. Clear cache manually if needed

### No Results
1. Check filter combinations aren't too restrictive
2. Verify data exists in database
3. Check date format (YYYY-MM-DD)
4. Ensure user has access to the data
