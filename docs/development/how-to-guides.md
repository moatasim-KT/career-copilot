# Development How-To Guides

This guide provides step-by-step instructions for common development tasks in the Career Copilot project. Each guide includes prerequisites, implementation steps, testing instructions, and best practices.

## Backend Development

### Adding a New API Endpoint

#### Prerequisites
- FastAPI router structure understanding
- Pydantic schema knowledge
- Service layer pattern familiarity
- Database model knowledge

#### Step-by-Step Implementation

1. **Define the Data Model** (if needed)
```python
# backend/app/models/new_feature.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class NewFeature(Base):
    __tablename__ = "new_features"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="new_features")
```

2. **Create Pydantic Schemas**
```python
# backend/app/schemas/new_feature.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NewFeatureBase(BaseModel):
    title: str
    description: Optional[str] = None

class NewFeatureCreate(NewFeatureBase):
    pass

class NewFeatureUpdate(NewFeatureBase):
    title: Optional[str] = None

class NewFeature(NewFeatureBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
```

3. **Implement Service Layer**
```python
# backend/app/services/new_feature_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.new_feature import NewFeature
from app.schemas.new_feature import NewFeatureCreate, NewFeatureUpdate
from .base_service import BaseService

class NewFeatureService(BaseService[NewFeature]):
    """New feature management service"""

    def __init__(self, db: Session):
        super().__init__(db)

    def get_user_features(self, user_id: int, skip: int = 0, limit: int = 100) -> List[NewFeature]:
        """Get features for a user"""
        return (
            self.db.query(NewFeature)
            .filter(NewFeature.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_user_feature(self, user_id: int, feature_data: NewFeatureCreate) -> NewFeature:
        """Create a new feature for a user"""
        feature = NewFeature(user_id=user_id, **feature_data.dict())
        self.db.add(feature)
        self.db.commit()
        self.db.refresh(feature)
        return feature

    def update_feature(self, feature_id: int, user_id: int, feature_data: NewFeatureUpdate) -> Optional[NewFeature]:
        """Update a feature (user can only update their own features)"""
        feature = (
            self.db.query(NewFeature)
            .filter(NewFeature.id == feature_id, NewFeature.user_id == user_id)
            .first()
        )

        if not feature:
            return None

        update_data = feature_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(feature, field, value)

        self.db.commit()
        self.db.refresh(feature)
        return feature
```

4. **Create API Router**
```python
# backend/app/api/v1/new_features.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.new_feature import NewFeature, NewFeatureCreate, NewFeatureUpdate
from app.services.new_feature_service import NewFeatureService

router = APIRouter(prefix="/new-features", tags=["new-features"])

@router.get("/", response_model=List[NewFeature])
def get_user_features(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's features"""
    service = NewFeatureService(db)
    return service.get_user_features(current_user.id, skip, limit)

@router.post("/", response_model=NewFeature, status_code=status.HTTP_201_CREATED)
def create_feature(
    feature_data: NewFeatureCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new feature"""
    service = NewFeatureService(db)
    return service.create_user_feature(current_user.id, feature_data)

@router.put("/{feature_id}", response_model=NewFeature)
def update_feature(
    feature_id: int,
    feature_data: NewFeatureUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a feature"""
    service = NewFeatureService(db)
    feature = service.update_feature(feature_id, current_user.id, feature_data)

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found or access denied"
        )

    return feature

@router.delete("/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feature(
    feature_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a feature"""
    service = NewFeatureService(db)
    feature = service.get_by_id(NewFeature, feature_id)

    if not feature or feature.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found or access denied"
        )

    service.delete(feature)
```

5. **Register Router in Main App**
```python
# backend/app/main.py
from app.api.v1.new_features import router as new_features_router

# Add to the router includes
app.include_router(new_features_router)
```

6. **Create Database Migration**
```bash
# Generate migration
alembic revision --autogenerate -m "add new_features table"

# Apply migration
alembic upgrade head
```

#### Testing the New Endpoint

