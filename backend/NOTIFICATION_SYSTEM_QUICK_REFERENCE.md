# Notification System Quick Reference

## API Endpoints

### List Notifications
```bash
GET /api/v1/notifications?skip=0&limit=50&unread_only=false
```
**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (default: 50, max: 100)
- `unread_only` (bool): Show only unread (default: false)
- `notification_type` (enum): Filter by type
- `priority` (enum): Filter by priority

**Response:**
```json
{
  "notifications": [...],
  "total": 100,
  "unread_count": 15,
  "page": 1,
  "page_size": 50
}
```

### Get Single Notification
```bash
GET /api/v1/notifications/{notification_id}
```

### Mark as Read
```bash
PUT /api/v1/notifications/{notification_id}/read
```

### Mark as Unread
```bash
PUT /api/v1/notifications/{notification_id}/unread
```

### Mark All as Read
```bash
PUT /api/v1/notifications/read-all
```

### Bulk Mark as Read
```bash
POST /api/v1/notifications/mark-read
{
  "notification_ids": [1, 2, 3]
}
```

### Delete Notification
```bash
DELETE /api/v1/notifications/{notification_id}
```

### Bulk Delete
```bash
POST /api/v1/notifications/bulk-delete
{
  "notification_ids": [1, 2, 3]
}
```

### Delete All Notifications
```bash
DELETE /api/v1/notifications/all?read_only=false
```

### Get Statistics
```bash
GET /api/v1/notifications/statistics
```
**Response:**
```json
{
  "total_notifications": 100,
  "unread_notifications": 15,
  "notifications_by_type": {
    "APPLICATION_UPDATE": 30,
    "JOB_STATUS_CHANGE": 25,
    "INTERVIEW_REMINDER": 10
  },
  "notifications_by_priority": {
    "HIGH": 20,
    "MEDIUM": 60,
    "LOW": 20
  },
  "notifications_today": 5,
  "notifications_this_week": 25
}
```

### Get Preferences
```bash
GET /api/v1/notifications/preferences
```

### Update Preferences
```bash
PUT /api/v1/notifications/preferences
{
  "email_enabled": true,
  "push_enabled": false,
  "in_app_enabled": true,
  "application_update_enabled": true,
  "interview_reminder_enabled": true,
  "morning_briefing_time": "08:00",
  "evening_update_time": "18:00",
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "07:00",
  "digest_frequency": "daily"
}
```

### Reset Preferences
```bash
POST /api/v1/notifications/preferences/reset
```

## Notification Types

- `JOB_STATUS_CHANGE` - Job status updated
- `APPLICATION_UPDATE` - Application status changed
- `INTERVIEW_REMINDER` - Upcoming interview
- `NEW_JOB_MATCH` - New matching job found
- `APPLICATION_DEADLINE` - Application deadline approaching
- `SKILL_GAP_REPORT` - Skill gap analysis report
- `SYSTEM_ANNOUNCEMENT` - System-wide announcement
- `MORNING_BRIEFING` - Daily morning briefing
- `EVENING_UPDATE` - Daily evening update

## Priority Levels

- `URGENT` - Requires immediate attention
- `HIGH` - Important, should be addressed soon
- `MEDIUM` - Normal priority
- `LOW` - Informational, can be addressed later

## Service Usage

### Create Notification Programmatically
```python
from app.services.notification_service import notification_service

# Application update
await notification_service.notify_application_update(
    db=db,
    user_id=user.id,
    application_id=app.id,
    job_id=job.id,
    job_title="Software Engineer",
    company="Tech Corp",
    old_status="applied",
    new_status="interview",
    notes="Phone screen scheduled"
)

# Job status change
await notification_service.notify_job_status_change(
    db=db,
    user_id=user.id,
    job_id=job.id,
    job_title="Senior Developer",
    company="StartupXYZ",
    old_status="interested",
    new_status="applied"
)

# Interview reminder
await notification_service.notify_interview_reminder(
    db=db,
    user_id=user.id,
    application_id=app.id,
    job_id=job.id,
    job_title="Backend Engineer",
    company="BigTech Inc",
    interview_date=datetime.utcnow() + timedelta(hours=2),
    interview_type="phone"
)

# New job match
await notification_service.notify_new_job_match(
    db=db,
    user_id=user.id,
    job_id=job.id,
    job_title="Full Stack Developer",
    company="Innovation Labs",
    location="San Francisco, CA",
    match_score=0.95,
    matching_skills=["Python", "React", "PostgreSQL"]
)
```

