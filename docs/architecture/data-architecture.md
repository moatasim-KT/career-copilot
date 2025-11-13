# Data Architecture

```mermaid
erDiagram
    %% Core Entities
    User ||--o{ Application : "tracks"
    User ||--o{ Job : "saves"
    User ||--o{ Notification : "receives"
    User ||--o{ Feedback : "provides"
    User ||--o{ Goal : "sets"
    User ||--o{ Milestone : "achieves"
    User ||--o{ Document : "uploads"
    User ||--o{ ContentGeneration : "requests"
    User ||--o{ ResumeUpload : "owns"
    User ||--o{ NotificationPreferences : "configures"

    %% Job Application Flow
    Job ||--o{ Application : "has"
    Application ||--|| Job : "references"

    %% Analytics & Tracking
    User ||--o{ Analytics : "generates"
    Application ||--o{ Analytics : "triggers"

    %% Notifications
    User ||--o{ Notification : "owns"
    Notification ||--|| NotificationPreferences : "respects"

    %% Content & Documents
    User ||--o{ ContentGeneration : "owns"
    User ||--o{ Document : "owns"
    User ||--o{ ResumeUpload : "owns"

    %% Goals & Progress
    User ||--o{ Goal : "defines"
    Goal ||--o{ Milestone : "contains"
    User ||--o{ Milestone : "achieves"

    %% Feedback System
    User ||--o{ Feedback : "submits"
    Application ||--o{ Feedback : "relates"

    %% Detailed Entity Definitions
    User {
        integer id PK
        string email UK
        string username UK
        string hashed_password
        json skills
        json preferred_locations
        string experience_level
        integer daily_application_goal
        boolean is_admin
        boolean prefer_remote_jobs

        %% OAuth fields
        string oauth_provider
        string oauth_id
        string profile_picture_url

        datetime created_at
        datetime updated_at
    }

    Job {
        integer id PK
        string title
        string company
        string location
        text description
        string job_type
        string experience_level
        json requirements
        json benefits
        string source_url
        string source_platform
        string external_id
        datetime posted_date
        datetime scraped_at
        json metadata

        integer user_id FK
        datetime created_at
        datetime updated_at
    }

    Application {
        integer id PK
        integer user_id FK
        integer job_id FK
        string status
        date applied_date
        date response_date
        datetime interview_date
        date offer_date
        text notes
        json interview_feedback
        date follow_up_date

        datetime created_at
        datetime updated_at
    }

    Notification {
        integer id PK
        integer user_id FK
        string type
        string priority
        string title
        text message
        boolean is_read
        datetime read_at
        json data
        string action_url
        datetime expires_at

        datetime created_at
    }

    NotificationPreferences {
        integer id PK
        integer user_id FK UK

        boolean email_enabled
        boolean push_enabled
        boolean in_app_enabled

        boolean job_status_change_enabled
        boolean application_update_enabled
        boolean interview_reminder_enabled
        boolean new_job_match_enabled
        boolean application_deadline_enabled
        boolean skill_gap_report_enabled
        boolean system_announcement_enabled
        boolean morning_briefing_enabled
        boolean evening_update_enabled

        string morning_briefing_time
        string evening_update_time
        string quiet_hours_start
        string quiet_hours_end
        string digest_frequency

        datetime created_at
        datetime updated_at
    }

    Analytics {
        integer id PK
        integer user_id FK
        string type
        json data

        datetime generated_at
    }

    ContentGeneration {
        integer id PK
        integer user_id FK
        string content_type
        string prompt
        text generated_content
        json metadata
        string model_used
        integer tokens_used

        datetime created_at
    }

    Document {
        integer id PK
        integer user_id FK
        string filename
        string file_type
        string storage_path
        integer file_size
        json metadata

        datetime uploaded_at
    }

    ResumeUpload {
        integer id PK
        integer user_id FK
        string filename
        string storage_path
        integer file_size
        json parsed_data
        json metadata

        datetime uploaded_at
    }

    Goal {
        integer id PK
        integer user_id FK
        string title
        text description
        string goal_type
        json target_metrics
        date target_date
        string status
        json progress_data

        datetime created_at
        datetime updated_at
    }

    Milestone {
        integer id PK
        integer user_id FK
        integer goal_id FK
        string title
        text description
        date target_date
        boolean is_completed
        datetime completed_at
        json metadata

        datetime created_at
        datetime updated_at
    }

    Feedback {
        integer id PK
        integer user_id FK
        integer application_id FK
        string feedback_type
        integer rating
        text comments
        json metadata

        datetime created_at
    }
```

## Data Architecture Overview

This diagram illustrates the comprehensive data model for the Career Copilot system, showing relationships between all major entities and their attributes.

### Core Data Relationships

#### User-Centric Design
- **User** is the central entity with cascading relationships to all other data
- All major features (applications, notifications, analytics) are user-scoped
- Supports both single-user and multi-user modes

#### Job Application Flow
- **Job** entities represent scraped job postings from external sources
- **Application** tracks user progress through the job application lifecycle
- One-to-many relationship allows users to apply to multiple jobs

#### Notification System
- **Notification** entities store all user communications
- **NotificationPreferences** control delivery channels and content types
- Supports real-time delivery via WebSocket and scheduled delivery

#### Content Management
- **ContentGeneration** tracks AI-generated content (cover letters, emails)
- **Document** and **ResumeUpload** handle file storage and parsing
- Metadata fields support extensibility and search capabilities

#### Goal Tracking
- **Goal** entities define user objectives (applications per month, etc.)
- **Milestone** provides granular progress tracking
- Progress data enables analytics and reporting

