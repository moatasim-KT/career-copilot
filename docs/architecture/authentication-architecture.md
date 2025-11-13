# Authentication Architecture

```mermaid
graph TB
    %% External Providers
    subgraph "OAuth Providers"
        GOOGLE[Google OAuth<br/>accounts.google.com]
        LINKEDIN[LinkedIn OAuth<br/>linkedin.com]
        GITHUB[GitHub OAuth<br/>github.com]
    end

    %% Frontend Authentication
    subgraph "Frontend (Next.js)"
        LOGIN_FORM[Login Form<br/>Google OAuth Button]
        AUTH_CONTEXT[Auth Context<br/>Token Management]
        API_CLIENT[API Client<br/>with Auth Headers]
        PROTECTED_ROUTES[Protected Routes<br/>Route Guards]
    end

    %% API Layer
    subgraph "API Layer (FastAPI)"
        AUTH_ROUTER[Auth Router<br/>/api/v1/auth/*]
        USER_ROUTER[User Router<br/>/api/v1/users/*]
        AUTH_MIDDLEWARE[Auth Middleware<br/>JWT Validation]
        CORS_MIDDLEWARE[CORS Middleware<br/>Cross-Origin Requests]
    end

    %% Service Layer
    subgraph "Service Layer"
        OAUTH_SERVICE[OAuth Service<br/>Token Exchange]
        USER_SERVICE[User Service<br/>Profile Management]
        SECURITY_SERVICE[Security Service<br/>Token Validation]
        DEPENDENCIES[Dependencies<br/>get_current_user]
    end

    %% Data Layer
    subgraph "Data Layer"
        USERS_TABLE[(users<br/>PostgreSQL)]
        SESSIONS_CACHE[(sessions<br/>Redis)]
        TOKENS_STORE[(tokens<br/>Redis)]
    end

    %% Authentication Flow
    subgraph "Auth Flow"
        INITIATE[1. Initiate OAuth<br/>Frontend → Google]
        CALLBACK[2. OAuth Callback<br/>Google → Backend]
        TOKEN_EXCHANGE[3. Token Exchange<br/>Backend ↔ Google]
        USER_LOOKUP[4. User Lookup/Create<br/>Database Query]
        JWT_ISSUE[5. JWT Token Issue<br/>Backend → Frontend]
        SESSION_STORE[6. Session Storage<br/>Redis Cache]
    end

    %% Connections
    LOGIN_FORM --> INITIATE
    INITIATE --> GOOGLE
    GOOGLE --> CALLBACK
    CALLBACK --> AUTH_ROUTER
    AUTH_ROUTER --> OAUTH_SERVICE
    OAUTH_SERVICE --> TOKEN_EXCHANGE
    TOKEN_EXCHANGE --> GOOGLE
    OAUTH_SERVICE --> USER_LOOKUP
    USER_LOOKUP --> USERS_TABLE
    OAUTH_SERVICE --> JWT_ISSUE
    JWT_ISSUE --> AUTH_CONTEXT
    AUTH_CONTEXT --> SESSION_STORE
    SESSION_STORE --> SESSIONS_CACHE

    API_CLIENT --> AUTH_MIDDLEWARE
    AUTH_MIDDLEWARE --> SECURITY_SERVICE
    SECURITY_SERVICE --> TOKENS_STORE
    SECURITY_SERVICE --> DEPENDENCIES
    DEPENDENCIES --> USERS_TABLE

    USER_ROUTER --> USER_SERVICE
    USER_SERVICE --> USERS_TABLE

    %% Styling
    classDef external fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef backend fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef service fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef data fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef flow fill:#f3e5f5,stroke:#4a148c,stroke-width:2px

    class GOOGLE,LINKEDIN,GITHUB external
    class LOGIN_FORM,AUTH_CONTEXT,API_CLIENT,PROTECTED_ROUTES frontend
    class AUTH_ROUTER,USER_ROUTER,AUTH_MIDDLEWARE,CORS_MIDDLEWARE backend
    class OAUTH_SERVICE,USER_SERVICE,SECURITY_SERVICE,DEPENDENCIES service
    class USERS_TABLE,SESSIONS_CACHE,TOKENS_STORE data
    class INITIATE,CALLBACK,TOKEN_EXCHANGE,USER_LOOKUP,JWT_ISSUE,SESSION_STORE flow
```

## Authentication Flow Details

### 1. OAuth Initiation
```javascript
// Frontend: Initiate Google OAuth
const handleGoogleLogin = () => {
  window.location.href = `${API_BASE}/auth/oauth/google/login`;
};
```

### 2. OAuth Callback Handling
```python
# Backend: Handle OAuth callback
@router.get("/auth/oauth/google/callback")
async def google_oauth_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    # Exchange code for tokens
    token_data = await exchange_code_for_token(code)

    # Get user info from Google
    user_info = await get_google_user_info(token_data["access_token"])

    # Find or create user
    user = await get_or_create_user(db, user_info)

    # Generate JWT token
    jwt_token = create_jwt_token(user.id)

    return {"access_token": jwt_token, "token_type": "bearer"}
```