### Check User Preferences
```python
enabled = await notification_service.check_user_preferences(
    db=db,
    user_id=user.id,
    notification_type=NotificationType.APPLICATION_UPDATE
)

if enabled:
    # Create notification
    pass
```

### Cleanup Operations
```python
# Remove expired notifications
count = await notification_service.cleanup_expired_notifications(db)

# Remove old read notifications (older than 30 days)
count = await notification_service.cleanup_old_read_notifications(db, days_old=30)
```

## Database Models

### Notification
```python
from app.models.notification import Notification, NotificationType, NotificationPriority

notification = Notification(
    user_id=1,
    type=NotificationType.APPLICATION_UPDATE,
    priority=NotificationPriority.HIGH,
    title="Application Updated",
    message="Your application status has changed",
    data={"job_id": 123, "new_status": "interview"},
    action_url="/applications/456",
    expires_at=datetime.utcnow() + timedelta(days=7)
)
```

### NotificationPreferences
```python
from app.models.notification import NotificationPreferences

preferences = NotificationPreferences(
    user_id=1,
    email_enabled=True,
    push_enabled=False,
    in_app_enabled=True,
    application_update_enabled=True,
    morning_briefing_time="08:00",
    digest_frequency="daily"
)
```

## Common Queries

### Get Unread Notifications
```python
from sqlalchemy import select, and_
from app.models.notification import Notification

query = select(Notification).where(
    and_(
        Notification.user_id == user_id,
        Notification.is_read == False
    )
).order_by(Notification.created_at.desc())

result = await db.execute(query)
notifications = result.scalars().all()
```

### Get High Priority Notifications
```python
query = select(Notification).where(
    and_(
        Notification.user_id == user_id,
        Notification.priority == NotificationPriority.HIGH
    )
)
```

### Get Notifications by Type
```python
query = select(Notification).where(
    and_(
        Notification.user_id == user_id,
        Notification.type == NotificationType.INTERVIEW_REMINDER
    )
)
```

## Frontend Integration Examples

### Fetch Notifications
```typescript
// Get unread notifications
const response = await fetch('/api/v1/notifications?unread_only=true&limit=20');
const data = await response.json();

// Display notifications
data.notifications.forEach(notification => {
  console.log(notification.title, notification.message);
});
```

### Mark as Read
```typescript
const markAsRead = async (notificationId: number) => {
  await fetch(`/api/v1/notifications/${notificationId}/read`, {
    method: 'PUT'
  });
};
```

### Update Preferences
```typescript
const updatePreferences = async (preferences: NotificationPreferences) => {
  await fetch('/api/v1/notifications/preferences', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(preferences)
  });
};
```

## Testing

### Run Notification Tests
```bash
cd backend
python -m pytest tests/test_notification_system.py -v
```

### Test Specific Function
```bash
python -m pytest tests/test_notification_system.py::test_create_notification -v
```

## Troubleshooting

### No Notifications Appearing
1. Check user preferences: `GET /api/v1/notifications/preferences`
2. Verify `in_app_enabled` is true
3. Check specific event type is enabled (e.g., `application_update_enabled`)

### Notifications Not Being Created
1. Verify notification service is imported correctly
2. Check database connection
3. Ensure user_id exists in users table
4. Check application logs for errors

### Performance Issues
1. Verify indexes are created: `ix_notifications_user_unread`
2. Use pagination with reasonable limits
3. Consider cleanup of old notifications
4. Check database query performance

## Best Practices

1. **Always check user preferences** before creating notifications
2. **Use appropriate priority levels** based on urgency
3. **Include action URLs** for better user experience
4. **Set expiration dates** for time-sensitive notifications
5. **Cleanup old notifications** regularly to maintain performance
6. **Use bulk operations** when marking multiple notifications as read/deleted
7. **Provide meaningful titles and messages** for better user engagement
8. **Include relevant data** in the data field for context

## Migration

### Apply Migration
```bash
cd backend
alembic upgrade head
```

### Rollback Migration
```bash
alembic downgrade -1
```

### Check Current Version
```bash
alembic current
```

## Configuration

### Environment Variables
No additional environment variables required. Uses existing database connection.

### Default Settings
- Morning briefing time: 08:00
- Evening update time: 18:00
- All notification types: Enabled by default
- All channels: Enabled by default
- Digest frequency: Daily

## Support

For issues or questions:
1. Check the full implementation guide: `NOTIFICATION_SYSTEM_IMPLEMENTATION.md`
2. Review test cases: `tests/test_notification_system.py`
3. Check API documentation: OpenAPI/Swagger UI
4. Review database schema: `alembic/versions/002_add_notification_tables.py`
