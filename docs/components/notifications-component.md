# Notifications Component Reference

## Overview

The Notifications component provides comprehensive notification management including real-time WebSocket delivery, scheduled notifications, email integration, and user preference management. It supports multiple notification types, priorities, and delivery channels.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Layer     │    │  Service Layer   │    │  Data Layer     │
│                 │    │                  │    │                 │
│ • notifications │◄──►│ • Notification   │◄──►│ • notification  │
│ • websocket     │    │   Service        │    │ • notification_ │
│ • email         │    │ • WebSocket      │    │   preferences   │
│                 │    │   Service        │    │                 │
│                 │    │ • Scheduled      │    │                 │
│                 │    │   Service        │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              ▲
                              │
                       ┌─────────────────┐
                       │   Delivery      │
                       │   Channels      │
                       │                 │
                       │ • WebSocket     │
                       │ • Email         │
                       │ • Push          │
                       │ • In-App        │
                       └─────────────────┘
```

## Core Files

### API Layer
- **Notifications API**: [[../../backend/app/api/v1/notifications.py|notifications.py]] - Notification management endpoints
- **WebSocket API**: [[../../backend/app/api/v1/websocket.py|websocket.py]] - Real-time WebSocket connections
- **Email API**: [[../../backend/app/api/v1/email.py|email.py]] - Email notification endpoints

### Service Layer
- **Notification Service**: [[../../backend/app/services/notification_service.py|notification_service.py]] - Core notification creation and management
- **WebSocket Service**: [[../../backend/app/services/websocket_notification_service.py|websocket_notification_service.py]] - Real-time WebSocket delivery
- **Scheduled Service**: [[../../backend/app/services/scheduled_notification_service.py|scheduled_notification_service.py]] - Morning/evening briefings
- **Email Service**: [[../../backend/app/services/email_service.py|email_service.py]] - Email composition and sending

### Data Layer
- **Notification Model**: [[../../backend/app/models/notification.py|notification.py]] - Notification storage and preferences
- **WebSocket Manager**: [[../../backend/app/core/websocket_manager.py|websocket_manager.py]] - Connection management

## Database Schema

### Notifications Table
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR NOT NULL,  -- NotificationType enum
    priority VARCHAR DEFAULT 'medium',  -- NotificationPriority enum
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP NULL,
    data JSONB DEFAULT '{}',  -- Additional context data
    action_url VARCHAR(500) NULL,  -- Click action URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,  -- Optional expiration

    INDEX idx_notifications_user_id (user_id),
    INDEX idx_notifications_type (type),
    INDEX idx_notifications_is_read (is_read),
    INDEX idx_notifications_created_at (created_at)
);
```

### Notification Preferences Table
```sql
CREATE TABLE notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,

    -- Channel preferences
    email_enabled BOOLEAN DEFAULT true,
    push_enabled BOOLEAN DEFAULT true,
    in_app_enabled BOOLEAN DEFAULT true,

    -- Event type preferences
    job_status_change_enabled BOOLEAN DEFAULT true,
    application_update_enabled BOOLEAN DEFAULT true,
    interview_reminder_enabled BOOLEAN DEFAULT true,
    new_job_match_enabled BOOLEAN DEFAULT true,
    application_deadline_enabled BOOLEAN DEFAULT true,
    skill_gap_report_enabled BOOLEAN DEFAULT true,
    system_announcement_enabled BOOLEAN DEFAULT true,
    morning_briefing_enabled BOOLEAN DEFAULT true,
    evening_update_enabled BOOLEAN DEFAULT true,

    -- Timing preferences
    morning_briefing_time VARCHAR(5) DEFAULT '08:00',  -- HH:MM
    evening_update_time VARCHAR(5) DEFAULT '18:00',
    quiet_hours_start VARCHAR(5) NULL,
    quiet_hours_end VARCHAR(5) NULL,

    -- Frequency preferences
    digest_frequency VARCHAR(20) DEFAULT 'daily',  -- daily, weekly, never

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Notification Types

### Event-Driven Notifications
```python
# From notification.py
class NotificationType(str, Enum):
    JOB_STATUS_CHANGE = "job_status_change"        # Job status updates
    APPLICATION_UPDATE = "application_update"      # Application progress
    INTERVIEW_REMINDER = "interview_reminder"      # Interview scheduling
    NEW_JOB_MATCH = "new_job_match"               # New job recommendations
    APPLICATION_DEADLINE = "application_deadline"  # Deadline reminders
    SKILL_GAP_REPORT = "skill_gap_report"         # Skill analysis reports
    SYSTEM_ANNOUNCEMENT = "system_announcement"   # System updates
    MORNING_BRIEFING = "morning_briefing"         # Daily morning summary
    EVENING_UPDATE = "evening_update"            # Daily evening recap