1. **Unit Tests**
```python
# backend/tests/test_new_feature_service.py
import pytest
from app.services.new_feature_service import NewFeatureService
from app.schemas.new_feature import NewFeatureCreate

def test_create_user_feature(db_session, test_user):
    service = NewFeatureService(db_session)
    feature_data = NewFeatureCreate(title="Test Feature", description="Test description")

    feature = service.create_user_feature(test_user.id, feature_data)

    assert feature.title == "Test Feature"
    assert feature.user_id == test_user.id
    assert feature.description == "Test description"
```

2. **API Tests**
```python
# backend/tests/test_new_features_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_feature(client: AsyncClient, test_user_token):
    response = await client.post(
        "/api/v1/new-features/",
        json={"title": "Test Feature", "description": "Test description"},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Feature"
    assert data["description"] == "Test description"
```

#### Best Practices
- Always use dependency injection for database sessions
- Implement proper error handling and validation
- Add comprehensive tests for all endpoints
- Use meaningful status codes and error messages
- Document your API with OpenAPI decorators

### Implementing Caching

#### Prerequisites
- Redis setup and configuration
- Cache key generation strategy
- Cache invalidation patterns

#### Step-by-Step Implementation

1. **Configure Cache Backend**
```python
# backend/app/core/cache/redis_config.py
from redis.asyncio import Redis
from app.core.config import get_settings

settings = get_settings()

redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    max_connections=20
)

async def get_redis_client() -> Redis:
    """Get Redis client instance"""
    return redis_client
```

2. **Create Cache Manager**
```python
# backend/app/core/cache/cache_manager.py
from typing import Any, Optional, Dict
import json
import hashlib
from app.core.cache.redis_config import get_redis_client

class CacheManager:
    """Redis-based cache manager"""

    def __init__(self):
        self.redis = None

    async def get_client(self):
        """Lazy load Redis client"""
        if self.redis is None:
            self.redis = await get_redis_client()
        return self.redis

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from parameters"""
        key_parts = [prefix] + [str(arg) for arg in args]
        for k, v in sorted(kwargs.items()):
            key_parts.extend([k, str(v)])

        key_string = ":".join(key_parts)
        if len(key_string) > 250:
            key_string = hashlib.md5(key_string.encode()).hexdigest()

        return key_string

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        redis = await self.get_client()
        try:
            data = await redis.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        redis = await self.get_client()
        try:
            data = json.dumps(value)
            if ttl:
                await redis.setex(key, ttl, data)
            else:
                await redis.set(key, data)
        except Exception:
            pass  # Fail silently

    async def delete(self, key: str) -> None:
        """Delete from cache"""
        redis = await self.get_client()
        try:
            await redis.delete(key)
        except Exception:
            pass

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        redis = await self.get_client()
        try:
            return await redis.exists(key) > 0
        except Exception:
            return False

# Global instance
cache_manager = CacheManager()

def get_cache_manager() -> CacheManager:
    """Get cache manager instance"""
    return cache_manager
```

3. **Add Caching to Service**
```python
# backend/app/services/user_service.py
from app.core.cache.cache_manager import get_cache_manager

class UserService(BaseService[User]):
    def __init__(self, db: Session):
        super().__init__(db)
        self.cache = get_cache_manager()

    async def get_user_by_id_cached(self, user_id: int) -> Optional[User]:
        """Get user by ID with caching"""
        cache_key = self.cache.generate_key("user", user_id)

        # Try cache first
        cached_user = await self.cache.get(cache_key)
        if cached_user:
            return User(**cached_user)

        # Get from database
        user = self.get_by_id(User, user_id)
        if user:
            # Cache for 30 minutes
            await self.cache.set(cache_key, user.__dict__, ttl=1800)

        return user

    async def update_user_cached(self, user: User, user_data: UserUpdate) -> User:
        """Update user and invalidate cache"""
        updated_user = self.update_user(user, user_data)

        # Invalidate cache
        cache_key = self.cache.generate_key("user", user.id)
        await self.cache.delete(cache_key)

        return updated_user
```

