# Code Example Library

This library contains practical, reusable code examples extracted from the Career Copilot codebase. Each example demonstrates common patterns and best practices for development.

## Backend Patterns

### Service Layer Pattern

#### Basic Service Structure
```python
# backend/app/services/base_service.py
from typing import Generic, TypeVar, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel

T = TypeVar('T')

class BaseService(Generic[T]):
    """Base service class providing common CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, model_class: T, id: int) -> Optional[T]:
        """Get entity by ID"""
        return self.db.get(model_class, id)

    def get_all(self, model_class: T, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        stmt = select(model_class).offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return result.scalars().all()

    def create(self, model_class: T, data: BaseModel) -> T:
        """Create new entity"""
        entity = model_class(**data.dict())
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: T, data: BaseModel) -> T:
        """Update existing entity"""
        for field, value in data.dict(exclude_unset=True).items():
            setattr(entity, field, value)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: T) -> None:
        """Delete entity"""
        self.db.delete(entity)
        self.db.commit()
```

#### User Service Implementation
```python
# backend/app/services/user_service.py
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from .base_service import BaseService

class UserService(BaseService[User]):
    """User management service"""

    def __init__(self, db: Session):
        super().__init__(db)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        stmt = select(User).where(User.email == email)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def create_user(self, user_data: UserCreate) -> User:
        """Create new user with hashed password"""
        hashed_password = get_password_hash(user_data.password)
        user_dict = user_data.dict()
        user_dict['hashed_password'] = hashed_password
        del user_dict['password']

        user = User(**user_dict)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user: User, user_data: UserUpdate) -> User:
        """Update user information"""
        update_data = user_data.dict(exclude_unset=True)

        # Handle password updates separately
        if 'password' in update_data:
            update_data['hashed_password'] = get_password_hash(update_data['password'])
            del update_data['password']

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user
```

### Repository Pattern

#### Base Repository
```python
# backend/app/repositories/base_repository.py
from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.sql import Select

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository providing common database operations"""

    def __init__(self, db: Session, model_class: T):
        self.db = db
        self.model_class = model_class

    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by primary key"""
        return self.db.get(self.model_class, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        stmt = select(self.model_class).offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return result.scalars().all()

    def create(self, **kwargs) -> T:
        """Create new entity"""
        entity = self.model_class(**kwargs)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, id: int, **kwargs) -> Optional[T]:
        """Update entity by ID"""
        stmt = (
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**kwargs)
        )
        self.db.execute(stmt)
        self.db.commit()

        return self.get_by_id(id)

    def delete(self, id: int) -> bool:
        """Delete entity by ID"""
        entity = self.get_by_id(id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters"""
        stmt = select(func.count()).select_from(self.model_class)

        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    conditions.append(getattr(self.model_class, field) == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = self.db.execute(stmt)
        return result.scalar()

    def exists(self, id: int) -> bool:
        """Check if entity exists"""
        stmt = select(func.count()).select_from(self.model_class).where(self.model_class.id == id)
        result = self.db.execute(stmt)
        return result.scalar() > 0

    def filter_by(self, **filters) -> List[T]:
        """Filter entities by field values"""
        conditions = []
        for field, value in filters.items():
            if hasattr(self.model_class, field):
                conditions.append(getattr(self.model_class, field) == value)

        stmt = select(self.model_class)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = self.db.execute(stmt)
        return result.scalars().all()
```