```

### Priority Levels
```python
class NotificationPriority(str, Enum):
    LOW = "low"          # General information
    MEDIUM = "medium"    # Important updates
    HIGH = "high"        # Time-sensitive actions
    URGENT = "urgent"    # Immediate attention required
```

## Key Services

### Notification Service
```python
# From notification_service.py
class NotificationService:
    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> Notification:
        """Create notification and deliver via WebSocket"""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
            action_url=action_url,
            expires_at=expires_at,
        )

        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        # Real-time delivery via WebSocket
        await WebSocketNotificationService.send_notification_to_user(
            user_id, notification
        )

        return notification
```

### WebSocket Notification Service
```python
# From websocket_notification_service.py
class WebSocketNotificationService:
    def __init__(self):
        self.manager = websocket_manager
        self._heartbeat_tasks: Dict[int, asyncio.Task] = {}

    async def authenticate_websocket(
        self, websocket: WebSocket, token: Optional[str], db: AsyncSession
    ) -> Optional[int]:
        """Authenticate WebSocket connection with JWT token"""
        if not token:
            return None

        try:
            # Validate JWT token
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            user_id = payload.get("sub")
            if user_id:
                # Verify user exists
                user = await UserRepository.get_by_id(db, int(user_id))
                return user.id if user else None
        except JWTError:
            return None

        return None

    async def handle_websocket_connection(
        self, websocket: WebSocket, user_id: int, db: AsyncSession
    ):
        """Handle WebSocket connection lifecycle"""
        await self.manager.connect(user_id, websocket)

        try:
            # Send queued offline notifications
            await self._send_offline_notifications(user_id)

            # Start heartbeat
            heartbeat_task = asyncio.create_task(
                self._send_heartbeat(user_id)
            )
            self._heartbeat_tasks[user_id] = heartbeat_task

            # Listen for messages
            while True:
                data = await websocket.receive_text()
                await self._handle_websocket_message(user_id, data, db)

        except WebSocketDisconnect:
            await self._handle_disconnect(user_id)
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            await self._handle_disconnect(user_id)
```

### Scheduled Notification Service
```python
# From scheduled_notification_service.py
class ScheduledNotificationService:
    def __init__(self, db: Session):
        self.email_service = None  # Lazy-loaded
        self._recommendation_service = None

    async def send_morning_briefing(self, user_id: int, db: Session):
        """Generate and send morning job briefing"""
        # Get user's preferences
        prefs = await self._get_user_preferences(user_id, db)
        if not prefs.morning_briefing_enabled:
            return

        # Generate briefing content
        briefing_data = await self._generate_morning_briefing(user_id, db)

        # Send via email
        await self._get_email_service().send_morning_briefing(
            user_id=user_id,
            briefing_data=briefing_data,
            scheduled_time=prefs.morning_briefing_time
        )

    async def send_evening_update(self, user_id: int, db: Session):
        """Generate and send evening application recap"""
        prefs = await self._get_user_preferences(user_id, db)
        if not prefs.evening_update_enabled:
            return

        # Generate evening update
        update_data = await self._generate_evening_update(user_id, db)

        # Send via email
        await self._get_email_service().send_evening_update(
            user_id=user_id,
            update_data=update_data,
            scheduled_time=prefs.evening_update_time
        )