### 3. Token Validation
```python
# Backend: JWT token validation
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await UserRepository.get_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
```

### 4. Frontend Token Management
```typescript
// Frontend: Auth context with token storage
const AuthContext = createContext<AuthContextType>({
  user: null,
  login: async (token: string) => {
    localStorage.setItem('access_token', token);
    // Decode and set user info
  },
  logout: () => {
    localStorage.removeItem('access_token');
    setUser(null);
  }
});
```

## Security Features

### Token Security
- **JWT Expiration**: 15-minute access tokens, 7-day refresh tokens
- **Token Rotation**: New tokens issued on refresh
- **Secure Storage**: HttpOnly cookies for refresh tokens
- **Token Blacklisting**: Revoked tokens tracked in Redis

### OAuth Security
- **State Parameter**: CSRF protection for OAuth flows
- **PKCE**: Proof Key for Code Exchange for public clients
- **Scope Limitation**: Minimal OAuth scopes requested
- **Provider Validation**: Strict validation of OAuth provider responses

### Session Management
- **Session Timeout**: Automatic logout after 24 hours of inactivity
- **Concurrent Sessions**: Support for multiple active sessions
- **Device Tracking**: Optional device fingerprinting
- **Session Revocation**: Ability to revoke all sessions for a user

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR UNIQUE,
    hashed_password VARCHAR,  -- NULL for OAuth-only users
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,

    -- OAuth fields
    oauth_provider VARCHAR,  -- 'google', 'linkedin', 'github'
    oauth_id VARCHAR,        -- External provider user ID
    oauth_access_token VARCHAR,
    oauth_refresh_token VARCHAR,
    oauth_token_expires TIMESTAMP,

    -- Profile data
    first_name VARCHAR,
    last_name VARCHAR,
    profile_picture_url VARCHAR,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_oauth_provider_id ON users(oauth_provider, oauth_id);
```

### Sessions Table (Optional)
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR UNIQUE NOT NULL,
    device_info JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true
);
```

## Error Handling

### Authentication Errors
- **Invalid Token**: 401 Unauthorized with token refresh suggestion
- **Expired Token**: 401 with automatic refresh attempt
- **Invalid OAuth Code**: 400 Bad Request with retry option
- **User Not Found**: 404 with account creation prompt

### OAuth Flow Errors
- **Provider Unavailable**: Retry with exponential backoff
- **Invalid Scope**: Clear error message with scope explanation
- **User Denied Access**: Graceful handling with alternative login options
- **Network Errors**: Retry logic with user feedback

## Testing Strategy

### Unit Tests
```python
def test_oauth_token_exchange():
    # Mock OAuth provider response
    mock_response = {"access_token": "mock_token", "token_type": "Bearer"}

    with patch('httpx.post') as mock_post:
        mock_post.return_value.json.return_value = mock_response

        result = exchange_code_for_token("mock_code")
        assert result["access_token"] == "mock_token"

def test_jwt_token_creation():
    user_id = 123
    token = create_jwt_token(user_id)

    # Decode and verify
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
```

### Integration Tests
```python
async def test_oauth_flow(client: TestClient, db: AsyncSession):
    # Mock Google OAuth response
    with patch('app.services.oauth_service.get_google_user_info') as mock_user:
        mock_user.return_value = {
            "id": "123456",
            "email": "test@example.com",
            "name": "Test User"
        }

        # Simulate OAuth callback
        response = client.get("/auth/oauth/google/callback?code=mock_code")
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data

        # Verify user was created
        user = await UserRepository.get_by_email(db, "test@example.com")
        assert user is not None
        assert user.oauth_provider == "google"
```

## Monitoring & Observability

### Authentication Metrics
- **Login Success Rate**: Percentage of successful authentications
- **OAuth Conversion Rate**: Users completing OAuth flow
- **Token Refresh Rate**: Frequency of token refreshes
- **Failed Login Attempts**: Security monitoring for brute force

### Performance Metrics
- **Token Validation Latency**: JWT decoding and verification time
- **OAuth Callback Latency**: End-to-end OAuth flow duration
- **Session Creation Rate**: New session establishment frequency
- **Database Query Performance**: User lookup and session queries

## Migration Strategies

### From Single-User to Multi-User
1. **Enable OAuth Providers**: Configure Google, LinkedIn OAuth
2. **Update User Model**: Add OAuth fields to existing users
3. **Migrate Sessions**: Convert single-user sessions to multi-user
4. **Update Frontend**: Add login/logout UI components
5. **Database Migration**: Add OAuth columns with proper constraints

### OAuth-Only Authentication
1. **Remove Password Fields**: Drop password-related columns
2. **Update Registration**: OAuth-only user creation
3. **Simplify Login Flow**: Direct OAuth provider redirects
4. **Update Dependencies**: Remove password validation logic

## Related Components

- [[auth-component|Authentication Component Reference]] - Detailed implementation
- [[users-component|Users Component]] - User profile management
- [[security-component|Security Component]] - Token validation and encryption
- [[api-auth|API Authentication]] - Endpoint protection patterns

---

*See also: [[system-architecture|System Architecture]], [[data-architecture|Data Architecture]], [[api-architecture|API Architecture]]*"