4. **Add Cache Middleware**
```python
# backend/app/middleware/cache_middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.cache.cache_manager import get_cache_manager

class CacheMiddleware(BaseHTTPMiddleware):
    """HTTP caching middleware"""

    def __init__(self, app, cache_ttl: int = 300):
        super().__init__(app)
        self.cache = get_cache_manager()
        self.cache_ttl = cache_ttl

    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)

        # Generate cache key from request
        cache_key = f"response:{request.url.path}:{request.url.query}"

        # Try to get cached response
        cached_response = await self.cache.get(cache_key)
        if cached_response:
            return Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response["headers"]
            )

        # Get fresh response
        response = await call_next(request)

        # Cache the response if successful
        if response.status_code == 200:
            response_content = b""
            async for chunk in response.body_iterator:
                response_content += chunk

            cached_data = {
                "content": response_content.decode(),
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }

            await self.cache.set(cache_key, cached_data, ttl=self.cache_ttl)

            # Return new response with cached content
            return Response(
                content=response_content,
                status_code=response.status_code,
                headers=response.headers
            )

        return response
```

#### Testing Cache Implementation

```python
# backend/tests/test_cache.py
import pytest
from app.core.cache.cache_manager import CacheManager

@pytest.mark.asyncio
async def test_cache_set_get():
    cache = CacheManager()
    test_data = {"key": "value", "number": 42}

    await cache.set("test_key", test_data, ttl=60)
    result = await cache.get("test_key")

    assert result == test_data

@pytest.mark.asyncio
async def test_cache_expiration():
    cache = CacheManager()

    await cache.set("temp_key", "temp_value", ttl=1)
    result = await cache.get("temp_key")
    assert result == "temp_value"

    # Wait for expiration
    import asyncio
    await asyncio.sleep(2)

    result = await cache.get("temp_key")
    assert result is None
```

#### Best Practices
- Use descriptive cache keys with prefixes
- Set appropriate TTL values based on data freshness requirements
- Implement cache invalidation strategies
- Monitor cache hit rates and performance
- Handle cache failures gracefully (fail open)

### Setting Up WebSocket Connections

#### Prerequisites
- WebSocket protocol understanding
- FastAPI WebSocket support
- Connection management patterns
- Authentication over WebSockets

#### Step-by-Step Implementation

1. **Create WebSocket Manager**
```python
# backend/app/websockets/connection_manager.py
from typing import Dict, List, Set
import json
from fastapi import WebSocket
from app.core.logging import get_logger

logger = get_logger(__name__)

class ConnectionManager:
    """WebSocket connection manager"""

    def __init__(self):
        # active_connections[user_id] = set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and register a WebSocket connection"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

            logger.info(f"User {user_id} disconnected. Remaining connections: {len(self.active_connections.get(user_id, set()))}")

    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to specific user"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")
                    # Remove broken connection
                    self.active_connections[user_id].discard(connection)

    async def broadcast(self, message: dict, user_ids: List[int] = None):
        """Broadcast message to multiple users or all users"""
        if user_ids is None:
            user_ids = list(self.active_connections.keys())

        for user_id in user_ids:
            await self.send_personal_message(message, user_id)

    async def send_to_group(self, message: dict, group_name: str):
        """Send message to a group (requires group management)"""
        # Implementation depends on your grouping logic
        pass

    def get_active_connections_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())

    def get_user_connections_count(self, user_id: int) -> int:
        """Get number of connections for a specific user"""
        return len(self.active_connections.get(user_id, set()))

# Global instance
manager = ConnectionManager()

def get_connection_manager() -> ConnectionManager:
    """Get connection manager instance"""
    return manager
```

2. **Create WebSocket Authentication**
```python
# backend/app/websockets/auth.py
from fastapi import WebSocket, HTTPException, status
from jose import JWTError, jwt
from app.core.config import get_settings
from app.services.user_service import UserService
from app.core.database import get_db_session

async def get_current_user_from_websocket(websocket: WebSocket) -> int:
    """Authenticate WebSocket connection and return user ID"""
    # Get token from query parameters
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=400, detail="Token required")

    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
        email: str = payload.get("sub")

        if email is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=400, detail="Invalid token")

    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=400, detail="Invalid token")

    # Verify user exists
    db = get_db_session()
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_email(email)

        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=400, detail="User not found")

        if not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=400, detail="Inactive user")

        return user.id

    finally:
        db.close()
```

