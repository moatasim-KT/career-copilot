# Job Scraping Configuration Update

**Date**: November 5, 2025  
**Status**: ✅ COMPLETED

## Summary

Updated the job scraping system with three major improvements:
1. **Remote jobs preference** - Users can now configure whether they want remote or in-person jobs (default: in-person)
2. **Increased scraping frequency** - Changed from every 6 hours to every 1 hour
3. **Manual scraping endpoint** - Frontend can now trigger job scraping via API button

---

## 1. Remote Jobs Configuration

### Database Changes
- **New Column**: `prefer_remote_jobs` (Boolean, default: `false`)
- **Migration**: `6b17ab364809_add_prefer_remote_jobs_to_user.py`
- **Applied**: ✅ Successfully migrated

### User Preference Behavior

| Setting | Behavior | Example Locations |
|---------|----------|-------------------|
| `prefer_remote_jobs = false` | Filters OUT remote locations | Berlin, Munich, Amsterdam |
| `prefer_remote_jobs = true` | INCLUDES remote locations | Berlin, Munich, Remote |

### Code Changes

**File**: `backend/app/models/user.py`
```python
# Added new field
prefer_remote_jobs = Column(Boolean, default=False, nullable=False)
```

**File**: `backend/app/services/job_scraping_service.py`
```python
def _extract_search_params(self, user: User) -> Dict[str, List[str]]:
    # ...existing code...
    
    # Respect user's remote preference (default is in-person jobs)
    prefer_remote = getattr(user, "prefer_remote_jobs", False)
    
    if prefer_remote:
        # User wants remote jobs - add "remote" if not already present
        if not any("remote" in loc.lower() for loc in locations):
            locations.append("remote")
    else:
        # User prefers in-person jobs - remove "remote" if present
        locations = [loc for loc in locations if "remote" not in loc.lower()]
```

### Testing
```bash
# Verified with test script
User: Moatasim
Prefer Remote Jobs: False
Preferred Locations: ['Berlin', 'Munich', 'Amsterdam', 'London', 'Paris', ...]
Search Locations Used: ['Berlin', 'Munich', 'Amsterdam']  # ✅ Remote filtered out
```

---

## 2. Scraping Frequency Update

### Schedule Change

| Before | After |
|--------|-------|
| Every 6 hours (0, 6, 12, 18) | Every 1 hour (hourly) |
| `CronTrigger(hour="*/6", minute=0)` | `CronTrigger(hour="*", minute=0)` |
| Cron: `0 */6 * * *` | Cron: `0 * * * *` |

### Code Changes

**File**: `backend/app/tasks/scheduled_tasks.py`
```python
# Register ingest_jobs task - runs every hour
scheduler.add_job(
    func=run_scrape_jobs,
    trigger=CronTrigger(hour="*", minute=0, timezone=utc),  # Changed from hour="*/6"
    id="ingest_jobs",
    name="Hourly Job Ingestion",  # Changed from "6-Hourly Job Ingestion"
    replace_existing=True,
)
logger.info("Registered task: ingest_jobs (cron: 0 * * * *)")
```

### Next Run Schedule
- Runs at: **:00** minutes of every hour (e.g., 2:00, 3:00, 4:00...)
- More frequent updates → fresher job listings
- Better for testing and development

---

## 3. Manual Scraping Endpoint

### API Endpoint

**Endpoint**: `POST /api/v1/jobs/scrape`

**Request Body**:
```json
{
  "skills": ["python", "data engineer"],     // Optional, defaults to user.skills
  "locations": ["Berlin", "Munich"],         // Optional, defaults to user.preferred_locations
  "remote": false,                           // Optional, defaults to user.prefer_remote_jobs
  "max_jobs": 100                           // Optional, defaults to 100
}
```

**Response**:
```json
{
  "message": "Successfully scraped 42 jobs",
  "jobs_found": 42,
  "keywords": ["python", "data engineer"],
  "locations": ["Berlin", "Munich"],
  "remote_included": false,
  "sources_used": ["ScraperManager", "Adzuna", "Arbeitnow", "The Muse", "RapidAPI", "RemoteOK"]
}
```

### Code Changes

**File**: `backend/app/api/v1/jobs.py`
```python
@router.post("/api/v1/jobs/scrape")
async def trigger_job_scraping(
    search_params: dict, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger job scraping from multiple sources."""
    
    # Build user preferences from search params and user settings
    user_preferences = {
        "skills": search_params.get("skills", current_user.skills or []),
        "locations": search_params.get("locations", current_user.preferred_locations or []),
        "remote": search_params.get("remote", getattr(current_user, "prefer_remote_jobs", False)),
        "max_jobs": search_params.get("max_jobs", 100)
    }

    # Use the manual scraping method (uses ScraperManager)
    jobs = await scraper.scrape_jobs(user_preferences)
    # ...
```

