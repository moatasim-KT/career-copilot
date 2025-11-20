# Authentication & Real-Time Notification System

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Testing Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

## Overview

Complete authentication and real-time notification system for Career Copilot, implementing Phase 3 Task 3.1 requirements.

## Architecture

### Components

#### 1. **AuthContext** (`frontend/src/contexts/AuthContext.tsx`)
Global authentication state management using React Context API.

**Features:**
- User state management with TypeScript interfaces
- JWT token persistence in localStorage
- Automatic token validation on app mount
- Login, register, logout, and refresh user methods
- Router integration for post-auth redirects

**Usage:**
```typescript
import { useAuth } from '@/contexts/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();
  
  const handleLogin = async () => {
    await login('user@example.com', 'password');
  };
  
  return <div>{isAuthenticated ? `Hello ${user?.username}` : 'Please login'}</div>;
}
```

**Methods:**
- `login(identifier: string, password: string)` - Credential login (email or username)
- `register(username: string, email: string, password: string)` - User registration
- `logout()` - Clear session and redirect to login
- `refreshUser()` - Validate token and update user state

#### 2. **NotificationContext** (`frontend/src/contexts/NotificationContext.tsx`)
Real-time notification management with WebSocket integration.

**Features:**
- Automatic WebSocket connection when user authenticates
- Channel subscription management (user-specific, job matches, system updates)
- Toast notifications for real-time events
- Notification history (last 50 notifications)
- Connection status tracking

**Usage:**
```typescript
import { useNotifications } from '@/contexts/NotificationContext';

function MyComponent() {
  const { isConnected, notifications, clearNotifications } = useNotifications();
  
  return (
    <div>
      <div>Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      <div>Unread: {notifications.length}</div>
      <button onClick={clearNotifications}>Clear All</button>
    </div>
  );
}
```

**Notification Types:**
- **Job Match**: New job matches with score and details
- **Application Status**: Status updates for applications
- **Analytics**: Real-time metric updates
- **System**: Platform-wide announcements (info/warning/error)

#### 3. **WebSocket Client** (`frontend/src/services/websocket.ts`)
Singleton WebSocket service for real-time communication.

**Features:**
- Connection management with token authentication
- Exponential backoff reconnection (5 attempts: 1s, 2s, 4s, 8s, 16s, 32s)
- Message type subscription system
- Channel subscription/unsubscription
- Ping/pong keepalive (30-second interval)
- Type-safe notification interfaces

**Usage:**
```typescript
import { webSocketClient } from '@/services/websocket';

// Connect (done automatically by NotificationContext)
await webSocketClient.connect(userId, token);

// Subscribe to specific message types
const unsubscribe = webSocketClient.subscribe('job_match_notification', (message) => {
  console.log('New job match:', message);
});

// Subscribe to channels
webSocketClient.subscribeToChannel('user_123');
webSocketClient.subscribeToChannel('job_matches');

// Cleanup
unsubscribe();
webSocketClient.disconnect();
```

#### 4. **Protected Routes Middleware** (`frontend/src/middleware.ts`)
Next.js middleware for route protection.

**Protected Routes:**
- `/dashboard` - User dashboard
- `/jobs` - Job listings
- `/applications` - Application tracking
- `/content` - Content generation
- `/interview-practice` - Interview preparation
- `/analytics` - Analytics dashboard
- `/settings` - User settings
- `/profile` - User profile

**Auth Routes:**
- `/login` - Login page (redirects to dashboard if authenticated)
- `/register` - Registration page (redirects to dashboard if authenticated)

**Flow:**
1. Check for access token in cookies
2. Protected route + no token → Redirect to `/login?redirect=/original-path`
3. Auth route + token → Redirect to `/dashboard`
4. Valid token → Allow access

#### 5. **OAuth Callback Handler** (`frontend/src/app/auth/oauth/[provider]/callback/page.tsx`)
Handles OAuth provider callbacks (Google, LinkedIn, GitHub).

**Flow:**
1. User initiates OAuth login on login page
2. Redirected to provider (Google/LinkedIn/GitHub)
3. Provider redirects back to `/auth/oauth/[provider]/callback`
4. Handler extracts token from URL params or cookies
5. Stores token in localStorage
6. Calls `refreshUser()` to fetch user details
7. Redirects to `/dashboard` on success

**Error Handling:**
- Displays error message if OAuth fails
- Provides "Back to Login" button for retry

#### 6. **Login Page** (`frontend/src/app/login/page.tsx`)
User login interface with credential and OAuth options.

**Features:**
- Email or username login
- Password field with show/hide toggle
- OAuth buttons (Google, LinkedIn, GitHub)
- Form validation
- Error display
- Loading states
- "Forgot password?" link
- Register link

#### 7. **Register Page** (`frontend/src/app/register/page.tsx`)
New user registration interface.