3. **Create WebSocket Endpoints**
```python
# backend/app/api/v1/websockets.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.websockets.connection_manager import get_connection_manager
from app.websockets.auth import get_current_user_from_websocket
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.websocket("/ws/notifications")
async def notification_websocket(
    websocket: WebSocket,
    current_user_id: int = Depends(get_current_user_from_websocket)
):
    """WebSocket endpoint for real-time notifications"""
    manager = get_connection_manager()

    try:
        await manager.connect(websocket, current_user_id)

        # Send welcome message
        await manager.send_personal_message({
            "type": "connection_established",
            "message": "Connected to notification service",
            "timestamp": "2024-01-01T00:00:00Z"
        }, current_user_id)

        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_json()

            # Handle client messages (ping, etc.)
            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": "2024-01-01T00:00:00Z"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {current_user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {current_user_id}: {e}")
    finally:
        manager.disconnect(websocket, current_user_id)

@router.websocket("/ws/applications/{application_id}")
async def application_websocket(
    websocket: WebSocket,
    application_id: int,
    current_user_id: int = Depends(get_current_user_from_websocket)
):
    """WebSocket endpoint for application-specific updates"""
    manager = get_connection_manager()

    # Verify user owns this application
    db = get_db_session()
    try:
        application_service = ApplicationService(db)
        application = application_service.get_by_id(Application, application_id)

        if not application or application.user_id != current_user_id:
            await websocket.close(code=1008)  # Policy violation
            return
    finally:
        db.close()

    try:
        await manager.connect(websocket, current_user_id)

        # Send initial application state
        await websocket.send_json({
            "type": "application_state",
            "application_id": application_id,
            "status": application.status,
            "last_updated": application.updated_at.isoformat()
        })

        while True:
            data = await websocket.receive_json()

            # Handle application-specific messages
            if data.get("type") == "update_status":
                new_status = data.get("status")
                # Update application status and notify
                # Implementation depends on your business logic

    except WebSocketDisconnect:
        logger.info(f"Application WebSocket disconnected for user {current_user_id}, app {application_id}")
    finally:
        manager.disconnect(websocket, current_user_id)
```

4. **Integrate with Services**
```python
# backend/app/services/notification_service.py
from app.websockets.connection_manager import get_connection_manager

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.ws_manager = get_connection_manager()

    async def send_notification(self, user_id: int, notification: dict):
        """Send notification via WebSocket"""
        await self.ws_manager.send_personal_message({
            "type": "notification",
            "data": notification,
            "timestamp": "2024-01-01T00:00:00Z"
        }, user_id)

    async def broadcast_system_message(self, message: str):
        """Broadcast system message to all users"""
        await self.ws_manager.broadcast({
            "type": "system_message",
            "message": message,
            "timestamp": "2024-01-01T00:00:00Z"
        })
```

#### Testing WebSocket Implementation

```python
# backend/tests/test_websockets.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_websocket_connection():
    client = TestClient(app)

    with client.websocket_connect("/ws/notifications?token=valid_token") as websocket:
        # Test connection
        data = websocket.receive_json()
        assert data["type"] == "connection_established"

        # Test ping-pong
        websocket.send_json({"type": "ping"})
        response = websocket.receive_json()
        assert response["type"] == "pong"
```

#### Best Practices
- Implement proper authentication for WebSocket connections
- Handle connection lifecycle events (connect/disconnect)
- Implement heartbeat/ping-pong for connection health
- Use connection pooling for scalability
- Handle errors gracefully and clean up broken connections
- Implement rate limiting for WebSocket messages

### Database Migrations

#### Prerequisites
- Alembic configuration
- SQLAlchemy model knowledge
- Database schema understanding

#### Step-by-Step Implementation

1. **Create Migration Script**
```bash
# Generate migration for model changes
alembic revision --autogenerate -m "add new_feature table"

# Or create empty migration for manual changes
alembic revision -m "custom migration"
```