```

## API Endpoints

| Method | Endpoint | Description | Implementation |
|--------|----------|-------------|----------------|
| GET | `/api/v1/notifications` | List user notifications | [[../../backend/app/api/v1/notifications.py#get_notifications\|get_notifications()]] |
| POST | `/api/v1/notifications` | Create notification | [[../../backend/app/api/v1/notifications.py#create_notification\|create_notification()]] |
| PUT | `/api/v1/notifications/{id}/read` | Mark as read | [[../../backend/app/api/v1/notifications.py#mark_notification_read\|mark_notification_read()]] |
| DELETE | `/api/v1/notifications/{id}` | Delete notification | [[../../backend/app/api/v1/notifications.py#delete_notification\|delete_notification()]] |
| GET | `/api/v1/notifications/preferences` | Get preferences | [[../../backend/app/api/v1/notifications.py#get_notification_preferences\|get_notification_preferences()]] |
| PUT | `/api/v1/notifications/preferences` | Update preferences | [[../../backend/app/api/v1/notifications.py#update_notification_preferences\|update_notification_preferences()]] |
| WebSocket | `/api/v1/ws/notifications` | Real-time connection | [[../../backend/app/api/v1/websocket.py#websocket_notifications\|websocket_notifications()]] |

## WebSocket Implementation

### Connection Management
```python
# WebSocket manager handles connections
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """Add WebSocket connection for user"""
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to all user connections"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to user {user_id}: {e}")
```

### Real-time Notification Delivery
```python
# Send notification via WebSocket
async def send_notification_to_user(user_id: int, notification: Notification):
    """Deliver notification via WebSocket if user is connected"""
    message = {
        "type": "notification",
        "data": {
            "id": notification.id,
            "type": notification.type.value,
            "priority": notification.priority.value,
            "title": notification.title,
            "message": notification.message,
            "data": notification.data,
            "action_url": notification.action_url,
            "created_at": notification.created_at.isoformat()
        }
    }

    # Send to WebSocket connections
    await websocket_manager.send_to_user(user_id, message)

    # Queue for offline delivery if needed
    if user_id not in websocket_manager.active_connections:
        await queue_offline_notification(user_id, message)
```

### Heartbeat Mechanism
```python
# Maintain connection health
async def _send_heartbeat(self, user_id: int):
    """Send periodic heartbeat to maintain connection"""
    while True:
        try:
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)
            await self.manager.send_to_user(user_id, {"type": "heartbeat"})
        except Exception as e:
            logger.error(f"Heartbeat failed for user {user_id}: {e}")
            break
```

## Email Integration

### Email Service Integration
```python
# From email_service.py
class EmailService:
    async def send_notification_email(
        self,
        user_id: int,
        notification: Notification,
        template: str = "notification"
    ):
        """Send notification via email"""
        user = await UserRepository.get_by_id(self.db, user_id)

        # Render email template
        html_content = self._render_template(
            template,
            notification=notification,
            user=user
        )

        # Send email
        await self._send_email(
            to_email=user.email,
            subject=notification.title,
            html_content=html_content
        )
```

### Scheduled Email Campaigns
```python
# Morning briefing email
async def send_morning_briefing(self, user_id: int, briefing_data: dict):
    """Send daily morning job briefing"""
    user = await UserRepository.get_by_id(self.db, user_id)

    # Generate briefing content
    jobs_count = briefing_data.get("new_jobs_count", 0)
    applications_count = briefing_data.get("pending_applications", 0)

    subject = f"Good morning! {jobs_count} new jobs match your profile"

    html_content = self._render_template(
        "morning_briefing",
        user=user,
        jobs_count=jobs_count,
        applications_count=applications_count,
        top_jobs=briefing_data.get("top_jobs", []),
        briefing_data=briefing_data
    )

    await self._send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content
    )
```

## User Preferences Management

### Preference Storage
```python
# User notification preferences
@dataclass
class UserNotificationPreferences:
    email_enabled: bool = True
    push_enabled: bool = True
    in_app_enabled: bool = True

    # Event-specific preferences
    job_status_change_enabled: bool = True
    application_update_enabled: bool = True
    interview_reminder_enabled: bool = True
    new_job_match_enabled: bool = True
    application_deadline_enabled: bool = True
    skill_gap_report_enabled: bool = True
    system_announcement_enabled: bool = True
    morning_briefing_enabled: bool = True
    evening_update_enabled: bool = True

    # Timing preferences
    morning_briefing_time: str = "08:00"
    evening_update_time: str = "18:00"
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None

    # Frequency settings
    digest_frequency: str = "daily"  # daily, weekly, never
