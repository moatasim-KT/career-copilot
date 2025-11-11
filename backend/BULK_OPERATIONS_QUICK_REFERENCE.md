# Bulk Operations Quick Reference Guide

## Overview

The bulk operations API provides efficient batch processing for jobs and applications with full transaction support.

## Endpoints

### Bulk Create

#### Create Multiple Jobs
```http
POST /api/v1/bulk/jobs/create
Content-Type: application/json

{
  "jobs": [
    {
      "company": "Tech Corp",
      "title": "Senior Developer",
      "tech_stack": ["Python", "FastAPI"],
      "salary_min": 120000
    }
  ]
}
```

#### Create Multiple Applications
```http
POST /api/v1/bulk/applications/create
Content-Type: application/json

{
  "applications": [
    {
      "job_id": 123,
      "status": "applied",
      "notes": "Applied via website"
    }
  ]
}
```

### Bulk Update

#### Update Multiple Jobs
```http
PUT /api/v1/bulk/jobs/update
Content-Type: application/json

{
  "updates": [
    {
      "id": 123,
      "data": {
        "status": "applied",
        "notes": "Applied today"
      }
    }
  ]
}
```

#### Update Multiple Applications
```http
PUT /api/v1/bulk/applications/update
Content-Type: application/json

{
  "updates": [
    {
      "id": 456,
      "data": {
        "status": "interview",
        "interview_date": "2024-01-20T10:00:00Z"
      }
    }
  ]
}
```

### Bulk Delete

#### Delete Multiple Jobs
```http
DELETE /api/v1/bulk/jobs/delete
Content-Type: application/json

{
  "ids": [123, 124, 125],
  "soft_delete": false
}
```

#### Delete Multiple Applications
```http
DELETE /api/v1/bulk/applications/delete
Content-Type: application/json

{
  "ids": [456, 457, 458],
  "soft_delete": true
}
```

## Response Format

All bulk operations return a consistent response format:

```json
{
  "total": 3,
  "successful": 2,
  "failed": 1,
  "created_ids": [123, 124],
  "errors": [
    {
      "index": 2,
      "id": null,
      "error": "Validation error: Company name is required",
      "details": {
        "job_data": {...}
      }
    }
  ]
}
```

## Key Features

### Transaction Support
- All operations are atomic within a transaction
- Partial success: valid items succeed even if some fail
- Automatic rollback on critical errors

### Validation
- Maximum 1000 items per request
- Ownership validation for all operations
- Duplicate detection for applications
- Foreign key validation

### Soft Delete
- `soft_delete: true` - Marks items as deleted (status = "deleted")
- `soft_delete: false` - Permanently removes items from database
- Default: false (hard delete)

### Automatic Behaviors

**Job Updates:**
- Setting status to "applied" automatically sets `date_applied`
- Updates `updated_at` timestamp

**Application Updates:**
- Setting status to "applied" updates associated job status
- Updates `updated_at` timestamp

**Job Deletion:**
- Hard delete cascades to associated applications
- Soft delete preserves applications

## Error Handling

Errors are reported per item with:
- `index`: Position in the request array
- `id`: Item ID if available
- `error`: Human-readable error message
- `details`: Additional context (optional)

## Limits

- Maximum 1000 items per request
- All items must belong to the authenticated user
- Applications must reference existing jobs

## Python Client Example

```python
import httpx

# Bulk create jobs
response = httpx.post(
    "http://localhost:8002/api/v1/bulk/jobs/create",
    json={
        "jobs": [
            {
                "company": "Tech Corp",
                "title": "Developer",
                "tech_stack": ["Python"]
            },
            {
                "company": "Startup Inc",
                "title": "Engineer",
                "tech_stack": ["JavaScript"]
            }
        ]
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

result = response.json()
print(f"Created {result['successful']} jobs")
print(f"Failed: {result['failed']}")
print(f"IDs: {result['created_ids']}")
```

## JavaScript/TypeScript Client Example

```typescript
// Bulk update applications
const response = await fetch('/api/v1/bulk/applications/update', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    updates: [
      {
        id: 456,
        data: {
          status: 'interview',
          notes: 'Phone screen scheduled'
        }
      },
      {
        id: 457,
        data: {
          status: 'rejected'
        }
      }
    ]
  })
});

const result = await response.json();
console.log(`Updated ${result.successful} applications`);
```

## Best Practices

1. **Batch Size**: Keep batches under 500 items for optimal performance
2. **Error Handling**: Always check the `errors` array in responses
3. **Soft Delete**: Use soft delete for maintaining historical data
4. **Validation**: Validate data client-side before sending
5. **Idempotency**: Check for duplicates before bulk creating applications

## Common Use Cases

### Import Jobs from CSV
1. Parse CSV file
2. Convert to job objects
3. Send in batches of 500 via bulk create

### Update Multiple Job Statuses
1. Get list of job IDs to update
2. Create update objects with new status
3. Send via bulk update

### Clean Up Old Data
1. Get list of job IDs to remove
2. Use soft delete to preserve history
3. Or hard delete to permanently remove

### Migrate Data
1. Export from old system
2. Transform to bulk create format
3. Import via bulk create endpoints

## Testing

Access the interactive API documentation at:
```
http://localhost:8002/docs
```

Navigate to the "bulk-operations" section to test endpoints interactively.
