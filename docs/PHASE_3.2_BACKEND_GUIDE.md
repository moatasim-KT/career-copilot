# Phase 3.2 Implementation Guide - Backend Infrastructure

**Date**: November 16, 2025  
**Status**: Backend Infrastructure Complete (Part 1 of 3)  
**Progress**: 40% Complete (Backend), Frontend & Testing Remain

---

## Overview

Phase 3.2 focuses on three major feature additions:
1. **Calendar Integration** - Google Calendar and Outlook sync
2. **Dashboard Customization** - Drag-and-drop widget system
3. **Additional Job Boards** - XING, Welcome to the Jungle, AngelList

This document covers the **Backend Infrastructure** completed in Part 1.

---

## 1. Calendar Integration

### Architecture

The calendar integration system consists of:
- **Service Layer**: Handles OAuth and calendar operations
- **Data Layer**: Stores credentials and event mappings
- **API Layer**: Exposes REST endpoints for frontend
- **Migration**: Database schema changes

### Components

#### 1.1 Calendar Service (`backend/app/services/calendar_service.py`)

**Purpose**: Core business logic for calendar operations

**Features**:
- Google Calendar OAuth 2.0 flow
- Microsoft Outlook OAuth 2.0 flow (via MSAL)
- Event CRUD operations for both providers
- Token refresh handling
- Credential management

**Key Methods**:
```python
class CalendarService:
    # Google Calendar
    def get_google_auth_url(user_id, redirect_uri) -> str
    def exchange_google_code(code, redirect_uri) -> Dict
    def create_google_event(access_token, refresh_token, event_data) -> Dict
    def update_google_event(...) -> Dict
    def delete_google_event(...) -> bool
    
    # Microsoft Outlook
    def get_outlook_auth_url(user_id, redirect_uri) -> str
    def exchange_outlook_code(code, redirect_uri) -> Dict
    def create_outlook_event(access_token, event_data) -> Dict
    def update_outlook_event(...) -> Dict
    def delete_outlook_event(...) -> bool
```

**Lines**: 450+

#### 1.2 Calendar Models (`backend/app/models/calendar.py`)

**Purpose**: Database schema for calendar data

**Models**:

1. **CalendarCredential**
   - Stores OAuth tokens (access + refresh)
   - Provider type (google/outlook)
   - Token expiry tracking
   - Active/inactive status
   - One-to-many relationship with CalendarEvent

2. **CalendarEvent**
   - Maps application interviews to calendar events
   - Stores event details (title, description, location, times)
   - Reminder settings (15min, 1hour, 1day)
   - Sync status tracking
   - Links to User, Application, and CalendarCredential