```

### Preference Validation
```python
def validate_preferences(prefs: UserNotificationPreferences) -> bool:
    """Validate notification preferences"""
    # Time format validation
    time_fields = ['morning_briefing_time', 'evening_update_time',
                   'quiet_hours_start', 'quiet_hours_end']

    for field in time_fields:
        time_str = getattr(prefs, field)
        if time_str and not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_str):
            return False

    # Frequency validation
    if prefs.digest_frequency not in ['daily', 'weekly', 'never']:
        return False

    # Quiet hours logic
    if prefs.quiet_hours_start and not prefs.quiet_hours_end:
        return False
    if prefs.quiet_hours_end and not prefs.quiet_hours_start:
        return False

    return True
```

## Notification Templates

### Template System
```python
# Notification templates
NOTIFICATION_TEMPLATES = {
    "job_status_change": {
        "title": "Job Status Update",
        "template": "Your application for {job_title} at {company} has been {status}.",
        "action_url": "/applications/{application_id}"
    },
    "interview_reminder": {
        "title": "Interview Reminder",
        "template": "You have an interview scheduled for {job_title} at {company} on {interview_date}.",
        "action_url": "/applications/{application_id}"
    },
    "new_job_match": {
        "title": "New Job Match Found",
        "template": "We found {count} new jobs that match your profile.",
        "action_url": "/jobs/matches"
    }
}

def render_notification_template(
    template_key: str,
    **context
) -> Dict[str, str]:
    """Render notification template with context"""
    template = NOTIFICATION_TEMPLATES.get(template_key)
    if not template:
        return {}

    return {
        "title": template["title"],
        "message": template["template"].format(**context),
        "action_url": template["action_url"].format(**context) if template.get("action_url") else None
    }
```

## Offline Notification Queue

### Queue Management
```python
# Handle offline notifications
class OfflineNotificationQueue:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.queues: Dict[int, List[dict]] = {}

    async def add_notification(self, user_id: int, notification: dict):
        """Add notification to offline queue"""
        if user_id not in self.queues:
            self.queues[user_id] = []

        queue = self.queues[user_id]
        queue.append({
            **notification,
            "queued_at": datetime.now(UTC).isoformat()
        })

        # Maintain max size
        if len(queue) > self.max_size:
            queue.pop(0)  # Remove oldest

    async def get_notifications(self, user_id: int) -> List[dict]:
        """Get queued notifications for user"""
        return self.queues.get(user_id, [])

    async def clear_notifications(self, user_id: int):
        """Clear queued notifications after delivery"""
        if user_id in self.queues:
            self.queues[user_id].clear()
```

## Testing

### WebSocket Testing
```python
# Test WebSocket notification delivery
async def test_websocket_notifications(client: TestClient, db: AsyncSession):
    # Connect WebSocket
    with client.websocket_connect("/api/v1/ws/notifications?token=test_token") as websocket:
        # Create notification
        notification = await NotificationService.create_notification(
            db=db,
            user_id=1,
            notification_type=NotificationType.JOB_STATUS_CHANGE,
            title="Test Notification",
            message="Test message"
        )

        # Receive notification via WebSocket
        data = websocket.receive_json()
        assert data["type"] == "notification"
        assert data["data"]["title"] == "Test Notification"
```

### Email Testing
```python
# Test email notification sending
async def test_email_notifications(db: AsyncSession):
    email_service = EmailService()

    # Mock email sending
    with patch.object(email_service, '_send_email') as mock_send:
        await email_service.send_notification_email(
            user_id=1,
            notification=test_notification
        )

        # Verify email was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert "test@example.com" in call_args.kwargs["to_email"]
        assert "Test Notification" in call_args.kwargs["subject"]
```

### Preference Testing
```python
# Test notification preferences
def test_notification_preferences_validation():
    # Valid preferences
    valid_prefs = UserNotificationPreferences(
        morning_briefing_time="08:30",
        evening_update_time="18:00",
        digest_frequency="daily"
    )
    assert validate_preferences(valid_prefs)

    # Invalid time format
    invalid_prefs = UserNotificationPreferences(
        morning_briefing_time="25:00"  # Invalid hour
    )
    assert not validate_preferences(invalid_prefs)