**Features:**
- Username, email, password fields
- Password confirmation validation
- Minimum password length (8 characters)
- Terms and conditions checkbox
- OAuth signup options
- Form validation
- Error display
- Login link

#### 8. **NotificationCenter Component** (`frontend/src/components/ui/notification-center.tsx`)
UI component for notification dropdown.

**Features:**
- Bell icon with unread count badge
- Connection status indicator
- Notification list with timestamps
- Click to navigate to related pages
- "Clear all" button
- Empty state message
- Scrollable list (max height 96)

**Usage:**
```typescript
import { NotificationCenter } from '@/components/ui/notification-center';

function Header() {
  return (
    <header>
      <nav>
        <NotificationCenter />
      </nav>
    </header>
  );
}
```

## Data Flow

### Authentication Flow

```
1. User enters credentials on /login
   ↓
2. useAuth().login(identifier, password)
   ↓
3. POST /api/v1/auth/login (backend)
   ↓
4. Backend validates credentials
   ↓
5. Returns { access_token, user }
   ↓
6. Store token in localStorage
   ↓
7. Update AuthContext user state
   ↓
8. NotificationContext detects user state change
   ↓
9. WebSocket connects: ws://backend/ws/notifications/{userId}?token={token}
   ↓
10. Subscribe to channels: user_{userId}, job_matches, system_updates
   ↓
11. Router redirects to /dashboard
```

### Real-Time Notification Flow

```
1. Backend event triggers (new job match, status change, etc.)
   ↓
2. Backend sends WebSocket message
   ↓
3. WebSocketClient receives message
   ↓
4. Message dispatched to subscribed handlers
   ↓
5. NotificationContext handler executes
   ↓
6. Toast notification displayed (sonner)
   ↓
7. Notification added to history
   ↓
8. NotificationCenter badge updates
```

### OAuth Flow

```
1. User clicks OAuth button on /login
   ↓
2. Redirect to provider: GET /api/v1/auth/oauth/{provider}
   ↓
3. Backend redirects to provider's OAuth page
   ↓
4. User authenticates with provider
   ↓
5. Provider redirects: /auth/oauth/{provider}/callback?token={token}
   ↓
6. Callback page extracts token
   ↓
7. Store token in localStorage
   ↓
8. Call refreshUser() to fetch user details
   ↓
9. WebSocket connects automatically
   ↓
10. Redirect to /dashboard
```

## Configuration

### Environment Variables

**Backend** (`backend/.env`):
```bash
# JWT Settings
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OAuth Providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# WebSocket
WEBSOCKET_URL=ws://localhost:8000/ws
```