#### Application Repository
```python
# backend/app/repositories/application_repository.py
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy import select, and_, or_, func, desc
from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from .base_repository import BaseRepository

class ApplicationRepository(BaseRepository[Application]):
    """Repository for job applications"""

    def __init__(self, db):
        super().__init__(db, Application)

    def get_user_applications(self, user_id: int, status: Optional[str] = None,
                            skip: int = 0, limit: int = 100) -> List[Application]:
        """Get applications for a user with optional status filter"""
        stmt = (
            select(Application)
            .where(Application.user_id == user_id)
            .options(joinedload(Application.job))
        )

        if status:
            stmt = stmt.where(Application.status == status)

        stmt = stmt.offset(skip).limit(limit).order_by(desc(Application.created_at))

        result = self.db.execute(stmt)
        return result.scalars().all()

    def get_application_with_details(self, application_id: int) -> Optional[Application]:
        """Get application with job and user details"""
        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(
                joinedload(Application.job),
                joinedload(Application.user)
            )
        )

        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_applications_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Application]:
        """Get applications by status"""
        stmt = (
            select(Application)
            .where(Application.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(desc(Application.updated_at))
        )

        result = self.db.execute(stmt)
        return result.scalars().all()

    def get_applications_by_date_range(self, start_date: date, end_date: date) -> List[Application]:
        """Get applications within date range"""
        stmt = (
            select(Application)
            .where(
                and_(
                    Application.created_at >= start_date,
                    Application.created_at <= end_date
                )
            )
            .order_by(desc(Application.created_at))
        )

        result = self.db.execute(stmt)
        return result.scalars().all()

    def get_application_stats(self, user_id: int) -> Dict[str, Any]:
        """Get application statistics for a user"""
        # Total applications
        total_stmt = select(func.count()).where(Application.user_id == user_id)
        total = self.db.execute(total_stmt).scalar()

        # Applications by status
        status_stmt = (
            select(Application.status, func.count())
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        status_counts = dict(self.db.execute(status_stmt).all())

        # Recent applications (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_stmt = (
            select(func.count())
            .where(
                and_(
                    Application.user_id == user_id,
                    Application.created_at >= thirty_days_ago
                )
            )
        )
        recent = self.db.execute(recent_stmt).scalar()

        return {
            'total_applications': total,
            'status_breakdown': status_counts,
            'recent_applications': recent
        }
```

### Dependency Injection Pattern

#### FastAPI Dependency Injection
```python
# backend/app/core/dependencies.py
from typing import Generator, Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.database import get_db
from app.core.config import get_settings
from app.models.user import User
from app.services.user_service import UserService

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_service = UserService(db)
    user = user_service.get_user_by_email(email)
    if user is None:
        raise credentials_exception

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency for UserService"""
    return UserService(db)

def get_application_service(db: Session = Depends(get_db)) -> ApplicationService:
    """Dependency for ApplicationService"""
    return ApplicationService(db)

def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency for AnalyticsService"""
    return AnalyticsService(db)

# Optional dependencies (don't fail if service unavailable)
def get_optional_notification_service(db: Session = Depends(get_db)) -> Optional[NotificationService]:
    """Optional dependency for NotificationService"""
    try:
        return NotificationService(db)
    except Exception:
        return None
```

#### Service Factory Pattern
```python
# backend/app/core/service_factory.py
from typing import Dict, Type, Any
from sqlalchemy.orm import Session
from app.services.base_service import BaseService

class ServiceFactory:
    """Factory for creating service instances"""

    _services: Dict[str, Type[BaseService]] = {}

    @classmethod
    def register_service(cls, name: str, service_class: Type[BaseService]):
        """Register a service class"""
        cls._services[name] = service_class

    @classmethod
    def create_service(cls, name: str, db: Session, **kwargs) -> BaseService:
        """Create service instance"""
        if name not in cls._services:
            raise ValueError(f"Service '{name}' not registered")

        service_class = cls._services[name]
        return service_class(db, **kwargs)

    @classmethod
    def get_registered_services(cls) -> Dict[str, Type[BaseService]]:
        """Get all registered services"""
        return cls._services.copy()

# Register services at startup
def register_all_services():
    """Register all available services"""
    from app.services.user_service import UserService
    from app.services.application_service import ApplicationService
    from app.services.analytics_service import AnalyticsService
    from app.services.notification_service import NotificationService

    ServiceFactory.register_service('user', UserService)
    ServiceFactory.register_service('application', ApplicationService)
    ServiceFactory.register_service('analytics', AnalyticsService)
    ServiceFactory.register_service('notification', NotificationService)

# Call during app startup
register_all_services()
```

### Background Task Pattern

#### Celery Task Structure
```python
# backend/app/tasks/base_task.py
from celery import Task
from app.core.database import get_db_session
from app.core.logging import get_logger

logger = get_logger(__name__)

class BaseTask(Task):
    """Base class for all Celery tasks"""

    def __init__(self):
        self.db_session = None

    def before_start(self, task_id, args, kwargs):
        """Setup before task execution"""
        logger.info(f"Starting task {task_id}")
        self.db_session = get_db_session()

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Cleanup after task execution"""
        if self.db_session:
            self.db_session.close()
        logger.info(f"Task {task_id} completed with status: {status}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {exc}")
        # Send notification or alert
        self._send_failure_notification(task_id, exc)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        logger.warning(f"Retrying task {task_id}: {exc}")

    def _send_failure_notification(self, task_id: str, exception: Exception):
        """Send notification about task failure"""
        # Implementation for sending alerts
        pass

    def get_db_session(self):
        """Get database session for task"""
        return self.db_session or get_db_session()
```