```

**Test Files:**
- [[../../backend/tests/test_notifications.py|test_notifications.py]] - Notification CRUD tests
- [[../../backend/tests/test_websocket_notifications.py|test_websocket_notifications.py]] - WebSocket delivery tests
- [[../../backend/tests/test_email_notifications.py|test_email_notifications.py]] - Email integration tests

## Performance Considerations

### Connection Scaling
- **Connection Pooling**: Limit concurrent WebSocket connections per user
- **Message Batching**: Group multiple notifications into single WebSocket messages
- **Connection Cleanup**: Automatic cleanup of stale connections

### Database Optimization
- **Index Strategy**: Composite indexes on `(user_id, is_read, created_at)`
- **Partitioning**: Partition notifications by month for large datasets
- **Archiving**: Move old notifications to archive tables

### Email Delivery
- **Rate Limiting**: Prevent email spam with rate limits per user/hour
- **Template Caching**: Cache compiled email templates
- **Queue Management**: Use Celery for asynchronous email sending

## Monitoring & Analytics

### Delivery Metrics
- **Delivery Rate**: Percentage of notifications successfully delivered
- **Open Rate**: Email open tracking for email notifications
- **Click Rate**: Action URL click tracking
- **Real-time Latency**: WebSocket message delivery time

### User Engagement
- **Read Rate**: Percentage of notifications marked as read
- **Interaction Rate**: User interactions with notifications
- **Preference Changes**: Track preference update frequency

### System Health
- **Connection Count**: Active WebSocket connections
- **Queue Depth**: Offline notification queue sizes
- **Error Rates**: Failed delivery attempts

## Related Components

- **Users**: [[users-component|Users Component]] - User management and preferences
- **Applications**: [[applications-component|Applications Component]] - Application status change triggers
- **Jobs**: [[jobs-component|Jobs Component]] - Job matching notifications
- **Analytics**: [[analytics-component|Analytics Component]] - Notification event tracking

## Common Patterns

### Notification Creation Pattern
```python
async def create_status_change_notification(
    db: AsyncSession,
    application: Application,
    old_status: str,
    new_status: str
):
    """Create notification for application status change"""
    # Build context data
    context = {
        "application_id": application.id,
        "job_id": application.job_id,
        "old_status": old_status,
        "new_status": new_status,
        "company": application.job.company,
        "job_title": application.job.title
    }

    # Create notification
    await NotificationService.create_notification(
        db=db,
        user_id=application.user_id,
        notification_type=NotificationType.APPLICATION_UPDATE,
        title=f"Application Status Changed",
        message=f"Your application for {application.job.title} at {application.job.company} changed from {old_status} to {new_status}",
        priority=NotificationPriority.HIGH,
        data=context,
        action_url=f"/applications/{application.id}"
    )
```

### Preference-Aware Delivery
```python
async def send_notification_with_preferences(
    db: AsyncSession,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    message: str,
    **kwargs
):
    """Send notification respecting user preferences"""
    # Check user preferences
    prefs = await NotificationPreferencesRepository.get_by_user_id(db, user_id)

    # Check if notification type is enabled
    type_enabled = getattr(prefs, f"{notification_type.value}_enabled", True)
    if not type_enabled:
        return

    # Check quiet hours
    if await _is_in_quiet_hours(prefs):
        # Queue for later delivery
        await queue_offline_notification(user_id, {
            "type": "notification",
            "data": {"title": title, "message": message, **kwargs}
        })
        return

    # Send via enabled channels
    if prefs.in_app_enabled:
        await NotificationService.create_notification(
            db, user_id, notification_type, title, message, **kwargs
        )

    if prefs.email_enabled:
        await EmailService().send_notification_email(user_id, notification, **kwargs)
```

### Scheduled Notification Pattern
```python
async def schedule_daily_notifications(db: Session):
    """Schedule daily morning briefings and evening updates"""
    users = await UserRepository.get_all_active(db)

    for user in users:
        # Check user preferences
        prefs = await NotificationPreferencesRepository.get_by_user_id(db, user.id)

        if prefs.morning_briefing_enabled:
            # Schedule morning briefing
            await ScheduledNotificationService().schedule_morning_briefing(
                user.id, prefs.morning_briefing_time
            )

        if prefs.evening_update_enabled:
            # Schedule evening update
            await ScheduledNotificationService().schedule_evening_update(
                user.id, prefs.evening_update_time
            )
```

---

*See also: [[../api/API.md#notifications|Notifications API Docs]], [[../../backend/app/models/notification.py|Notification Data Models]], [[../../backend/app/services/websocket_notification_service.py|WebSocket Implementation]]*"