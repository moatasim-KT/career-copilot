# Single-User System Migration Guide

This document outlines the changes made to convert Career Copilot to a single-user system for Moatasim.

## Core Changes

### 1. Created Single User Module
**File**: `backend/app/core/single_user.py`

- Defines constants: `MOATASIM_USER_ID = 1`
- User attributes: skills, experience_level, career_goals
- `SingleUser` class for compatibility
- `get_single_user()` function

### 2. Updated Files

#### Completed ✅
1. **backend/app/api/v1/social.py**
   - Removed all `User = Depends(get_current_user)`
   - Uses `MOATASIM_USER_ID` constant
   - All endpoints work without authentication

2. **backend/app/services/career_resources_service.py**
   - Updated to accept `user_id`, `user_skills`, `experience_level` as parameters
   - No dependency on User model
   - Works with simple data types

3. **backend/app/api/v1/saved_searches.py**
   - All endpoints use `MOATASIM_USER_ID`
   - Removed `current_user` dependencies
   - No authentication required

#### Need Updates ⚠️

Files that still reference authentication:

1. **backend/app/api/v1/tasks.py**
   - Lines 57, 79, 101, 107, 172, 198, 210
   - Replace `current_user: User = Depends(get_current_user)` with no dependency
   - Replace `current_user.id` with `MOATASIM_USER_ID`

2. **backend/app/api/v1/websocket.py**
   - Lines 55, 71, 96, 124, 148
   - Remove authentication dependencies
   - Use `get_single_user()` where user object is needed

3. **backend/app/api/v1/migration_strategy.py**
   - Multiple endpoints with `current_user` dependency
   - Can be simplified to work without auth

4. **backend/app/api/v1/scheduled_reports.py**
   - Line 22: Remove `current_user` dependency
   - Use `MOATASIM_USER_ID`

5. **backend/app/api/workflow_progress.py**
   - Lines 63, 97, 138, 193, 245, 289
   - Remove all `current_user` dependencies
   - Use `get_single_user()` for username references

## Migration Pattern

### Before (Multi-user with Auth):
```python
from app.core.dependencies import get_current_user
from app.models.user import User

@router.get("/endpoint")
async def my_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.id
    user_skills = current_user.skills
    # ...
```

### After (Single-user without Auth):
```python
from app.core.single_user import MOATASIM_USER_ID, MOATASIM_SKILLS, get_single_user

@router.get("/endpoint")
async def my_endpoint(
    db: AsyncSession = Depends(get_db)
):
    user_id = MOATASIM_USER_ID
    user_skills = MOATASIM_SKILLS
    # Or if you need a user object:
    # user = get_single_user()
    # user_id = user.id
    # ...
```

## Frontend Changes Needed

All frontend code that sends authentication headers or user_id in URLs needs updating:

### API Calls to Update:
1. Change from `/api/v1/users/{user_id}/resources` to `/api/v1/me/resources`
2. Remove Authorization headers
3. Remove user_id from request bodies where it was required

### Example Frontend Change:
```typescript
// Before
const response = await fetch(`/api/v1/users/${userId}/resources`, {
    headers: { 'Authorization': `Bearer ${token}` }
});

// After
const response = await fetch('/api/v1/me/resources');
```

## Testing

After migration, test these endpoints:
- `GET /api/v1/me/resources`
- `POST /api/v1/me/bookmarks`
- `GET /api/v1/me/bookmarks`
- `POST /api/v1/resources/{id}/feedback`
- `PATCH /api/v1/me/bookmarks/{id}`
- `GET /api/v1/me/stats`

## Rollback Plan

If needed to revert:
1. Restore User model imports
2. Restore `get_current_user` dependency
3. Change endpoints back to `/users/{user_id}/...`
4. Re-add authentication middleware

## Benefits

1. **Simpler Architecture**: No auth complexity
2. **Faster Development**: No token management
3. **Better Performance**: No auth checks on every request
4. **Cleaner Code**: Less boilerplate

## Notes

- Database schema unchanged (still has `user_id` columns)
- Easy to scale back to multi-user if needed
- All data automatically associated with user_id = 1