#### Job Scraping Task
```python
# backend/app/tasks/job_scraping_tasks.py
from typing import List, Dict, Any
from app.tasks.base_task import BaseTask
from app.services.job_scraper import JobScraper
from app.services.job_service import JobService
from app.services.deduplication_service import DeduplicationService
from app.core.logging import get_logger

logger = get_logger(__name__)

@celery_app.task(bind=True, base=BaseTask, max_retries=3)
def scrape_jobs_task(self, sources: List[str] = None) -> Dict[str, Any]:
    """
    Scrape jobs from configured sources

    Args:
        sources: List of sources to scrape (optional)

    Returns:
        Dict with scraping results
    """
    try:
        scraper = JobScraper()
        service = JobService(self.get_db_session())
        deduplicator = DeduplicationService()

        all_jobs = []
        total_processed = 0
        total_duplicates = 0

        # Default sources if none specified
        if not sources:
            sources = ['linkedin', 'indeed', 'stepstone']

        for source in sources:
            logger.info(f"Scraping jobs from {source}")

            try:
                # Scrape jobs from source
                jobs_data = scraper.scrape_source(source)

                for job_data in jobs_data:
                    total_processed += 1

                    # Check for duplicates
                    if deduplicator.is_duplicate(job_data):
                        total_duplicates += 1
                        continue

                    # Save job
                    job = service.create_job_from_scraped_data(job_data)
                    all_jobs.append(job)

                    # Update progress
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'source': source,
                            'processed': total_processed,
                            'duplicates': total_duplicates,
                            'saved': len(all_jobs)
                        }
                    )

            except Exception as e:
                logger.error(f"Failed to scrape {source}: {e}")
                # Continue with other sources
                continue

        result = {
            'total_processed': total_processed,
            'total_duplicates': total_duplicates,
            'total_saved': len(all_jobs),
            'sources_processed': sources
        }

        logger.info(f"Job scraping completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Job scraping task failed: {e}")
        raise self.retry(countdown=60 * (self.request.retries + 1))

@celery_app.task(bind=True, base=BaseTask)
def update_job_statuses_task(self) -> Dict[str, Any]:
    """Update job statuses (expired, etc.)"""
    try:
        service = JobService(self.get_db_session())

        updated_count = service.update_expired_jobs()
        deactivated_count = service.deactivate_old_jobs()

        result = {
            'updated_jobs': updated_count,
            'deactivated_jobs': deactivated_count
        }

        logger.info(f"Job status update completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Job status update failed: {e}")
        raise
```

### Caching Pattern

