# Calendar Integration Roadmap

Tracking interviews and follow-ups inside Career Copilot is powerful, but users still rely on Google or Outlook calendars to manage their day. This roadmap captures the minimum viable plan for syncing Career Copilot events with external calendars while keeping the architecture maintainable.

## Goals

1. **Create calendar events automatically** for interviews, follow-ups, and reminders scheduled in the application.
2. **Bidirectional updates** so edits/cancellations in Career Copilot reflect on the user’s calendar (and vice versa where feasible).
3. **Respect privacy and security** by storing tokens securely and scoping access to the minimum required calendar permissions.
4. **Deliver a delightful UX** for connecting accounts, previewing events, and resolving sync conflicts.

## Supported Providers (Phase 1)

- Google Calendar (OAuth 2.0 + Google Calendar API v3)
- Microsoft Outlook / Office 365 (OAuth 2.0 + Microsoft Graph Calendar APIs)

> Additional providers (iCloud, CalDAV) can be considered once the shared abstraction is stable.

## High-Level Architecture

| Layer | Responsibilities |
| --- | --- |
| Frontend | Collect OAuth consent, display connection status, allow users to choose which events sync, show sync errors. |
| Backend API | Handle OAuth callbacks, store refresh tokens (encrypted), expose CRUD endpoints for calendar preferences, enqueue sync jobs. |
| Background Workers (Celery) | Create/update/delete calendar events via provider SDKs, retry failed jobs, emit notifications. |
| Database | Persist provider credentials, per-event sync metadata (provider event IDs, sync timestamps, status). |

## Backend Tasks

1. **Credential Storage**
   - Create `calendar_credentials` table (user_id, provider, refresh_token, token_expiry, scopes, metadata, created_at, updated_at).
   - Encrypt tokens at rest (e.g., Fernet with key from secrets manager).

2. **OAuth Flow Endpoints**
   - `POST /api/v1/calendar/{provider}/connect` → returns provider auth URL.
   - `GET /api/v1/calendar/{provider}/callback` → exchanges code for tokens, stores credentials.
   - `DELETE /api/v1/calendar/{provider}` → revokes tokens and deletes stored credentials.

3. **Sync Preferences API**
   - Allow users to choose which event types sync (interviews, follow-ups, reminders) and default notification timing.
   - Store preferences alongside credentials or in dedicated table.

4. **Event Sync Service**
   - Service class responsible for translating Career Copilot events to provider payloads.
   - Handles create/update/delete + conflict detection (compare `updated_at` vs provider `updated` timestamp).
   - Emits domain events (success/failure) for notifications or audit logs.

5. **Celery Tasks**
   - `sync_calendar_event(event_id, action)` (create/update/delete).
   - Batch job `sync_calendar_credentials(user_id)` to refresh tokens proactively.

6. **Webhooks / Push Notifications (Phase 2)**
   - Google push notifications & Microsoft change subscriptions for near real-time inbound updates.

## Frontend Tasks

1. **Settings UI** (`/settings/integrations` or `/settings/notifications`)
   - Display provider cards with “Connect” / “Disconnect” CTA and status badges.
   - Show last sync time, error state, and event type toggles.

2. **OAuth Redirect Handling**
   - Dedicated page to handle provider callback query params and show success/error state before redirecting.

3. **Event Forms Hooks**
   - Update interview/follow-up forms with “Add to calendar” checkbox (default on if integration active).
   - Surface sync status in timelines (e.g., badge “Synced to Google Calendar”).

4. **Error Surfacing**
   - Toasts / banners when sync fails (rate limit, revoked token, missing permissions) with CTA to reconnect.

## Security & Compliance

- Use provider-specific least-privilege scopes (`https://www.googleapis.com/auth/calendar.events`, `Calendars.ReadWrite`).
- Store refresh tokens encrypted; never log raw tokens.
- Implement token revocation on disconnect.
- Add audit logs for connection/disconnection and outbound event sync attempts.

## Observability

- Metrics: number of connected calendars, sync success/failure counts, average sync latency.
- Alerts for repeated failures (e.g., more than 5 sync failures for same user within 1 hour).

## Open Questions

- Do we support multiple calendars per user or single default calendar?
- Should follow-up reminders be separate calendar events or reminders attached to interviews?
- How do we reconcile edits made directly on the user’s calendar (Phase 2 push notifications)?

## Next Steps

1. Finalize database schema and migrations.
2. Build Google OAuth flow end-to-end (backend + frontend) behind feature flag.
3. Create sync service + Celery tasks for interview events.
4. Roll out to internal testers before enabling for all users.
