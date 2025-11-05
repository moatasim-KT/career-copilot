# Frontend Testing Guide

## ✅ System Status

- **Backend**: Running on `http://localhost:8002`
- **Frontend**: Running on `http://localhost:3000`
- **Database**: PostgreSQL populated with demo data
- **Redis**: Connected and operational

## 🔐 Demo User Credentials

```
Email: demo@careercopilot.com
Password: demo123
```

## 📊 Demo Data Created

The database now contains:
- **1 Demo User** with skills: Python, FastAPI, React, TypeScript, PostgreSQL, Docker
- **5 Sample Jobs**:
  1. TechCorp Inc - Senior Backend Engineer (Remote)
  2. StartupXYZ - Full Stack Developer (San Francisco, CA)
  3. Enterprise Solutions Ltd - Tech Lead - Platform Engineering (New York, NY)
  4. DataDriven AI - Machine Learning Engineer (Remote)
  5. Cloud Innovations - DevOps Engineer (Austin, TX)
- **3 Sample Applications** (applied, interview, applied status)

## 🧪 Testing Steps

### 1. Login to Frontend

1. Open `http://localhost:3000` in your browser
2. Navigate to the login page
3. Enter credentials:
   - Email: `demo@careercopilot.com`
   - Password: `demo123`
4. Click "Login"

### 2. Verify Jobs Display

1. Navigate to Jobs page (`/jobs`)
2. You should see 5 jobs listed
3. Verify job details are visible:
   - Company name
   - Job title
   - Location
   - Tech stack
   - Salary range

### 3. Test Job Status Updates

1. Click on a job card
2. Try changing the status (e.g., from "not_applied" to "applied")
3. Verify the status updates successfully

### 4. Test Skill Extraction

1. Navigate to Profile page
2. Verify your skills are displayed: Python, FastAPI, React, TypeScript, PostgreSQL, Docker
3. Navigate to Skill Gap Analysis
4. Click "Analyze Skills"
5. Verify skill recommendations appear

### 5. Test Applications Tracking

1. Navigate to Applications page (`/applications`)
2. You should see 3 applications:
   - TechCorp Inc - Applied
   - StartupXYZ - Interview
   - Enterprise Solutions Ltd - Applied
3. Verify application details and notes are visible

### 6. Test Resume Upload

1. Navigate to Profile/Resume page
2. Upload a PDF resume
3. Verify skill extraction works
4. Check if suggestions appear

## 🔧 Troubleshooting

### No Jobs Showing

If jobs don't appear:

```bash
# Check backend is running
curl http://localhost:8002/health

# Verify database has data (requires auth token)
# First login to get token, then:
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8002/api/v1/jobs
```

### Login Fails

If login doesn't work:

1. Check browser console for errors (F12)
2. Verify backend API is accessible:
   ```bash
   curl -X POST http://localhost:8002/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=demo@careercopilot.com&password=demo123"
   ```
3. Should return a JSON with `access_token`

### Frontend Not Connecting to Backend

1. Check CORS settings in backend (`app/main.py`)
2. Verify frontend API base URL is set to `http://localhost:8002`
3. Check browser console for CORS errors

## 📝 API Endpoints to Test

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register new user
- `GET /api/v1/auth/me` - Get current user

### Jobs
- `GET /api/v1/jobs` - List all jobs
- `GET /api/v1/jobs/{id}` - Get specific job
- `POST /api/v1/jobs` - Create new job
- `PATCH /api/v1/jobs/{id}` - Update job
- `DELETE /api/v1/jobs/{id}` - Delete job

### Applications
- `GET /api/v1/applications` - List all applications
- `GET /api/v1/applications/{id}` - Get specific application  
- `POST /api/v1/applications` - Create application
- `PATCH /api/v1/applications/{id}` - Update application

### Skill Analysis
- `GET /api/v1/skill-gap-analysis` - Analyze skill gaps
- `GET /api/v1/skill-gap-analysis/recommendations` - Get skill recommendations

### Resume
- `POST /api/v1/resume/upload` - Upload resume
- `GET /api/v1/resume/parse` - Parse uploaded resume

## 🎯 Expected Behavior

### Jobs Page
- Should display 5 jobs in a grid/list
- Each job card should show: company, title, location, salary, tech stack
- Status badges should be visible
- Filtering and sorting should work

### Dashboard
- Should show stats: Total Jobs (5), Applications (3), Interviews (1)
- Should display recent activity
- Should show skill coverage percentage

### Skill Gap Analysis
- Should compare your skills (6 skills) against job requirements
- Should show missing skills
- Should provide learning recommendations
- Should calculate skill coverage percentage

## 🚨 Known Issues

1. **Empty Data**: If database is empty, run:
   ```bash
   python scripts/initialize_demo_data.py
   ```

2. **Authentication**: Frontend may need to store auth token in localStorage
3. **CORS**: Frontend must send requests with proper headers

## 🔄 Resetting Demo Data

To reset and recreate demo data:

```bash
# Stop backend
# Drop and recreate database (or just delete data)
psql -d career_copilot -c "TRUNCATE users, jobs, applications CASCADE;"

# Run demo data script again
python scripts/initialize_demo_data.py

# Restart backend
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## ✨ Success Criteria

Frontend is working correctly if:
- ✅ Login works with demo credentials
- ✅ Jobs page displays 5 jobs
- ✅ Applications page shows 3 applications
- ✅ Skill gap analysis shows recommendations
- ✅ Job status can be changed
- ✅ Profile shows user skills
- ✅ Dashboard shows correct stats
- ✅ All buttons are functional

---

**Last Updated**: 2025-11-04
**Demo User ID**: 345