#### Multi-Level Caching
```python
# backend/app/core/cache/cache_manager.py
from typing import Any, Optional, Dict, List
from abc import ABC, abstractmethod
import json
import hashlib
from datetime import datetime, timedelta
from app.core.redis_client import get_redis_client
from app.core.logging import get_logger

logger = get_logger(__name__)

class CacheBackend(ABC):
    """Abstract base class for cache backends"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

class RedisCacheBackend(CacheBackend):
    """Redis-based cache backend"""

    def __init__(self):
        self.redis = get_redis_client()

    async def get(self, key: str) -> Optional[Any]:
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        try:
            data = json.dumps(value)
            if ttl:
                await self.redis.setex(key, ttl, data)
            else:
                await self.redis.set(key, data)
        except Exception as e:
            logger.error(f"Redis cache set error: {e}")

    async def delete(self, key: str) -> None:
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")

    async def exists(self, key: str) -> bool:
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis cache exists error: {e}")
            return False

class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend for development"""

    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}

    async def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            entry = self.cache[key]
            if entry['expires_at'] > datetime.utcnow():
                return entry['value']
            else:
                del self.cache[key]
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl else datetime.max
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at
        }

    async def delete(self, key: str) -> None:
        self.cache.pop(key, None)

    async def exists(self, key: str) -> bool:
        return key in self.cache and self.cache[key]['expires_at'] > datetime.utcnow()

class MultiLevelCache:
    """Multi-level caching with L1 (memory) and L2 (Redis)"""

    def __init__(self, l1_cache: CacheBackend, l2_cache: CacheBackend):
        self.l1_cache = l1_cache  # Fast memory cache
        self.l2_cache = l2_cache  # Persistent Redis cache

    async def get(self, key: str) -> Optional[Any]:
        """Get from cache with fallback"""
        # Try L1 cache first
        value = await self.l1_cache.get(key)
        if value is not None:
            return value

        # Try L2 cache
        value = await self.l2_cache.get(key)
        if value is not None:
            # Populate L1 cache
            await self.l1_cache.set(key, value, ttl=300)  # 5 minutes
            return value

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set in both cache levels"""
        # Set in both caches
        await self.l1_cache.set(key, value, ttl=min(ttl or 3600, 300))  # Max 5 min for L1
        await self.l2_cache.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        """Delete from both cache levels"""
        await self.l1_cache.delete(key)
        await self.l2_cache.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in any cache level"""
        return await self.l1_cache.exists(key) or await self.l2_cache.exists(key)

class CacheManager:
    """High-level cache manager with key generation and patterns"""

    def __init__(self, cache: MultiLevelCache):
        self.cache = cache

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from parameters"""
        key_parts = [prefix] + [str(arg) for arg in args]

        # Add sorted kwargs
        for k, v in sorted(kwargs.items()):
            key_parts.extend([k, str(v)])

        key_string = ":".join(key_parts)

        # Create hash for long keys
        if len(key_string) > 250:
            key_string = hashlib.md5(key_string.encode()).hexdigest()

        return key_string

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data from cache"""
        key = self.generate_key("user", user_id)
        return await self.cache.get(key)

    async def set_user(self, user_id: int, user_data: Dict[str, Any]) -> None:
        """Cache user data"""
        key = self.generate_key("user", user_id)
        await self.cache.set(key, user_data, ttl=1800)  # 30 minutes

    async def get_user_applications(self, user_id: int, page: int = 1, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Get user applications from cache"""
        key = self.generate_key("user_applications", user_id, page=page, limit=limit)
        return await self.cache.get(key)

    async def set_user_applications(self, user_id: int, applications: List[Dict[str, Any]], page: int = 1, limit: int = 20) -> None:
        """Cache user applications"""
        key = self.generate_key("user_applications", user_id, page=page, limit=limit)
        await self.cache.set(key, applications, ttl=600)  # 10 minutes

    async def invalidate_user_cache(self, user_id: int) -> None:
        """Invalidate all user-related cache"""
        # Delete specific keys
        user_key = self.generate_key("user", user_id)
        await self.cache.delete(user_key)

        # Note: For applications, we might need to delete multiple pages
        # In practice, you might use key patterns or cache tags
```

## Frontend Patterns

### React Hook Patterns

#### Custom Data Fetching Hook
```typescript
// frontend/src/hooks/useApi.ts
import { useState, useEffect, useCallback } from 'react';
import { fetchApi } from '@/lib/api/client';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiOptions {
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: string) => void;
}

export function useApi<T>(
  endpoint: string,
  options: UseApiOptions = {}
) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(async (params?: Record<string, any>) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await fetchApi<T>(endpoint, { params });

      if (response.error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error: response.error
        }));
        options.onError?.(response.error);
      } else {
        setState(prev => ({
          ...prev,
          data: response.data,
          loading: false,
          error: null
        }));
        options.onSuccess?.(response.data);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage
      }));
      options.onError?.(errorMessage);
    }
  }, [endpoint, options]);

  useEffect(() => {
    if (options.immediate) {
      execute();
    }
  }, [execute, options.immediate]);

  return {
    ...state,
    execute,
    refetch: () => execute(),
  };
}
```

