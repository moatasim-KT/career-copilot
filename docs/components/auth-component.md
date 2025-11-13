# Authentication Component Reference

## Overview

The Authentication component handles user management, OAuth integration, and session management. Currently configured for single-user mode with optional OAuth support.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Layer     │    │  Service Layer   │    │  Data Layer     │
│                 │    │                  │    │                 │
│ • auth.py       │◄──►│ • dependencies.py │◄──►│ • user.py       │
│ • users.py      │    │ • security/      │    │ • user_schemas  │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              ▲
                              │
                       ┌─────────────────┐
                       │   OAuth Flow    │
                       │                 │
                       │ • Google OAuth  │
                       │ • JWT Tokens    │
                       └─────────────────┘
```

## Core Files

### API Layer
- **Auth API**: [[../../backend/app/api/v1/auth.py|auth.py]] - OAuth endpoints and user authentication
- **Users API**: [[../../backend/app/api/v1/users.py|users.py]] - User profile management
- **OAuth Flow**: [[../../backend/app/api/v1/auth.py#google_oauth_login|Google OAuth login/callback]]

### Service Layer
- **Dependencies**: [[../../backend/app/dependencies.py|dependencies.py]] - Authentication dependencies and user resolution
- **Security Module**: [[../../backend/app/security/|security/]] - Security utilities and validation

### Data Layer
- **User Model**: [[../../backend/app/models/user.py|user.py]] - User database model
- **User Schemas**: [[../../backend/app/schemas/user.py|user.py]] - Pydantic schemas for user data

## Authentication Modes

### Single-User Mode (Current)
- **Purpose**: Simplified development and testing
- **Implementation**: All requests use a single default user (moatasimfarooque@gmail.com)
- **Dependencies**: [[../../backend/app/dependencies.py#get_current_user|get_current_user()]] always returns the same user

### OAuth Mode (Configured but Disabled)
- **Google OAuth**: Full OAuth 2.0 flow with Google
- **JWT Tokens**: Token-based authentication (mock tokens in development)
- **User Creation**: Automatic user creation on first OAuth login

## Database Schema

```sql
-- From user.py model
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NULL,  -- Not used in single-user mode
    skills JSONB DEFAULT '[]',
    preferred_locations JSONB DEFAULT '[]',
    experience_level VARCHAR,
    daily_application_goal INTEGER DEFAULT 10,
    is_admin BOOLEAN DEFAULT false,
    prefer_remote_jobs BOOLEAN DEFAULT false,

    -- OAuth fields
    oauth_provider VARCHAR NULL,  -- 'google', 'linkedin', 'github'
    oauth_id VARCHAR NULL,  -- External user ID
    profile_picture_url VARCHAR NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Extended data
    profile JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}'
);
```

**Relationships:**
- One-to-Many: `jobs`, `applications`, `notifications`, etc.
- One-to-One: `notification_preferences`

**Indexes:**
- `email` (unique)
- `username` (unique)
- `oauth_provider`, `oauth_id` (composite)

## API Endpoints

| Method | Endpoint | Description | Implementation |
|--------|----------|-------------|----------------|
| GET | `/auth/oauth/google/login` | Initiate Google OAuth | [[../../backend/app/api/v1/auth.py#google_oauth_login\|google_oauth_login()]] |
| GET | `/auth/oauth/google/callback` | Handle OAuth callback | [[../../backend/app/api/v1/auth.py#google_oauth_callback\|google_oauth_callback()]] |
| GET | `/users/me` | Get current user profile | [[../../backend/app/api/v1/users.py#get_current_user_profile\|get_current_user_profile()]] |
| PUT | `/users/me` | Update user profile | [[../../backend/app/api/v1/users.py#update_current_user\|update_current_user()]] |
| GET | `/users/{user_id}` | Get user by ID | [[../../backend/app/api/v1/users.py#get_user\|get_user()]] |

## Key Functions

### Single-User Authentication
```python
# From dependencies.py
async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    # Always return Moatasim's user account
    result = await db.execute(
        select(User).where(User.email == "moatasimfarooque@gmail.com")
    )
    user = result.scalar_one_or_none()

    if user is None:
        # Fallback to first user or raise error
        raise HTTPException(status_code=404, detail="No users found")
    return user
```

### OAuth Flow
```python
# From auth.py - Google OAuth initiation
@router.get("/auth/oauth/google/login")
async def google_oauth_login():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.google_client_id}"
        "&redirect_uri={settings.backend_url}/api/v1/auth/oauth/google/callback"
        "&response_type=code&scope=openid email profile"
        "&access_type=offline&prompt=consent"
    )
    return RedirectResponse(url=google_auth_url)