### Database Design Patterns

#### JSON Fields for Flexibility
```sql
-- Flexible metadata storage
skills JSONB DEFAULT '[]'
metadata JSONB DEFAULT '{}'
interview_feedback JSONB NULL
progress_data JSONB DEFAULT '{}'
```

#### Indexing Strategy
```sql
-- Performance indexes
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_notifications_user_id_is_read ON notifications(user_id, is_read);
CREATE INDEX idx_jobs_user_id_created_at ON jobs(user_id, created_at);
CREATE INDEX idx_analytics_user_id_type ON analytics(user_id, type);
```

#### Foreign Key Constraints
```sql
-- Referential integrity
ALTER TABLE applications ADD CONSTRAINT fk_applications_user_id
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE notifications ADD CONSTRAINT fk_notifications_user_id
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

### Data Flow Patterns

#### Write-Heavy Operations
- **Analytics Events**: High-frequency inserts for user behavior tracking
- **Notifications**: Frequent creation for real-time updates
- **Application Updates**: Status changes and note updates

#### Read-Heavy Operations
- **Dashboard Data**: Complex aggregations for metrics display
- **Search Operations**: Full-text search across jobs and applications
- **Analytics Queries**: Time-series data for trend analysis

#### Caching Strategy
```python
# Redis caching patterns
cache_keys = {
    "user_applications": f"apps:{user_id}",
    "user_notifications": f"notifs:{user_id}:unread",
    "job_search": f"jobs:search:{hash(query_params)}",
    "analytics_summary": f"analytics:summary:{user_id}:{date_range}"
}
```

### Data Partitioning Strategy

#### Time-Based Partitioning
```sql
-- Partition analytics by month for performance
CREATE TABLE analytics_y2024m01 PARTITION OF analytics
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Partition notifications by quarter
CREATE TABLE notifications_q1_2024 PARTITION OF notifications
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
```

#### User-Based Partitioning
```sql
-- Partition large tables by user ranges
CREATE TABLE applications_0_100000 PARTITION OF applications
    FOR VALUES FROM (0) TO (100000);

CREATE TABLE applications_100000_200000 PARTITION OF applications
    FOR VALUES FROM (100000) TO (200000);
```

### Data Migration Patterns

#### Schema Evolution
```python
# Alembic migration example
def upgrade():
    # Add new column
    op.add_column('applications', sa.Column('follow_up_date', sa.Date(), nullable=True))

    # Create index
    op.create_index('idx_applications_follow_up_date', 'applications', ['follow_up_date'])

    # Update existing data
    op.execute("""
        UPDATE applications
        SET follow_up_date = applied_date + INTERVAL '7 days'
        WHERE follow_up_date IS NULL
    """)

def downgrade():
    op.drop_index('idx_applications_follow_up_date')
    op.drop_column('applications', 'follow_up_date')
```

#### Data Migration
```python
# Migrate existing data to new structure
async def migrate_application_data(db: AsyncSession):
    # Get applications without follow_up_date
    applications = await db.execute(
        select(Application).where(Application.follow_up_date.is_(None))
    )

    for app in applications.scalars():
        # Set default follow-up date
        app.follow_up_date = app.applied_date + timedelta(days=7)

    await db.commit()
```

### Performance Optimization

#### Query Optimization
```sql
-- Optimized dashboard query
SELECT
    COUNT(*) as total_applications,
    COUNT(CASE WHEN status = 'interview' THEN 1 END) as interviews,
    COUNT(CASE WHEN status = 'offer' THEN 1 END) as offers,
    AVG(EXTRACT(EPOCH FROM (response_date - applied_date))/86400) as avg_response_days
FROM applications
WHERE user_id = $1 AND applied_date >= $2
```

#### Connection Pooling
```python
# Database connection configuration
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo": False  # Disable in production
}
```

### Backup and Recovery

#### Backup Strategy
```bash
# PostgreSQL backup commands
pg_dump -U postgres -h localhost career_copilot > backup_$(date +%Y%m%d_%H%M%S).sql

# Continuous archiving
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/archive/%f'
```

#### Point-in-Time Recovery
```bash
# Restore to specific timestamp
pg_restore -U postgres -d career_copilot --clean --if-exists backup_file.sql

# PITR recovery
recovery_target_time = '2024-01-15 14:30:00'
recovery_target_action = 'promote'
```

### Monitoring and Observability

#### Database Metrics
- **Connection Count**: Active/idle connections
- **Query Performance**: Slow query logs and execution plans
- **Table Sizes**: Growth monitoring and capacity planning
- **Index Usage**: Effectiveness and maintenance requirements

#### Data Quality Metrics
- **Null Value Rates**: Data completeness monitoring
- **Duplicate Detection**: Duplicate job/application detection
- **Constraint Violations**: Foreign key and check constraint monitoring
- **Data Freshness**: Staleness of cached and derived data

## Related Diagrams

- [[system-architecture|System Architecture]] - Overall system structure
- [[authentication-architecture|Authentication Architecture]] - Auth flow and security
- [[api-architecture|API Architecture]] - Endpoint organization
- [[deployment-architecture|Deployment Architecture]] - Infrastructure setup

## Component References

- [[auth-component|Authentication Component]] - User management
- [[applications-component|Applications Component]] - Job tracking
- [[analytics-component|Analytics Component]] - Metrics and reporting
- [[notifications-component|Notifications Component]] - Alert system

---

*See also: [[database-schema|Database Schema Details]], [[data-migration|Data Migration Guide]], [[performance-tuning|Performance Tuning]]*"