### Testing the Endpoint

```bash
# Example 1: Use defaults from user profile
curl -X POST http://localhost:8002/api/v1/jobs/scrape \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{}'

# Example 2: Custom search for in-person jobs in Berlin
curl -X POST http://localhost:8002/api/v1/jobs/scrape \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "skills": ["python", "fastapi"],
    "locations": ["Berlin", "Munich"],
    "remote": false,
    "max_jobs": 50
  }'

# Example 3: Search for remote jobs only
curl -X POST http://localhost:8002/api/v1/jobs/scrape \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "skills": ["react", "typescript"],
    "locations": ["Remote"],
    "remote": true,
    "max_jobs": 100
  }'
```

---

## Files Modified

1. **`backend/app/models/user.py`**
   - Added `prefer_remote_jobs` column

2. **`backend/app/tasks/scheduled_tasks.py`**
   - Changed scraping frequency from 6 hours to 1 hour

3. **`backend/app/services/job_scraping_service.py`**
   - Updated `_extract_search_params()` to respect `prefer_remote_jobs`
   - Filters locations based on remote preference

4. **`backend/app/api/v1/jobs.py`**
   - Updated `/api/v1/jobs/scrape` endpoint
   - Accepts full search parameters
   - Defaults to user preferences

5. **`backend/alembic/versions/6b17ab364809_add_prefer_remote_jobs_to_user.py`**
   - Database migration for new column

---

## How It Works Together

### Automatic Scraping (Every Hour)
```
1. APScheduler triggers at top of hour (e.g., 14:00)
2. Calls ingest_jobs_for_user(user.id)
3. Extracts user.prefer_remote_jobs → false
4. Generates search params WITHOUT remote locations
5. Calls ScraperManager → searches in-person jobs in Berlin, Munich, etc.
6. Saves jobs to database
```

### Manual Scraping (Frontend Button)
```
1. User clicks "Find Jobs" button
2. Frontend sends POST to /api/v1/jobs/scrape
3. Can override remote preference: {"remote": true}
4. Calls scrape_jobs(user_preferences)
5. Uses ScraperManager (same as automatic)
6. Returns jobs found to frontend
```

---

## Testing Checklist

- [x] Database migration applied successfully
- [x] `prefer_remote_jobs` column exists with default `false`
- [x] Search params filter out remote when `prefer_remote_jobs = false`
- [x] Search params include remote when `prefer_remote_jobs = true`
- [x] Scheduler configured for hourly runs (0 * * * *)
- [x] Manual endpoint accepts search parameters
- [x] Manual endpoint defaults to user preferences
- [ ] **TODO**: Restart backend to load new scheduler config
- [ ] **TODO**: Test frontend button integration
- [ ] **TODO**: Add user settings UI to toggle `prefer_remote_jobs`

---

## Next Steps

### Backend
1. **Restart the backend** to apply new scheduler configuration
   ```bash
   cd /Users/moatasimfarooque/Downloads/Data_Science/GITHUB/career-copilot
   ./start_backend.sh
   ```

2. **Verify scheduler is running hourly**
   ```bash
   tail -f logs/backend.log | grep "ingest_jobs"
   ```

### Frontend
1. **Add "Find Jobs" button** to trigger manual scraping
   ```typescript
   const handleFindJobs = async () => {
     const response = await fetch('/api/v1/jobs/scrape', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
         skills: userSkills,
         locations: userLocations,
         remote: includeRemote,
         max_jobs: 100
       })
     });
     const data = await response.json();
     alert(`Found ${data.jobs_found} new jobs!`);
   };
   ```

2. **Add Remote Toggle** in job search settings
   ```typescript
   <label>
     <input 
       type="checkbox" 
       checked={includeRemote}
       onChange={(e) => setIncludeRemote(e.target.checked)}
     />
     Include Remote Jobs
   </label>
   ```

3. **Add User Settings Page**
   - Toggle for `prefer_remote_jobs`
   - Update via PATCH /api/v1/users/me
   ```json
   { "prefer_remote_jobs": true }
   ```

### Database (Optional - Update Existing User)
```sql
-- Set your own preference
UPDATE users 
SET prefer_remote_jobs = false  -- or true for remote jobs
WHERE username = 'Moatasim';
```

---

## Summary

✅ **Remote Preference**: In-person jobs by default, configurable per user  
✅ **Hourly Scraping**: More frequent updates (every hour instead of every 6 hours)  
✅ **Manual Trigger**: Frontend can trigger scraping on demand  
✅ **Backward Compatible**: Existing users default to in-person jobs  
✅ **ScraperManager**: Both paths use the same working scrapers  

**Impact**: Better job discovery with user control over remote vs in-person preferences!