**Schema**:
```sql
CREATE TABLE calendar_credentials (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expiry TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE calendar_events (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    application_id INTEGER REFERENCES applications(id),
    calendar_credential_id INTEGER REFERENCES calendar_credentials(id),
    event_id VARCHAR(255) NOT NULL,  -- Provider's event ID
    title VARCHAR(500) NOT NULL,
    description TEXT,
    location VARCHAR(500),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    timezone VARCHAR(100) DEFAULT 'UTC',
    reminder_15min BOOLEAN DEFAULT TRUE,
    reminder_1hour BOOLEAN DEFAULT TRUE,
    reminder_1day BOOLEAN DEFAULT FALSE,
    is_synced BOOLEAN DEFAULT TRUE,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Lines**: 75+

#### 1.3 Calendar Schemas (`backend/app/schemas/calendar.py`)

**Purpose**: Pydantic models for API validation

**Schemas**:
- `CalendarOAuthURL` - OAuth authorization URL response
- `CalendarCredentialCreate/Response` - Credential management
- `CalendarEventCreate/Update/Response` - Event operations
- Field validation (end time after start, provider validation)

**Lines**: 120+

#### 1.4 Calendar API (`backend/app/api/v1/calendar.py`)

**Purpose**: REST API endpoints for calendar operations

**Endpoints**:

**OAuth Flow**:
- `GET /api/v1/calendar/oauth/{provider}/authorize`
  - Generate OAuth authorization URL
  - Providers: google, outlook
  - Returns: Authorization URL with state

- `POST /api/v1/calendar/oauth/{provider}/callback`
  - Handle OAuth callback
  - Exchange code for tokens
  - Store credentials in database
  - Returns: CalendarCredential

- `DELETE /api/v1/calendar/credentials/{provider}`
  - Disconnect calendar provider
  - Marks credential as inactive

**Event Management**:
- `POST /api/v1/calendar/events`
  - Create event in calendar provider
  - Store event in database
  - Link to application (optional)
  - Returns: CalendarEvent

- `GET /api/v1/calendar/events`
  - List user's calendar events
  - Filter by application_id (optional)
  - Returns: List of CalendarEvent

- `GET /api/v1/calendar/events/{event_id}`
  - Get specific calendar event
  - Returns: CalendarEvent

- `PATCH /api/v1/calendar/events/{event_id}`
  - Update event details
  - Sync changes to calendar provider
  - Returns: Updated CalendarEvent

- `DELETE /api/v1/calendar/events/{event_id}`
  - Delete event from provider and database
  - Returns: 204 No Content

**Credential Status**:
- `GET /api/v1/calendar/credentials`
  - List connected calendar providers
  - Returns: List of CalendarCredential

**Lines**: 370+

#### 1.5 Database Migration (`backend/alembic/versions/004_add_calendar_tables.py`)

**Purpose**: Schema migration for calendar tables

**Changes**:
- Creates `calendar_credentials` table
- Creates `calendar_events` table
- Adds foreign key constraints
- Creates indexes for performance

**Lines**: 75+

### Configuration

Add to `backend/.env`:
```env
# Google Calendar
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Microsoft Outlook
MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret_here
MICROSOFT_TENANT_ID=common
```

### Dependencies

Install required packages:
```bash
cd backend
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client msal
```

### OAuth Setup

#### Google Calendar

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URIs:
   - `http://localhost:3000/calendar/callback`
   - `https://yourdomain.com/calendar/callback`
6. Copy Client ID and Client Secret to `.env`

#### Microsoft Outlook