**Frontend** (`frontend/.env`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### Backend OAuth Setup

Each OAuth provider requires app registration:

1. **Google Cloud Console** (https://console.cloud.google.com/)
   - Create OAuth 2.0 Client ID
   - Add redirect URI: `http://localhost:8000/api/v1/auth/oauth/google/callback`

2. **LinkedIn Developer Portal** (https://www.linkedin.com/developers/)
   - Create app
   - Add redirect URL: `http://localhost:8000/api/v1/auth/oauth/linkedin/callback`

3. **GitHub Developer Settings** (https://github.com/settings/developers)
   - Register OAuth App
   - Callback URL: `http://localhost:8000/api/v1/auth/oauth/github/callback`

## Testing

### Manual Testing Checklist

#### Authentication
- [ ] Register new user with username, email, password
- [ ] Login with email + password
- [ ] Login with username + password
- [ ] Logout clears session
- [ ] Protected routes redirect to login when unauthenticated
- [ ] Auth routes redirect to dashboard when authenticated
- [ ] Token persists across page reloads
- [ ] Invalid credentials show error message
- [ ] Duplicate username/email shows error

#### OAuth
- [ ] Google OAuth login works
- [ ] LinkedIn OAuth login works
- [ ] GitHub OAuth login works
- [ ] OAuth error displays properly
- [ ] OAuth callback redirects to dashboard

#### WebSocket
- [ ] WebSocket connects after login
- [ ] Connection status shows in NotificationCenter
- [ ] Job match notifications appear as toasts
- [ ] Application status notifications appear as toasts
- [ ] System notifications appear as toasts
- [ ] Notification history persists during session
- [ ] Clear all notifications works
- [ ] Clicking notification navigates to correct page
- [ ] WebSocket disconnects on logout
- [ ] WebSocket reconnects after connection loss (5 attempts)

#### Middleware
- [ ] Dashboard requires authentication
- [ ] Jobs page requires authentication
- [ ] Applications page requires authentication
- [ ] Login page accessible when not authenticated
- [ ] Login page redirects when authenticated
- [ ] Redirect URL preserved in login redirect

### Automated Testing

**Backend Tests** (Pytest):
```bash
cd backend
pytest tests/test_auth.py -v
pytest tests/test_websocket.py -v
```

**Frontend Tests** (Jest):
```bash
cd frontend
npm test -- AuthContext
npm test -- NotificationContext
npm test -- websocket
```

**E2E Tests** (Playwright):
```bash
cd frontend
npx playwright test auth-flow.spec.ts
npx playwright test notifications.spec.ts
```

## Troubleshooting

### WebSocket Connection Issues

**Symptom**: NotificationCenter shows "Disconnected"

**Possible Causes**:
1. Backend not running: `docker-compose up backend`
2. Invalid token: Check localStorage for `access_token`
3. CORS issues: Verify `CORS_ORIGINS` in backend config
4. Firewall blocking WebSocket: Check network settings

**Debug Steps**:
```javascript
// Open browser console
console.log('Token:', localStorage.getItem('access_token'));
console.log('User:', localStorage.getItem('user'));

// Check WebSocket connection
import { webSocketClient } from '@/services/websocket';
console.log('Connected:', webSocketClient.isConnected);
```

### OAuth Callback Errors

**Symptom**: OAuth redirect shows error message

**Possible Causes**:
1. Invalid OAuth credentials in backend `.env`
2. Incorrect redirect URI in provider settings
3. Provider app not approved/published
4. Missing scopes in OAuth request

**Debug Steps**:
1. Check backend logs: `docker-compose logs -f backend`
2. Verify redirect URIs match exactly (including http/https, port)
3. Test OAuth flow in Postman: `GET http://localhost:8000/api/v1/auth/oauth/google`

### Token Persistence Issues

**Symptom**: User logged out after page reload

**Possible Causes**:
1. Token not being saved to localStorage
2. Token expired (check `ACCESS_TOKEN_EXPIRE_MINUTES`)
3. Browser blocking localStorage (incognito mode)
4. Token validation failing on backend

**Debug Steps**:
```javascript
// Check localStorage
console.log('Token:', localStorage.getItem('access_token'));
console.log('User:', localStorage.getItem('user'));

// Test token validation
fetch('http://localhost:8000/api/v1/auth/me', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
}).then(r => r.json()).then(console.log);
```

## Performance Considerations

### WebSocket Connection
- Singleton client prevents multiple connections
- Exponential backoff prevents rapid reconnection attempts
- 30-second ping interval keeps connection alive
- Automatic cleanup on logout/unmount

### Notification History
- Limited to last 50 notifications to prevent memory bloat
- Cleared on context unmount
- Toast notifications auto-dismiss (default 4s)

### Token Storage
- localStorage used for persistence (not sessionStorage)
- Token checked once on mount, not on every route change
- Middleware checks cookie (faster than localStorage)

## Security Considerations

### Token Security
- JWT tokens use HS256 algorithm
- Tokens stored in localStorage (XSS risk, but acceptable for SPA)
- HTTPS recommended for production (prevents token interception)
- Short expiration time (30 minutes) limits exposure
- No refresh token in frontend (reduces attack surface)

### OAuth Security
- State parameter prevents CSRF attacks (backend handles)
- Redirect URIs strictly validated
- OAuth tokens never exposed to frontend (backend exchanges code for token)

### WebSocket Security
- Token required for WebSocket connection
- Token validated on connection and periodically
- Channel subscriptions limited to user's own data
- No arbitrary channel subscription allowed

### CORS Configuration
- Strict origin checking in production
- Credentials included in requests
- Preflight requests properly handled

## Future Enhancements

### Short-term (1-2 weeks)
- [ ] Add "Remember me" checkbox for extended sessions
- [ ] Implement email verification for new registrations
- [ ] Add password reset flow
- [ ] Create notification preferences page
- [ ] Add notification sound toggle
- [ ] Implement push notifications (web push API)

### Medium-term (1-2 months)
- [ ] Add two-factor authentication (2FA)
- [ ] Implement refresh token rotation
- [ ] Add session management (view active sessions, revoke)
- [ ] Create audit log for auth events
- [ ] Add rate limiting for login attempts
- [ ] Implement account lockout after failed attempts

### Long-term (3-6 months)
- [ ] Add biometric authentication (WebAuthn)
- [ ] Implement SSO with enterprise providers (Okta, Auth0)
- [ ] Add magic link login (passwordless)
- [ ] Create OAuth provider (allow other apps to use Career Copilot auth)
- [ ] Implement federated identity

## API Endpoints Reference

### Authentication Endpoints

**Login**
```
POST /api/v1/auth/login
Body: { "identifier": "user@example.com", "password": "password123" }
Response: { "access_token": "jwt-token", "user": {...} }
```

**Register**
```
POST /api/v1/auth/register
Body: { "username": "newuser", "email": "user@example.com", "password": "password123" }
Response: { "access_token": "jwt-token", "user": {...} }
```

**Validate Token**
```
GET /api/v1/auth/me
Headers: { "Authorization": "Bearer jwt-token" }
Response: { "id": 1, "email": "user@example.com", ... }
```

**OAuth Initiate**
```
GET /api/v1/auth/oauth/{provider}
Providers: google, linkedin, github
Response: Redirect to provider OAuth page
```

**OAuth Callback**
```
GET /api/v1/auth/oauth/{provider}/callback?code=...
Response: Redirect to frontend /auth/oauth/{provider}/callback?token=jwt-token
```

### WebSocket Endpoint

**Connect**
```
WS /ws/notifications/{user_id}?token=jwt-token
```

**Message Types** (from server):
- `job_match_notification` - New job match
- `application_status_update` - Application status changed
- `analytics_notification` - Metrics update
- `system_notification` - System announcement
- `pong` - Keepalive response

**Channel Operations** (to server):
```json
// Subscribe to channel
{ "action": "subscribe", "channel": "user_123" }

// Unsubscribe from channel
{ "action": "unsubscribe", "channel": "user_123" }
```

## Code Examples

### Custom Notification Hook

```typescript
// hooks/useJobMatchNotifications.ts
import { useEffect } from 'react';
import { webSocketClient } from '@/services/websocket';
import type { JobMatchNotification } from '@/services/websocket';

export function useJobMatchNotifications(onMatch: (notification: JobMatchNotification) => void) {
  useEffect(() => {
    const unsubscribe = webSocketClient.subscribe('job_match_notification', (message) => {
      onMatch(message as JobMatchNotification);
    });
    
    return unsubscribe;
  }, [onMatch]);
}

// Usage
function JobMatchesPage() {
  useJobMatchNotifications((notification) => {
    console.log('New match:', notification.job_title);
    // Custom handling
  });
  
  return <div>Jobs page</div>;
}
```

### Protected Component

```typescript
// components/ProtectedContent.tsx
import { useAuth } from '@/contexts/AuthContext';

export function ProtectedContent({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <div>Please log in to view this content.</div>;
  }
  
  return <>{children}</>;
}
```

### Conditional Rendering Based on Auth

```typescript
function Header() {
  const { isAuthenticated, user, logout } = useAuth();
  
  return (
    <header>
      <nav>
        {isAuthenticated ? (
          <>
            <span>Welcome, {user?.username}!</span>
            <NotificationCenter />
            <button onClick={logout}>Logout</button>
          </>
        ) : (
          <>
            <a href="/login">Login</a>
            <a href="/register">Register</a>
          </>
        )}
      </nav>
    </header>
  );
}
```

## Monitoring & Observability

### Metrics to Track

**Authentication**:
- Login success/failure rate
- Registration rate
- OAuth provider distribution
- Session duration
- Token expiration rate

**WebSocket**:
- Active connections count
- Connection duration
- Reconnection frequency
- Message delivery rate
- Channel subscription counts

**Notifications**:
- Notification delivery rate by type
- Average time to notification display
- Notification interaction rate (clicks)
- Clear rate vs. auto-dismiss rate

### Logging

**Backend**:
```python
# backend/app/services/auth_service.py
import logging
logger = logging.getLogger(__name__)

def login(identifier: str, password: str):
    logger.info(f"Login attempt for: {identifier}")
    # ... logic ...
    logger.info(f"Login successful: {user.id}")
```

**Frontend**:
```typescript
// frontend/src/contexts/AuthContext.tsx
console.log('[Auth] User logged in:', user.id);
console.log('[Auth] Token stored in localStorage');
console.log('[Auth] Redirecting to dashboard');
```

### Error Tracking (Sentry)

Already configured in `frontend/sentry.*.config.ts`:

```typescript
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 1.0,
  beforeSend(event) {
    // Filter sensitive data
    if (event.request?.cookies) {
      delete event.request.cookies;
    }
    return event;
  },
});
```

## Resources

### Documentation
- [Next.js Authentication Docs](https://nextjs.org/docs/authentication)
- [JWT.io](https://jwt.io/) - JWT token debugger
- [WebSocket API Docs](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [OAuth 2.0 RFC](https://tools.ietf.org/html/rfc6749)

### Libraries
- [sonner](https://sonner.emilkowal.ski/) - Toast notifications
- [React Hook Form](https://react-hook-form.com/) - Form validation
- [Zod](https://zod.dev/) - Schema validation

### Tools
- [Postman](https://www.postman.com/) - API testing
- [WebSocket King](https://websocketking.com/) - WebSocket testing
- [jwt.io Debugger](https://jwt.io/#debugger) - JWT inspection

---

**Document Version**: 1.0  
**Last Updated**: {{ current_date }}  
**Maintainer**: Career Copilot Team
