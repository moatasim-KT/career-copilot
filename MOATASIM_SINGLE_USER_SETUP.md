# Career Copilot - Single User Setup for Moatasim

## Overview

The system has been configured for **single-user mode** with all authentication completely disabled. You are the only user, and the system automatically uses your account for all operations.

## Current Configuration

### User Account
- **Email**: moatasimfarooque@gmail.com
- **User ID**: 338
- **Skills**: Python, Machine Learning, Data Science, FastAPI, React, TypeScript, PostgreSQL, Docker, Kubernetes, AWS
- **Experience Level**: senior
- **Daily Application Goal**: 15

### Database Stats
- **Total Users**: 1 (Moatasim only)
- **Total Jobs**: 12
- **Total Applications**: 0

## 🚀 Quick Start: Upload Your Resume

### Option 1: Using the Upload Script (Recommended)

```bash
# Upload your resume to automatically extract skills
./scripts/upload_resume.sh /path/to/your/resume.pdf
```

This script will:
1. ✅ Upload your resume
2. ✅ Parse it to extract skills, experience, and contact info
3. ✅ Show you suggested profile updates
4. ✅ Automatically apply the updates to your profile
5. ✅ Display your updated profile

**Supported formats**: PDF, DOCX, DOC (max 10MB)

### Option 2: Manual Upload via API

```bash
# Step 1: Upload resume
curl -X POST http://localhost:8002/api/v1/resume/upload \
  -F "file=@/path/to/your/resume.pdf" \
  -H "accept: application/json"

# Response will include upload_id, for example: {"upload_id": 1, ...}

# Step 2: Check parsing status
curl http://localhost:8002/api/v1/resume/1/status | python -m json.tool

# Step 3: Get profile update suggestions
curl http://localhost:8002/api/v1/resume/1/suggestions | python -m json.tool

# Step 4: Apply suggestions to your profile
curl -X POST http://localhost:8002/api/v1/resume/1/apply-suggestions \
  -H "Content-Type: application/json" \
  -d '{"apply_suggestions": true}'
```

### Option 3: Using the Frontend

1. Open http://localhost:3000
2. Navigate to Profile/Resume section
3. Upload your resume via the UI
4. Review and apply suggested updates

## 📊 Verify Your Setup

### Test API Endpoints

All endpoints automatically use your account (no authentication needed):

```bash
# Get your profile
curl http://localhost:8002/api/v1/users/me | python -m json.tool

# Get jobs (should show 12 jobs)
curl http://localhost:8002/api/v1/jobs | python -m json.tool | head -40

# Get analytics summary
curl http://localhost:8002/api/v1/analytics/summary | python -m json.tool

# Get applications (should be empty)
curl http://localhost:8002/api/v1/applications | python -m json.tool
```

### Check Frontend

```bash
# Frontend should be running on port 3000
open http://localhost:3000
```

**What to expect**:
- ✅ No login page - direct access to dashboard
- ✅ All data shows your jobs, applications, and analytics
- ✅ Profile shows your skills and experience
- ✅ Job recommendations based on your profile

## 🔧 System Architecture

### Authentication Bypass

**File**: `backend/app/core/dependencies.py`

```python
async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    """Get the current user (always returns Moatasim)"""
    result = await db.execute(
        select(User).where(User.email == "moatasimfarooque@gmail.com")
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Run setup_moatasim_user.py to create account"
        )
    return user
```

**How it works**:
- Every API endpoint uses `Depends(get_current_user)`
- This dependency **always** returns your account
- No token validation, no password checks, no sessions
- Clean and simple single-user mode

### Database Schema

**Tables relevant to your profile**:
- `users` - Your account (ID: 338)
- `jobs` - Job postings (12 assigned to you)
- `applications` - Your job applications (currently 0)
- `resume_uploads` - Your uploaded resumes and parsed data

## 🛠️ Maintenance

### Reset Everything (if needed)

```bash
python scripts/setup_moatasim_user.py
```

**This script will**:
- ✅ Ensure your account exists (moatasimfarooque@gmail.com)
- ✅ Delete all other users if any were created
- ✅ Transfer all jobs to your account
- ✅ Clean up orphaned data

### Add New Skills Manually

```bash
# Update your skills via API
curl -X PATCH http://localhost:8002/api/v1/users/me \
  -H "Content-Type: application/json" \
  -d '{
    "skills": ["Python", "Machine Learning", "Data Science", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker", "Kubernetes", "AWS", "TensorFlow", "PyTorch"]
  }'
```

Or use the frontend profile editor.

### Check System Health

```bash
# Backend health
curl http://localhost:8002/health

# Database connection
curl http://localhost:8002/api/v1/analytics/summary

# Frontend access
curl -I http://localhost:3000
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `backend/app/core/dependencies.py` | Authentication bypass - always returns your account |
| `scripts/setup_moatasim_user.py` | Database cleanup script - keeps only your account |
| `scripts/upload_resume.sh` | Resume upload helper script |
| `backend/app/api/v1/resume.py` | Resume upload and parsing endpoints |
| `backend/app/models/user.py` | User model with skills, experience, etc. |

## ✅ System Status Checklist

- [x] Authentication completely disabled
- [x] Database cleaned to single user
- [x] Backend configured to always use moatasimfarooque@gmail.com
- [x] 12 jobs assigned to your account
- [x] Resume upload endpoints ready
- [ ] Resume uploaded and skills extracted ← **Next Step**
- [ ] Frontend tested and verified

## 🎯 Next Steps

1. **Upload your resume** using one of the methods above
2. **Verify your skills** were extracted correctly
3. **Test the frontend** at http://localhost:3000
4. **Start applying to jobs** - system will track applications for you

## 🆘 Troubleshooting

### Issue: "User not found" error

```bash
# Recreate your account
python scripts/setup_moatasim_user.py
```

### Issue: Backend not responding

```bash
# Check if backend is running
lsof -i:8002

# Restart backend
./start_backend.sh
```

### Issue: Resume parsing fails

**Check**:
- File size < 10MB
- File format is PDF, DOCX, or DOC
- Backend logs: `tail -f logs/backend/api.log`

### Issue: Skills not updating after resume upload

```bash
# Check parsing status
curl http://localhost:8002/api/v1/resume/1/status | python -m json.tool

# Manually apply suggestions
curl -X POST http://localhost:8002/api/v1/resume/1/apply-suggestions \
  -H "Content-Type: application/json" \
  -d '{"apply_suggestions": true}'
```

## 📞 Support Files

- **Authentication Documentation**: `AUTHENTICATION_REMOVED.md`
- **Database Schema**: Check `backend/app/models/` directory
- **API Documentation**: http://localhost:8002/docs (Swagger UI)

---

**Last Updated**: November 4, 2024  
**User**: Moatasim (moatasimfarooque@gmail.com)  
**System Mode**: Single User (No Authentication)