#### Form Management Hook
```typescript
// frontend/src/hooks/useForm.ts
import { useState, useCallback, useRef } from 'react';

interface FormState<T> {
  values: T;
  errors: Partial<Record<keyof T, string>>;
  touched: Partial<Record<keyof T, boolean>>;
  isSubmitting: boolean;
  isValid: boolean;
}

interface FormOptions<T> {
  initialValues: T;
  validate?: (values: T) => Partial<Record<keyof T, string>>;
  onSubmit: (values: T) => Promise<void> | void;
}

export function useForm<T extends Record<string, any>>({
  initialValues,
  validate,
  onSubmit,
}: FormOptions<T>) {
  const [state, setState] = useState<FormState<T>>({
    values: initialValues,
    errors: {},
    touched: {},
    isSubmitting: false,
    isValid: true,
  });

  const validateRef = useRef(validate);

  const setFieldValue = useCallback((field: keyof T, value: any) => {
    setState(prev => ({
      ...prev,
      values: {
        ...prev.values,
        [field]: value,
      },
    }));
  }, []);

  const setFieldTouched = useCallback((field: keyof T, touched: boolean = true) => {
    setState(prev => ({
      ...prev,
      touched: {
        ...prev.touched,
        [field]: touched,
      },
    }));
  }, []);

  const setFieldError = useCallback((field: keyof T, error: string | null) => {
    setState(prev => ({
      ...prev,
      errors: {
        ...prev.errors,
        [field]: error || undefined,
      },
    }));
  }, []);

  const validateForm = useCallback(() => {
    if (!validateRef.current) return {};

    const errors = validateRef.current(state.values);
    setState(prev => ({
      ...prev,
      errors,
      isValid: Object.keys(errors).length === 0,
    }));

    return errors;
  }, [state.values]);

  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault();

    const errors = validateForm();
    if (Object.keys(errors).length > 0) return;

    setState(prev => ({ ...prev, isSubmitting: true }));

    try {
      await onSubmit(state.values);
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setState(prev => ({ ...prev, isSubmitting: false }));
    }
  }, [state.values, validateForm, onSubmit]);

  const reset = useCallback(() => {
    setState({
      values: initialValues,
      errors: {},
      touched: {},
      isSubmitting: false,
      isValid: true,
    });
  }, [initialValues]);

  const getFieldProps = useCallback((field: keyof T) => ({
    value: state.values[field],
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => {
      setFieldValue(field, e.target.value);
    },
    onBlur: () => setFieldTouched(field),
    error: state.errors[field],
    touched: state.touched[field],
  }), [state.values, state.errors, state.touched, setFieldValue, setFieldTouched]);

  return {
    values: state.values,
    errors: state.errors,
    touched: state.touched,
    isSubmitting: state.isSubmitting,
    isValid: state.isValid,
    setFieldValue,
    setFieldTouched,
    setFieldError,
    validateForm,
    handleSubmit,
    reset,
    getFieldProps,
  };
}
```

### Component Patterns