2. **Edit Migration File**
```python
# backend/alembic/versions/1234567890ab_add_new_feature_table.py
"""add new_feature table

Revision ID: 1234567890ab
Revises: 9876543210fe
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1234567890ab'
down_revision: Union[str, None] = '9876543210fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade database schema"""
    # Create new table
    op.create_table('new_features',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_new_features_id'), 'new_features', ['id'], unique=False)
    op.create_index(op.f('ix_new_features_user_id'), 'new_features', ['user_id'], unique=False)

def downgrade() -> None:
    """Downgrade database schema"""
    op.drop_index(op.f('ix_new_features_user_id'), table_name='new_features')
    op.drop_index(op.f('ix_new_features_id'), table_name='new_features')
    op.drop_table('new_features')
```

3. **Apply Migration**
```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade 1234567890ab

# Check current migration status
alembic current

# Show migration history
alembic history
```

4. **Handle Data Migrations**
```python
# For migrations that need to transform data
def upgrade() -> None:
    # Create new table
    op.create_table('user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bio', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Migrate data from users table
    connection = op.get_bind()

    # Get existing user data
    result = connection.execute(sa.text("SELECT id, bio, avatar_url FROM users"))
    users_data = result.fetchall()

    # Insert into new table
    for user_id, bio, avatar_url in users_data:
        connection.execute(
            sa.text("INSERT INTO user_profiles (user_id, bio, avatar_url) VALUES (:user_id, :bio, :avatar_url)"),
            {"user_id": user_id, "bio": bio, "avatar_url": avatar_url}
        )

    # Remove columns from users table
    op.drop_column('users', 'bio')
    op.drop_column('users', 'avatar_url')
```

#### Testing Migrations

```python
# backend/tests/test_migrations.py
import pytest
from alembic.config import Config
from alembic import command
from app.core.database import get_db_url

def test_migration_upgrade_downgrade():
    """Test that migrations can be applied and rolled back"""
    # Create Alembic config
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", get_db_url())

    # Apply all migrations
    command.upgrade(alembic_cfg, "head")

    # Rollback one migration
    command.downgrade(alembic_cfg, "-1")

    # Apply again
    command.upgrade(alembic_cfg, "head")
```

#### Best Practices
- Always test migrations on a copy of production data
- Create reversible migrations when possible
- Use descriptive migration messages
- Keep migrations small and focused
- Backup database before applying migrations
- Test both upgrade and downgrade paths

## Frontend Development

### Adding a New React Component

#### Prerequisites
- React fundamentals
- TypeScript knowledge
- Component composition patterns
- State management understanding

#### Step-by-Step Implementation

1. **Create Component Structure**
```typescript
// frontend/src/components/features/NewFeature/NewFeature.tsx
import React, { useState, useEffect } from 'react';
import { useApi } from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';

interface NewFeatureProps {
  userId: number;
  onFeatureCreated?: (feature: NewFeature) => void;
}

interface NewFeature {
  id: number;
  title: string;
  description?: string;
  created_at: string;
}

export const NewFeature: React.FC<NewFeatureProps> = ({ userId, onFeatureCreated }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { execute: createFeature, loading, error } = useApi<NewFeature>('/new-features', {
    onSuccess: (feature) => {
      onFeatureCreated?.(feature);
      setTitle('');
      setDescription('');
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) return;

    setIsSubmitting(true);
    try {
      await createFeature({
        title: title.trim(),
        description: description.trim() || undefined
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Create New Feature</h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Title *
          </label>
          <Input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter feature title"
            required
            disabled={loading}
          />
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter feature description"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={3}
            disabled={loading}
          />
        </div>

        {error && (
          <div className="text-red-600 text-sm">
            {error}
          </div>
        )}

        <Button
          type="submit"
          disabled={loading || !title.trim()}
          loading={loading}
        >
          {loading ? 'Creating...' : 'Create Feature'}
        </Button>
      </form>
    </Card>
  );
};
```

2. **Create Component Index**
```typescript
// frontend/src/components/features/NewFeature/index.ts
export { NewFeature } from './NewFeature';
export type { NewFeatureProps } from './NewFeature';
```

3. **Add to Feature Components**
```typescript
// frontend/src/components/features/index.ts
export { NewFeature } from './NewFeature';
```