1. Go to [Azure Portal](https://portal.azure.com)
2. Register new application in Azure AD
3. Add Calendar.ReadWrite permission
4. Create client secret
5. Copy Application (client) ID and secret to `.env`

### Testing

```bash
# Test OAuth flow
curl -X GET "http://localhost:8000/api/v1/calendar/oauth/google/authorize?redirect_uri=http://localhost:3000/calendar/callback"

# Test event creation (requires valid token)
curl -X POST "http://localhost:8000/api/v1/calendar/events" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "title": "Interview with Acme Corp",
    "description": "Technical interview for Senior Engineer position",
    "start_time": "2025-11-20T14:00:00Z",
    "end_time": "2025-11-20T15:00:00Z",
    "timezone": "America/New_York",
    "reminder_15min": true,
    "reminder_1hour": true
  }'
```

---

## 2. Dashboard Customization

### Architecture

The dashboard customization system provides:
- **Persistent Layout Storage**: Save user's widget configuration
- **Default Layout**: Predefined widget arrangement
- **Flexible Configuration**: Support for custom widgets and arrangements

### Components

#### 2.1 Dashboard Model (`backend/app/models/dashboard.py`)

**Purpose**: Store user's dashboard layout

**Schema**:
```python
class DashboardLayout(Base):
    id: int
    user_id: int (unique, indexed)
    layout_config: JSON  # Stores widget positions, sizes, visibility
    created_at: datetime
    updated_at: datetime
```

**Layout Config Structure**:
```json
{
  "widgets": [
    {
      "id": "status-overview",
      "type": "status",
      "x": 0,
      "y": 0,
      "w": 6,
      "h": 4,
      "visible": true
    }
  ],
  "columns": 12,
  "rowHeight": 60,
  "breakpoints": {"lg": 1200, "md": 996, "sm": 768, "xs": 480},
  "cols": {"lg": 12, "md": 10, "sm": 6, "xs": 4}
}
```

**Lines**: 30+

#### 2.2 Dashboard Schemas (`backend/app/schemas/dashboard.py`)

**Purpose**: Validation for dashboard layout

**Schemas**:
- `DashboardLayoutCreate` - Create/update entire layout
- `DashboardLayoutUpdate` - Partial updates
- `DashboardLayoutResponse` - API response with metadata

**Lines**: 50+

#### 2.3 Dashboard API (`backend/app/api/v1/dashboard_layout.py`)

**Purpose**: CRUD operations for dashboard layouts

**Endpoints**:
- `GET /api/v1/dashboard/layout`
  - Get user's dashboard layout
  - Returns default if none exists
  
- `POST /api/v1/dashboard/layout`
  - Create or update dashboard layout
  - Upsert operation

- `PATCH /api/v1/dashboard/layout`
  - Partial update of layout

- `DELETE /api/v1/dashboard/layout`
  - Reset to default layout

**Default Widgets**:
1. **Status Overview** - Application stats overview
2. **Recent Jobs** - Latest job matches
3. **Application Stats** - Charts and metrics
4. **Upcoming Calendar** - Next interviews/events
5. **Recommendations** - AI-suggested jobs
6. **Activity Timeline** - Recent actions (hideable)
7. **Skills Progress** - Skill development tracking (hideable)
8. **Goals Tracker** - Career goals progress (hideable)

**Lines**: 100+

### Testing

```bash
# Get user's layout
curl -X GET "http://localhost:8000/api/v1/dashboard/layout" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Save custom layout
curl -X POST "http://localhost:8000/api/v1/dashboard/layout" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "layout_config": {
      "widgets": [
        {"id": "status-overview", "type": "status", "x": 0, "y": 0, "w": 12, "h": 4, "visible": true}
      ],
      "columns": 12
    }
  }'

# Reset to default
curl -X DELETE "http://localhost:8000/api/v1/dashboard/layout" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Summary Statistics

### Backend Infrastructure

| Component               | Files  | Lines      | Status      |
| ----------------------- | ------ | ---------- | ----------- |
| Calendar Integration    | 4      | 1,015      | ✅ Complete  |
| Dashboard Customization | 3      | 180        | ✅ Complete  |
| Database Migrations     | 1      | 75         | ✅ Complete  |
| Documentation           | 2      | 800+       | ✅ Complete  |
| **TOTAL**               | **10** | **2,070+** | ✅ **Ready** |

### API Endpoints Added

- Calendar: 10 endpoints
- Dashboard: 4 endpoints
- **Total**: 14 new endpoints

### Database Tables Added

- `calendar_credentials`
- `calendar_events`
- `dashboard_layouts`
- **Total**: 3 new tables

---

## Next Steps

### Phase 3.2 - Part 2: Frontend Implementation

**Estimated Effort**: 5-7 days

**Components Needed**:

1. **Calendar Integration UI**
   - OAuth connection page (`/settings/calendar`)
   - Event management interface
   - Calendar view component (react-big-calendar)
   - "Add to Calendar" button on applications

2. **Dashboard Customization UI**
   - Install `react-grid-layout`
   - Drag-and-drop interface
   - Widget components (8 widgets)
   - Save/load from API
   - Widget visibility toggles

3. **API Client Integration**
   - Add calendar methods to API client
   - Add dashboard methods to API client
   - TypeScript types

### Phase 3.2 - Part 3: Testing & Docs

**Estimated Effort**: 3-5 days

**Tasks**:
- E2E tests for calendar flow
- E2E tests for dashboard customization
- API documentation updates
- User guides for new features
- Video tutorials (optional)

---

## Running the Backend

```bash
# Install dependencies
cd backend
pip install -r requirements.txt
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client msal

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --port 8000
```

---

## Files Created

1. `backend/app/services/calendar_service.py` - Calendar integration service
2. `backend/app/models/calendar.py` - Calendar database models
3. `backend/app/schemas/calendar.py` - Calendar validation schemas
4. `backend/app/api/v1/calendar.py` - Calendar API endpoints
5. `backend/app/models/dashboard.py` - Dashboard layout model
6. `backend/app/schemas/dashboard.py` - Dashboard validation schemas
7. `backend/app/api/v1/dashboard_layout.py` - Dashboard API endpoints
8. `backend/alembic/versions/004_add_calendar_tables.py` - Database migration
9. `docs/PHASE_3.2_STATUS.md` - Phase status tracking
10. `docs/PHASE_3.2_BACKEND_GUIDE.md` - This guide

---

**Last Updated**: November 16, 2025 23:45 UTC