#### Data Table Component
```typescript
// frontend/src/components/ui/DataTable.tsx
import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, Search, Filter } from 'lucide-react';

interface Column<T> {
  key: keyof T;
  header: string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, item: T) => React.ReactNode;
  width?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  searchable?: boolean;
  pageSize?: number;
  onRowClick?: (item: T) => void;
  className?: string;
}

export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  loading = false,
  searchable = true,
  pageSize = 10,
  onRowClick,
  className = '',
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortColumn, setSortColumn] = useState<keyof T | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);

  // Filter and sort data
  const filteredAndSortedData = useMemo(() => {
    let filtered = data;

    // Apply search filter
    if (searchTerm) {
      filtered = data.filter(item =>
        Object.values(item).some(value =>
          String(value).toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    }

    // Apply sorting
    if (sortColumn) {
      filtered = [...filtered].sort((a, b) => {
        const aValue = a[sortColumn];
        const bValue = b[sortColumn];

        if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  }, [data, searchTerm, sortColumn, sortDirection]);

  // Paginate data
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return filteredAndSortedData.slice(startIndex, startIndex + pageSize);
  }, [filteredAndSortedData, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredAndSortedData.length / pageSize);

  const handleSort = (column: keyof T) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {/* Search */}
      {searchable && (
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border rounded-lg w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                    column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                  }`}
                  style={{ width: column.width }}
                  onClick={() => column.sortable && handleSort(column.key)}
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.header}</span>
                    {column.sortable && sortColumn === column.key && (
                      sortDirection === 'asc' ?
                        <ChevronUp className="h-4 w-4" /> :
                        <ChevronDown className="h-4 w-4" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedData.map((item, index) => (
              <tr
                key={index}
                className={onRowClick ? 'cursor-pointer hover:bg-gray-50' : ''}
                onClick={() => onRowClick?.(item)}
              >
                {columns.map((column) => (
                  <td key={String(column.key)} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {column.render ?
                      column.render(item[column.key], item) :
                      String(item[column.key])
                    }
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-4 py-3 border-t flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, filteredAndSortedData.length)} of {filteredAndSortedData.length} results
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

#### Modal Component
```typescript
// frontend/src/components/ui/Modal.tsx
import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  closeOnOverlayClick?: boolean;
  showCloseButton?: boolean;
}

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  closeOnOverlayClick = true,
  showCloseButton = true,
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (closeOnOverlayClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50"
      onClick={handleOverlayClick}
    >
      <div
        ref={modalRef}
        className={`bg-white rounded-lg shadow-xl w-full ${sizeClasses[size]} max-h-[90vh] overflow-hidden`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-6 border-b">
            {title && (
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            )}
            {showCloseButton && (
              <button
                onClick={onClose}
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="h-5 w-5 text-gray-400" />
              </button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-8rem)]">
          {children}
        </div>
      </div>
    </div>
  );
}
```

## Testing Patterns

### Backend Testing Patterns

#### Service Testing
```python
# backend/tests/test_user_service.py
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class TestUserService:
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def user_service(self, mock_db):
        """User service instance with mocked database"""
        return UserService(mock_db)

    @pytest.fixture
    def sample_user(self):
        """Sample user for testing"""
        return User(
            id=1,
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )

    def test_get_user_by_email_success(self, user_service, mock_db, sample_user):
        """Test successful user retrieval by email"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user

        # Act
        result = user_service.get_user_by_email("test@example.com")

        # Assert
        assert result == sample_user
        mock_db.query.assert_called_once_with(User)
        mock_db.query.return_value.filter.assert_called_once()

    def test_get_user_by_email_not_found(self, user_service, mock_db):
        """Test user retrieval when user doesn't exist"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = user_service.get_user_by_email("nonexistent@example.com")

        # Assert
        assert result is None

    def test_create_user_success(self, user_service, mock_db):
        """Test successful user creation"""
        # Arrange
        user_data = UserCreate(
            email="new@example.com",
            password="password123"
        )

        created_user = User(
            id=2,
            email="new@example.com",
            hashed_password="hashed_password",
            is_active=True
        )

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        with patch('app.services.user_service.get_password_hash') as mock_hash:
            mock_hash.return_value = "hashed_password"

            # Act
            result = user_service.create_user(user_data)

            # Assert
            assert result.email == "new@example.com"
            assert result.hashed_password == "hashed_password"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_create_user_duplicate_email(self, user_service, mock_db, sample_user):
        """Test user creation with duplicate email"""
        # Arrange
        user_data = UserCreate(
            email="test@example.com",  # Existing email
            password="password123"
        )

        mock_db.query.return_value.filter.return_value.first.return_value = sample_user

        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            user_service.create_user(user_data)

    def test_authenticate_user_success(self, user_service, mock_db, sample_user):
        """Test successful user authentication"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user

        with patch('app.services.user_service.verify_password') as mock_verify:
            mock_verify.return_value = True

            # Act
            result = user_service.authenticate_user("test@example.com", "password123")

            # Assert
            assert result == sample_user

    def test_authenticate_user_wrong_password(self, user_service, mock_db, sample_user):
        """Test authentication with wrong password"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user

        with patch('app.services.user_service.verify_password') as mock_verify:
            mock_verify.return_value = False

            # Act
            result = user_service.authenticate_user("test@example.com", "wrongpassword")

            # Assert
            assert result is None

    def test_authenticate_user_not_found(self, user_service, mock_db):
        """Test authentication when user doesn't exist"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = user_service.authenticate_user("nonexistent@example.com", "password123")

        # Assert
        assert result is None
```

#### API Testing
```python
# backend/tests/test_auth_api.py
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import create_access_token

class TestAuthAPI:
    @pytest.fixture
    async def client(self, app):
        """Test client"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            yield client

    @pytest.fixture
    def test_user(self, db: Session):
        """Create test user"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    async def test_login_success(self, client, test_user):
        """Test successful login"""
        # Arrange
        login_data = {
            "username": "test@example.com",
            "password": "password123"
        }

        # Act
        response = await client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        # Arrange
        login_data = {
            "username": "test@example.com",
            "password": "wrongpassword"
        }

        # Act
        response = await client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        # Arrange
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }

        # Act
        response = await client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401

    async def test_register_success(self, client):
        """Test successful user registration"""
        # Arrange
        register_data = {
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User"
        }

        # Act
        response = await client.post("/api/v1/auth/register", json=register_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "created_at" in data

    async def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        # Arrange
        register_data = {
            "email": "test@example.com",  # Existing email
            "password": "password123",
            "full_name": "Test User"
        }

        # Act
        response = await client.post("/api/v1/auth/register", json=register_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    async def test_get_current_user(self, client, test_user):
        """Test getting current user with valid token"""
        # Arrange
        token = create_access_token({"sub": test_user.email})

        # Act
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

    async def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        # Act
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        # Assert
        assert response.status_code == 401

    async def test_get_current_user_no_token(self, client):
        """Test getting current user without token"""
        # Act
        response = await client.get("/api/v1/users/me")

        # Assert
        assert response.status_code == 401
```

### Frontend Testing Patterns

#### Component Testing
```typescript
// frontend/tests/components/DataTable.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DataTable } from '@/components/ui/DataTable';

interface TestData {
  id: number;
  name: string;
  email: string;
  status: string;
}

const mockData: TestData[] = [
  { id: 1, name: 'John Doe', email: 'john@example.com', status: 'active' },
  { id: 2, name: 'Jane Smith', email: 'jane@example.com', status: 'inactive' },
  { id: 3, name: 'Bob Johnson', email: 'bob@example.com', status: 'active' },
];

const columns = [
  { key: 'name' as keyof TestData, header: 'Name', sortable: true },
  { key: 'email' as keyof TestData, header: 'Email', sortable: true },
  { key: 'status' as keyof TestData, header: 'Status' },
];

describe('DataTable', () => {
  it('renders table with data', () => {
    render(<DataTable data={mockData} columns={columns} />);

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('jane@example.com')).toBeInTheDocument();
    expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    render(<DataTable data={[]} columns={columns} loading={true} />);

    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('filters data based on search term', async () => {
    render(<DataTable data={mockData} columns={columns} searchable={true} />);

    const searchInput = screen.getByPlaceholderText('Search...');
    fireEvent.change(searchInput, { target: { value: 'john' } });

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument();
    });
  });

  it('sorts data when column header is clicked', () => {
    render(<DataTable data={mockData} columns={columns} />);

    const nameHeader = screen.getByText('Name');
    fireEvent.click(nameHeader);

    // Check if data is sorted (this would depend on your sorting logic)
    const rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('Bob Johnson'); // Assuming ascending sort
  });

  it('calls onRowClick when row is clicked', () => {
    const mockOnRowClick = jest.fn();
    render(<DataTable data={mockData} columns={columns} onRowClick={mockOnRowClick} />);

    const firstRow = screen.getByText('John Doe').closest('tr');
    fireEvent.click(firstRow!);

    expect(mockOnRowClick).toHaveBeenCalledWith(mockData[0]);
  });

  it('paginates data correctly', () => {
    render(<DataTable data={mockData} columns={columns} pageSize={2} />);

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    expect(screen.queryByText('Bob Johnson')).not.toBeInTheDocument();

    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    expect(screen.queryByText('John Doe')).not.toBeInTheDocument();
    expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
  });

  it('shows pagination info correctly', () => {
    render(<DataTable data={mockData} columns={columns} pageSize={2} />);

    expect(screen.getByText('Showing 1 to 2 of 3 results')).toBeInTheDocument();
  });
});
```

#### Hook Testing
```typescript
// frontend/tests/hooks/useApi.test.ts
import { renderHook, act, waitFor } from '@testing-library/react';
import { useApi } from '@/hooks/useApi';

// Mock the API client
jest.mock('@/lib/api/client', () => ({
  fetchApi: jest.fn(),
}));

import { fetchApi } from '@/lib/api/client';

const mockFetchApi = fetchApi as jest.MockedFunction<typeof fetchApi>;

describe('useApi', () => {
  beforeEach(() => {
    mockFetchApi.mockClear();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useApi('/test-endpoint'));

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should execute API call and handle success', async () => {
    const mockData = { id: 1, name: 'Test' };
    mockFetchApi.mockResolvedValueOnce({ data: mockData, error: null });

    const { result } = renderHook(() => useApi('/test-endpoint'));

    act(() => {
      result.current.execute();
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toEqual(mockData);
      expect(result.current.error).toBeNull();
    });

    expect(mockFetchApi).toHaveBeenCalledWith('/test-endpoint', { params: undefined });
  });

  it('should handle API error', async () => {
    const errorMessage = 'API Error';
    mockFetchApi.mockResolvedValueOnce({ data: null, error: errorMessage });

    const { result } = renderHook(() => useApi('/test-endpoint'));

    act(() => {
      result.current.execute();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toBeNull();
      expect(result.current.error).toEqual(errorMessage);
    });
  });

  it('should execute immediately when immediate option is true', async () => {
    const mockData = { id: 1, name: 'Test' };
    mockFetchApi.mockResolvedValueOnce({ data: mockData, error: null });

    renderHook(() => useApi('/test-endpoint', { immediate: true }));

    await waitFor(() => {
      expect(mockFetchApi).toHaveBeenCalledWith('/test-endpoint', { params: undefined });
    });
  });

  it('should call onSuccess callback when provided', async () => {
    const mockData = { id: 1, name: 'Test' };
    const onSuccess = jest.fn();
    mockFetchApi.mockResolvedValueOnce({ data: mockData, error: null });

    const { result } = renderHook(() =>
      useApi('/test-endpoint', { onSuccess })
    );

    act(() => {
      result.current.execute();
    });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith(mockData);
    });
  });

  it('should call onError callback when provided', async () => {
    const errorMessage = 'API Error';
    const onError = jest.fn();
    mockFetchApi.mockResolvedValueOnce({ data: null, error: errorMessage });

    const { result } = renderHook(() =>
      useApi('/test-endpoint', { onError })
    );

    act(() => {
      result.current.execute();
    });

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(errorMessage);
    });
  });

  it('should pass params to API call', async () => {
    const mockData = { id: 1, name: 'Test' };
    const params = { page: 1, limit: 10 };
    mockFetchApi.mockResolvedValueOnce({ data: mockData, error: null });

    const { result } = renderHook(() => useApi('/test-endpoint'));

    act(() => {
      result.current.execute(params);
    });

    await waitFor(() => {
      expect(mockFetchApi).toHaveBeenCalledWith('/test-endpoint', { params });
    });
  });

  it('should handle network errors', async () => {
    const networkError = new Error('Network error');
    mockFetchApi.mockRejectedValueOnce(networkError);

    const { result } = renderHook(() => useApi('/test-endpoint'));

    act(() => {
      result.current.execute();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toBeNull();
      expect(result.current.error).toEqual('Network error');
    });
  });
});
```

## Configuration Patterns

### Environment Configuration
```python
# backend/app/core/config.py
from typing import List, Optional
from pydantic import BaseSettings, validator
import secrets

class Settings(BaseSettings):
    """Application settings with validation"""

    # Application
    app_name: str = "Career Copilot"
    version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_cache_ttl: int = 3600

    # Security
    secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:3000/auth/google/callback"

    # LLM Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    # Email
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: str = "noreply@careercopilot.com"

    # External APIs
    linkedin_api_key: Optional[str] = None
    indeed_api_key: Optional[str] = None

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://', 'sqlite:///')):
            raise ValueError('Database URL must be PostgreSQL or SQLite')
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings
```

### Feature Flags
```python
# backend/app/core/feature_flags.py
from typing import Dict, Any, Optional
import json
import os
from pathlib import Path

class FeatureFlags:
    """Feature flag management system"""

    def __init__(self, config_file: str = "config/feature_flags.json"):
        self.config_file = Path(config_file)
        self.flags: Dict[str, Any] = {}
        self.load_flags()

    def load_flags(self):
        """Load feature flags from configuration file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.flags = json.load(f)
        else:
            # Default flags
            self.flags = {
                "ai_matching": True,
                "advanced_analytics": False,
                "multi_tenant": False,
                "real_time_notifications": True,
                "job_scraping": True,
                "email_notifications": True,
                "push_notifications": False,
                "premium_features": False,
                "api_rate_limiting": True,
                "data_export": True,
                "bulk_operations": False,
                "webhook_support": False,
                "integration_apis": False,
                "advanced_reporting": False,
                "custom_workflows": False,
                "team_collaboration": False,
                "audit_logging": True,
                "gdpr_compliance": True,
                "data_retention": True,
                "backup_encryption": True
            }
            self.save_flags()

    def save_flags(self):
        """Save feature flags to configuration file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.flags, f, indent=2)

    def is_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.flags.get(feature, False)

    def enable(self, feature: str):
        """Enable a feature"""
        self.flags[feature] = True
        self.save_flags()

    def disable(self, feature: str):
        """Disable a feature"""
        self.flags[feature] = False
        self.save_flags()

    def set(self, feature: str, value: Any):
        """Set a feature flag value"""
        self.flags[feature] = value
        self.save_flags()

    def get(self, feature: str, default: Any = None) -> Any:
        """Get a feature flag value"""
        return self.flags.get(feature, default)

    def get_all_flags(self) -> Dict[str, Any]:
        """Get all feature flags"""
        return self.flags.copy()

    def reset_to_defaults(self):
        """Reset all flags to defaults"""
        if self.config_file.exists():
            os.remove(self.config_file)
        self.load_flags()

# Global feature flags instance
feature_flags = FeatureFlags()

def get_feature_flags() -> FeatureFlags:
    """Get feature flags instance"""
    return feature_flags

def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled (convenience function)"""
    return feature_flags.is_enabled(feature)
```

---

*See also: [[development-guide|Development Guide]], [[testing-strategies|Testing Strategies]], [[api-reference|API Reference]]*"