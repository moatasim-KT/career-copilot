

## Features

- **Dashboard:** Get a quick overview of your job search progress.
- **Jobs:** Track all your job applications in one place.
- **Recommendations:** Get personalized job recommendations based on your profile.
- **Analytics:** Analyze your job search performance with detailed analytics.
- **Skill Gap:** Identify your skill gaps and get learning recommendations.
- **Content Generation:** Generate cover letters and resume summaries with AI.
- **Interview Practice:** Practice your interview skills with an AI-powered interviewer.


### Prerequisites

- Python 3.9+
- Node.js 16+
- Docker (optional)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/career-copilot.git
   cd career-copilot
   ```

2. **Backend Setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Fill in the .env file with your credentials
   ```

3. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. **Start the backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

The application will be available at `http://localhost:3000`.


### Profile

- **GET /api/v1/profile**
  - **Description:** Retrieve the current user's profile.
  - **Response:**
    ```json
    {
      "id": 1,
      "username": "testuser",
      "email": "test@example.com",
      "skills": ["Python", "FastAPI"],
      "experience_level": "Mid",
      "preferred_locations": ["New York", "Remote"],
      "daily_application_goal": 5
    }
    ```

- **PUT /api/v1/profile**
  - **Description:** Update the current user's profile.
  - **Request Body:**
    ```json
    {
      "skills": ["Python", "FastAPI", "SQL"],
      "experience_level": "Senior"
    }
    ```
  - **Response:** The updated user profile.

### Jobs

- **GET /api/v1/jobs**
  - **Description:** List all jobs for the current user.
  - **Query Parameters:**
    - `skip` (int, optional): Number of records to skip.
    - `limit` (int, optional): Maximum number of records to return.
  - **Response:** A list of job objects.

- **POST /api/v1/jobs**
  - **Description:** Create a new job.
  - **Request Body:**
    ```json
    {
      "company": "Tech Corp",
      "title": "Software Engineer",
      "tech_stack": ["Python", "FastAPI"]
    }
    ```
  - **Response:** The created job object.

- **GET /api/v1/jobs/{job_id}**
  - **Description:** Get a specific job by ID.
  - **Response:** The job object.

- **PUT /api/v1/jobs/{job_id}**
  - **Description:** Update a job.
  - **Request Body:**
    ```json
    {
      "status": "applied"
    }
    ```
  - **Response:** The updated job object.

- **DELETE /api/v1/jobs/{job_id}**
  - **Description:** Delete a job.
  - **Response:** `204 No Content`

### Job Sources

- **GET /api/v1/job-sources**
  - **Description:** Get all available job sources.
  - **Response:** A list of job source objects.

- **POST /api/v1/job-sources/preferences**
  - **Description:** Create job source preferences for the current user.
  - **Request Body:**
    ```json
    {
      "preferred_sources": ["linkedin", "indeed"],
      "disabled_sources": ["glassdoor"]
    }
    ```
  - **Response:** The created job source preferences object.

- **PUT /api/v1/job-sources/preferences**
  - **Description:** Update job source preferences for the current user.
  - **Request Body:**
    ```json
    {
      "auto_scraping_enabled": true
    }
    ```
  - **Response:** The updated job source preferences object.

- **GET /api/v1/job-sources/preferences**
  - **Description:** Get current user's job source preferences.
  - **Response:** The job source preferences object.

### Analytics

- **GET /api/v1/analytics/summary**
  - **Description:** Get a summary of job application analytics for the current user.
  - **Response:** An analytics summary object.

- **GET /api/v1/analytics/interview-trends**
  - **Description:** Get analysis of interview trends for the current user.
  - **Response:** An interview trends analysis object.

### Recommendations

- **GET /api/v1/recommendations**
  - **Description:** Get personalized job recommendations.
  - **Query Parameters:**
    - `limit` (int, optional): Number of recommendations to return.
  - **Response:** A list of recommended job objects.

### Skill Gap

- **GET /api/v1/skill-gap**
  - **Description:** Analyze user's skill gaps based on job market.
  - **Response:** A skill gap analysis object.

### Applications

- **GET /api/v1/applications**
  - **Description:** List all applications for the current user.
  - **Query Parameters:**
    - `skip` (int, optional): Number of records to skip.
    - `limit` (int, optional): Maximum number of records to return.
    - `status` (str, optional): Filter by application status.
  - **Response:** A list of application objects.

- **POST /api/v1/applications**
  - **Description:** Create a new application for a job.
  - **Request Body:**
    ```json
    {
      "job_id": 1,
      "status": "applied"
    }
    ```
  - **Response:** The created application object.

- **GET /api/v1/applications/{app_id}**
  - **Description:** Get a specific application by ID.
  - **Response:** The application object.

- **PUT /api/v1/applications/{app_id}**
  - **Description:** Update an application's status and other fields.
  - **Request Body:**
    ```json
    {
      "status": "interview"
    }
    ```
  - **Response:** The updated application object.

- **DELETE /api/v1/applications/{app_id}**
  - **Description:** Delete an application by ID.
  - **Response:** `204 No Content`

### Job Recommendation Feedback

- **POST /api/v1/job-recommendation-feedback**
  - **Description:** Create new job recommendation feedback.
  - **Request Body:**
    ```json
    {
      "job_id": 1,
      "is_helpful": true
    }
    ```
  - **Response:** The created feedback object.

- **GET /api/v1/job-recommendation-feedback**
  - **Description:** Get user's job recommendation feedback.
  - **Response:** A list of feedback objects.

### Feedback Analysis

- **GET /api/v1/feedback-analysis**
  - **Description:** Get comprehensive feedback analysis for pattern recognition.
  - **Response:** A feedback analysis object.

### Market Analysis

- **GET /api/v1/market-analysis/salary-trends**
  - **Description:** Get comprehensive salary trend analysis for the user's job market.
  - **Response:** A salary trends analysis object.

- **GET /api/v1/market-analysis/job-patterns**
  - **Description:** Get comprehensive job market pattern analysis.
  - **Response:** A job market patterns analysis object.

### Advanced User Analytics

- **GET /api/v1/analytics/success-rates**
  - **Description:** Get detailed application success rate analysis.
  - **Response:** A success rates analysis object.

- **GET /api/v1/analytics/conversion-funnel**
  - **Description:** Get detailed conversion funnel analysis.
  - **Response:** A conversion funnel analysis object.

### Scheduled Reports

- **GET /api/v1/reports/weekly**
  - **Description:** Generate a comprehensive weekly analytics report.
  - **Response:** A weekly report object.

- **GET /api/v1/reports/monthly**
  - **Description:** Generate a comprehensive monthly analytics report.
  - **Response:** A monthly report object.