4. **Create Tests**
```typescript
// frontend/tests/components/NewFeature.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NewFeature } from '@/components/features/NewFeature';

// Mock the API hook
jest.mock('@/hooks/useApi');

describe('NewFeature', () => {
  const mockExecute = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock useApi hook
    require('@/hooks/useApi').useApi = jest.fn(() => ({
      execute: mockExecute,
      loading: false,
      error: null
    }));
  });

  it('renders form correctly', () => {
    render(<NewFeature userId={1} />);

    expect(screen.getByText('Create New Feature')).toBeInTheDocument();
    expect(screen.getByLabelText('Title *')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create Feature' })).toBeInTheDocument();
  });

  it('submits form with valid data', async () => {
    mockExecute.mockResolvedValueOnce({
      id: 1,
      title: 'Test Feature',
      description: 'Test description',
      created_at: '2024-01-01T00:00:00Z'
    });

    render(<NewFeature userId={1} />);

    fireEvent.change(screen.getByLabelText('Title *'), {
      target: { value: 'Test Feature' }
    });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Test description' }
    });

    fireEvent.click(screen.getByRole('button', { name: 'Create Feature' }));

    await waitFor(() => {
      expect(mockExecute).toHaveBeenCalledWith({
        title: 'Test Feature',
        description: 'Test description'
      });
    });
  });

  it('shows error message on API error', async () => {
    const mockUseApi = require('@/hooks/useApi').useApi;
    mockUseApi.mockReturnValue({
      execute: mockExecute,
      loading: false,
      error: 'API Error'
    });

    render(<NewFeature userId={1} />);

    expect(screen.getByText('API Error')).toBeInTheDocument();
  });

  it('calls onFeatureCreated callback on success', async () => {
    const mockOnFeatureCreated = jest.fn();
    const mockFeature = {
      id: 1,
      title: 'Test Feature',
      description: 'Test description',
      created_at: '2024-01-01T00:00:00Z'
    };

    mockExecute.mockResolvedValueOnce(mockFeature);

    render(<NewFeature userId={1} onFeatureCreated={mockOnFeatureCreated} />);

    fireEvent.change(screen.getByLabelText('Title *'), {
      target: { value: 'Test Feature' }
    });
    fireEvent.click(screen.getByRole('button', { name: 'Create Feature' }));

    await waitFor(() => {
      expect(mockOnFeatureCreated).toHaveBeenCalledWith(mockFeature);
    });
  });
});
```

#### Best Practices
- Use TypeScript for type safety
- Implement proper error handling
- Add loading states for better UX
- Write comprehensive tests
- Follow component composition patterns
- Use custom hooks for reusable logic

### Implementing Form Validation

#### Prerequisites
- React Hook Form knowledge
- Validation library familiarity
- Schema validation understanding

#### Step-by-Step Implementation

1. **Install Dependencies**
```bash
npm install react-hook-form @hookform/resolvers zod
```

2. **Create Validation Schema**
```typescript
// frontend/src/schemas/newFeature.ts
import { z } from 'zod';

export const newFeatureSchema = z.object({
  title: z
    .string()
    .min(1, 'Title is required')
    .max(100, 'Title must be less than 100 characters')
    .trim(),
  description: z
    .string()
    .max(500, 'Description must be less than 500 characters')
    .optional(),
  priority: z
    .enum(['low', 'medium', 'high'], {
      errorMap: () => ({ message: 'Please select a priority level' })
    }),
  tags: z
    .array(z.string().min(1).max(20))
    .max(5, 'Maximum 5 tags allowed')
    .optional()
});

export type NewFeatureFormData = z.infer<typeof newFeatureSchema>;
```