```

### User Creation/Update
```python
# From auth.py - OAuth callback handling
@router.get("/auth/oauth/google/callback")
async def google_oauth_callback(code: str, db: AsyncSession = Depends(get_db)):
    # Exchange code for token, get user info
    user_info = await get_google_user_info(access_token)

    # Check if user exists
    existing_user = await db.execute(
        select(User).where(User.email == user_info["email"])
    ).scalar_one_or_none()

    if existing_user:
        # Update existing user with OAuth info
        existing_user.oauth_provider = "google"
        existing_user.oauth_id = user_info["id"]
    else:
        # Create new user
        new_user = User(
            email=user_info["email"],
            username=user_info.get("name"),
            oauth_provider="google",
            oauth_id=user_info["id"]
        )
        db.add(new_user)
```

## Configuration

### Environment Variables
```bash
# OAuth Configuration (optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Single-User Mode (default)
# No additional configuration needed
```

### Settings Integration
```python
# From core/config.py
class Settings(BaseSettings):
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    @property
    def oauth_enabled(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)
```

## Security Considerations

### Single-User Mode
- **Development Only**: Not suitable for production
- **No Passwords**: Authentication completely bypassed
- **User Isolation**: All data belongs to single user

### OAuth Security
- **State Parameter**: Should be added for CSRF protection
- **PKCE**: Recommended for public clients
- **Token Storage**: JWT tokens with proper expiration
- **Refresh Tokens**: Separate long-lived refresh tokens

### Input Validation
- **Email Validation**: Proper email format checking
- **OAuth ID Sanitization**: Clean external provider IDs
- **Profile Data Sanitization**: Safe handling of user profile data

## Testing

### Single-User Tests
```python
# Test authentication dependency
def test_get_current_user(db: Session):
    user = get_current_user(db)
    assert user.email == "moatasimfarooque@gmail.com"
```

### OAuth Flow Tests
```python
# Mock OAuth tests
def test_google_oauth_callback(client: TestClient):
    # Mock Google API responses
    response = client.get("/auth/oauth/google/callback?code=mock_code")
    assert response.status_code == 200
```

**Test Files:**
- [[../../backend/tests/test_auth.py|test_auth.py]] - Authentication tests
- [[../../backend/tests/test_users.py|test_users.py]] - User management tests

## Migration Strategies

### To Multi-User Mode
1. **Enable Password Authentication**
   - Add password hashing (bcrypt)
   - Implement login/register endpoints
   - Add JWT token generation

2. **Database Changes**
   - Make `hashed_password` required
   - Add password reset functionality
   - Update user creation flow

3. **Frontend Changes**
   - Add login/register forms
   - Implement token storage
   - Add logout functionality

### OAuth-Only Mode
1. **Remove Password Fields**
   - Drop password-related columns
   - Simplify user model
   - Update schemas

2. **Enforce OAuth**
   - Remove password authentication
   - Require OAuth for all users
   - Simplify dependency injection

## Monitoring & Logging

### Authentication Events
- **Login Attempts**: Log all authentication attempts
- **OAuth Flows**: Track OAuth success/failure rates
- **User Creation**: Monitor new user registration

### Security Monitoring
- **Failed Logins**: Alert on suspicious patterns
- **OAuth Errors**: Monitor external provider issues
- **Token Issues**: Track JWT validation failures

## Related Components

- **Users**: [[users-component|Users Component]] - User profile management
- **Security**: [[../../backend/app/security/|Security Module]] - Input validation and threat detection
- **Notifications**: [[notifications-component|Notifications Component]] - User communication

## Common Patterns

### Dependency Injection
```python
# Always use dependency injection for current user
@router.get("/protected-endpoint")
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    return {"user_id": current_user.id}
```

### Optional Authentication
```python
# For endpoints that work with or without auth
@router.get("/public-endpoint")
async def public_endpoint(current_user: Optional[User] = Depends(get_current_user_optional)):
    if current_user:
        return {"personalized": True, "user": current_user.username}
    return {"personalized": False}
```

### OAuth Error Handling
```python
# Proper error handling for OAuth flows
try:
    token_data = await exchange_code_for_token(code)
    user_info = await get_user_info(token_data["access_token"])
except httpx.HTTPError as e:
    logger.error(f"OAuth API error: {e}")
    raise HTTPException(status_code=400, detail="OAuth provider error")
```

---

*See also: [[../api/API.md#authentication|API Authentication Docs]], [[../../backend/app/dependencies.py|Authentication Dependencies]]*"