3. **Create Validated Form Component**
```typescript
// frontend/src/components/forms/NewFeatureForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { Badge } from '@/components/ui/Badge';
import { newFeatureSchema, NewFeatureFormData } from '@/schemas/newFeature';

interface NewFeatureFormProps {
  onSubmit: (data: NewFeatureFormData) => Promise<void>;
  loading?: boolean;
}

export const NewFeatureForm: React.FC<NewFeatureFormProps> = ({ onSubmit, loading }) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
    setValue,
    reset
  } = useForm<NewFeatureFormData>({
    resolver: zodResolver(newFeatureSchema),
    defaultValues: {
      priority: 'medium',
      tags: []
    }
  });

  const tags = watch('tags') || [];
  const [tagInput, setTagInput] = React.useState('');

  const addTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim()) && tags.length < 5) {
      setValue('tags', [...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setValue('tags', tags.filter(tag => tag !== tagToRemove));
  };

  const handleFormSubmit = async (data: NewFeatureFormData) => {
    await onSubmit(data);
    reset();
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Title Field */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Title *
        </label>
        <Input
          {...register('title')}
          placeholder="Enter feature title"
          error={errors.title?.message}
        />
      </div>

      {/* Description Field */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description
        </label>
        <Textarea
          {...register('description')}
          placeholder="Describe the feature..."
          rows={4}
          error={errors.description?.message}
        />
      </div>

      {/* Priority Field */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Priority *
        </label>
        <Select {...register('priority')} error={errors.priority?.message}>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </Select>
      </div>

      {/* Tags Field */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tags
        </label>
        <div className="flex gap-2 mb-2">
          <Input
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            placeholder="Add a tag"
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
          />
          <Button type="button" onClick={addTag} variant="outline">
            Add
          </Button>
        </div>
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="cursor-pointer" onClick={() => removeTag(tag)}>
                {tag} ×
              </Badge>
            ))}
          </div>
        )}
        {errors.tags && (
          <p className="text-red-600 text-sm mt-1">{errors.tags.message}</p>
        )}
      </div>

      {/* Submit Button */}
      <Button
        type="submit"
        disabled={isSubmitting || loading}
        loading={isSubmitting || loading}
        className="w-full"
      >
        Create Feature
      </Button>
    </form>
  );
};
```

4. **Create Form Tests**
```typescript
// frontend/tests/components/forms/NewFeatureForm.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NewFeatureForm } from '@/components/forms/NewFeatureForm';

describe('NewFeatureForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders all form fields', () => {
    render(<NewFeatureForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText('Title *')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
    expect(screen.getByLabelText('Priority *')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Add a tag')).toBeInTheDocument();
  });

  it('shows validation errors for required fields', async () => {
    render(<NewFeatureForm onSubmit={mockOnSubmit} />);

    fireEvent.click(screen.getByRole('button', { name: 'Create Feature' }));

    await waitFor(() => {
      expect(screen.getByText('Title is required')).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    mockOnSubmit.mockResolvedValueOnce(undefined);

    render(<NewFeatureForm onSubmit={mockOnSubmit} />);

    fireEvent.change(screen.getByLabelText('Title *'), {
      target: { value: 'Test Feature' }
    });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Test description' }
    });

    fireEvent.click(screen.getByRole('button', { name: 'Create Feature' }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        title: 'Test Feature',
        description: 'Test description',
        priority: 'medium',
        tags: []
      });
    });
  });

  it('handles tag addition and removal', () => {
    render(<NewFeatureForm onSubmit={mockOnSubmit} />);

    const tagInput = screen.getByPlaceholderText('Add a tag');
    const addButton = screen.getByRole('button', { name: 'Add' });

    fireEvent.change(tagInput, { target: { value: 'urgent' } });
    fireEvent.click(addButton);

    expect(screen.getByText('urgent ×')).toBeInTheDocument();

    fireEvent.click(screen.getByText('urgent ×'));
    expect(screen.queryByText('urgent ×')).not.toBeInTheDocument();
  });

  it('prevents adding duplicate tags', () => {
    render(<NewFeatureForm onSubmit={mockOnSubmit} />);

    const tagInput = screen.getByPlaceholderText('Add a tag');
    const addButton = screen.getByRole('button', { name: 'Add' });

    fireEvent.change(tagInput, { target: { value: 'test' } });
    fireEvent.click(addButton);
    fireEvent.change(tagInput, { target: { value: 'test' } });
    fireEvent.click(addButton);

    expect(screen.getAllByText('test ×')).toHaveLength(1);
  });
});
```

#### Best Practices
- Use schema-based validation (Zod, Yup)
- Provide clear error messages
- Implement real-time validation
- Handle async validation for unique fields
- Test validation edge cases
- Use proper form accessibility

---

*See also: [[code-examples|Code Examples]], [[testing-strategies|Testing Strategies]], [[api-reference|API Reference]]*"