## Remaining Tasks

### Category 1: Frontend Scalability & Responsiveness

#### Enhancement 1.2: Real-time Communication (WebSockets)

*   **Task 1.2.3: Implement WebSocket Endpoint for Notifications**
    *   Modify `send_evening_summary` in `backend/app/tasks/scheduled_tasks.py` to send WebSocket notifications upon successful email delivery or failure.

*   **Task 1.2.4: Integrate WebSocket Client in New Frontend**
    *   Implement a WebSocket client in the new frontend to connect to backend WebSocket endpoints and display real-time updates.

### Category 2: Deeper AI Integration

#### Enhancement 2.1: Advanced LLM Integration (Resume/JD Parsing & Content Generation)

*   **Task 2.1.1: Research and Select LLM Provider/Model**
    *   **Objective**: Choose a suitable LLM provider (GOW or nvidia) and specific model(s) for text processing tasks.
    *   **Inputs**: Project requirements (cost, performance, capabilities), available API keys.
    *   **Expected Output**: Documented decision on LLM provider/model.
    *   **Success Criteria**: LLM selected and API access confirmed.

*   **Task 2.1.2: Implement LLM Service for Skill Extraction from Job Descriptions**
    *   **Objective**: Create a backend service that uses the selected LLM to extract key skills and technologies from raw job description text.
    *   **Inputs**: Raw job description text, LLM API.
    *   **Expected Output**: A list of extracted skills (e.g., `["Python", "AWS", "Docker"]`).
    *   **Success Criteria**: Service accurately extracts skills from diverse job descriptions with >80% precision/recall.

*   **Task 2.1.3: Integrate LLM Skill Extraction into Job Ingestion**
    *   **Objective**: Modify the `JobScraperService` and `ingest_jobs` function to use the LLM service to automatically extract `tech_stack` and `responsibilities` from scraped job descriptions.
    *   **Inputs**: LLM skill extraction service, `JobScraperService`, `ingest_jobs`.
    *   **Expected Output**: Scraped jobs automatically populate `tech_stack` and `responsibilities` fields using LLM.
    *   **Success Criteria**: New jobs ingested via scraping have automatically extracted skills and responsibilities.

*   **Task 2.1.4: Implement LLM Service for Resume Skill Extraction**
    *   **Objective**: Create a backend service that uses the selected LLM to extract skills from an uploaded user resume (PDF/DOCX/TXT).
    *   **Inputs**: User resume file content, LLM API.
    *   **Expected Output**: A list of extracted skills from the resume.
    *   **Success Criteria**: Service accurately extracts skills from diverse resume formats with >75% precision/recall.

*   **Task 2.1.5: Integrate Resume Skill Extraction into User Profile**
    *   **Objective**: Add a UI component to the user profile page allowing users to upload their resume, and integrate with the backend LLM service to populate their `skills` field automatically.
    *   **Inputs**: LLM resume skill extraction service, user profile UI.
    *   **Expected Output**: User can upload resume, and their profile `skills` are updated automatically.
    *   **Success Criteria**: User's skills are updated in their profile after resume upload and processing.

*   **Task 2.1.6: Implement LLM Service for Cover Letter Generation**
    *   **Objective**: Create a backend service that uses the LLM to generate a personalized cover letter draft based on a user's profile, a specific job description, and the user's resume.
    *   **Inputs**: User profile data, job description, LLM API.
    *   **Expected Output**: A draft cover letter text.
    *   **Success Criteria**: Service generates coherent and personalized cover letters.

*   **Task 2.1.7: Add Cover Letter Generation UI to Job Details**
    *   **Objective**: Add a UI component to the job details page (or application page) allowing users to generate a cover letter draft for a specific job.
    *   **Inputs**: LLM cover letter generation service, job details UI.
    *   **Expected Output**: User can click a button and receive a cover letter draft.
    *   **Success Criteria**: Cover letter draft is displayed to the user.

### Category 3: Broader Job Source Coverage

#### Enhancement 3.1: Expand Job Board Integrations

*   **Task 3.1.1: Research and Select New Job Boards**
    *   **Objective**: Identify 2-3 additional job boards (e.g., Indeed, LinkedIn, specific niche boards) with available APIs or feasible scraping methods.
    *   **Inputs**: Popular job boards list, API availability, terms of service.
    *   **Expected Output**: A list of selected job boards for integration.
    *   **Success Criteria**: New job boards identified and documented.

*   **Task 3.1.2: Implement API Integration for New Job Board (e.g., Indeed)**
    *   **Objective**: Add a new method to `JobScraperService` to integrate with one of the selected new job boards' APIs.
    *   **Inputs**: New job board API documentation, `JobScraperService`.
    *   **Expected Output**: `JobScraperService` can successfully fetch jobs from the new API.
    *   **Success Criteria**: `JobScraperService` method returns valid `JobCreate` objects from the new API.

*   **Task 3.1.3: Integrate New Job Board into `search_all_apis`**
    *   **Objective**: Modify `JobScraperService.search_all_apis` to include calls to the newly implemented job board integration method.
    *   **Inputs**: New job board integration method.
    *   **Expected Output**: `search_all_apis` fetches jobs from the new source.
    *   **Success Criteria**: `search_all_apis` returns jobs from the new job board.

*   **Task 3.1.4: Repeat for Additional Job Boards**
    *   **Objective**: Implement API integrations for the remaining selected new job boards.
    *   **Inputs**: Selected job boards, `JobScraperService`.
    *   **Expected Output**: `JobScraperService` integrates with all selected new job boards.
    *   **Success Criteria**: All selected new job boards are integrated and contribute to the job feed.

### Category 4: User Engagement & Experience

#### Enhancement 4.1: Advanced Analytics and Reporting

*   **Task 4.1.1: Implement Application Success Rate Analysis**
    *   **Objective**: Add a method to `AnalyticsService` to calculate and return application success rates (e.g., applied-to-interview, interview-to-offer, offer-to-accepted).
    *   **Inputs**: Historical application data.
    *   **Expected Output**: Success rate metrics.
    *   **Success Criteria**: `AnalyticsService` method returns accurate success rates.

*   **Task 4.1.2: Implement Skill Demand Trend Analysis**
    *   **Objective**: Add a method to `AnalyticsService` to analyze trends in skill demand based on the `tech_stack` of jobs the user has tracked over time.
    *   **Inputs**: Historical job data.
    *   **Expected Output**: Top trending skills, declining skills.
    *   **Success Criteria**: `AnalyticsService` method returns relevant skill demand trends.

*   **Task 4.1.3: Expose New Analytics Metrics via API**
    *   **Objective**: Add new endpoints or extend existing ones in `backend/app/api/v1/analytics.py` to expose the new success rate and skill demand trend metrics.
    *   **Inputs**: New `AnalyticsService` methods.
    *   **Expected Output**: New API endpoints returning the calculated metrics.
    *   **Success Criteria**: API endpoints are accessible and return correct data.

*   **Task 4.1.4: Design and Implement Advanced Analytics UI**
    *   **Objective**: Create new sections or enhance the existing analytics dashboard in the frontend to visualize the new success rate and skill demand trend metrics.
    *   **Inputs**: New analytics API endpoints.
    *   **Expected Output**: Frontend displays advanced analytics with appropriate charts/graphs.
    *   **Success Criteria**: Users can view detailed success rates and skill trends in the UI.

#### Enhancement 4.2: User Onboarding and Gamification

*   **Task 4.2.1: Implement Guided Onboarding Flow**
    *   **Objective**: Create a multi-step onboarding flow for new users, guiding them through profile setup, adding first jobs, and understanding key features.
    *   **Inputs**: User registration flow, profile setup UI.
    *   **Expected Output**: New users are guided through initial setup.
    *   **Success Criteria**: New users complete onboarding steps and have a basic profile/jobs set up.

*   **Task 4.2.2: Implement Daily Application Streak Tracking**
    *   **Objective**: Add logic to track a user's daily application streak (consecutive days meeting their daily application goal).
    *   **Inputs**: `Application` data, `daily_application_goal`.
    *   **Expected Output**: Backend tracks and provides streak data.
    *   **Success Criteria**: Streak data is accurately calculated and stored.

*   **Task 4.2.3: Add Gamification Badges/Achievements**
    *   **Objective**: Define and implement a system for awarding virtual badges or achievements (e.g., "First Application," "7-Day Streak," "Skill Master").
    *   **Inputs**: User activity data, defined achievements.
    *   **Expected Output**: Backend awards and tracks achievements.
    *   **Success Criteria**: Achievements are awarded based on user actions.

*   **Task 4.2.4: Display Gamification Elements in UI**
    *   **Objective**: Create a UI section (e.g., on the dashboard or a dedicated "Achievements" page) to display the user's current streak and earned badges.
    *   **Inputs**: Streak and achievement data from backend.
    *   **Expected Output**: Frontend displays gamification elements.
    *   **Success Criteria**: Users can view their progress and achievements.

### Category 5: System Infrastructure & Security

#### Enhancement 5.1: Authentication with OAuth/SSO

*   **Task 5.1.1: Research and Select OAuth Providers**
    *   **Objective**: Choose 1-2 primary OAuth providers to integrate based on user base and ease of integration.
    *   **Inputs**: User demographics, provider documentation.
    *   **Expected Output**: Documented decision on OAuth providers.
    *   **Success Criteria**: OAuth providers selected.

*   **Task 5.1.2: Implement Backend OAuth Integration (e.g., Google)**
    *   **Objective**: Add backend routes and logic to handle OAuth callbacks, token exchange, and user creation/linking for a chosen provider.
    *   **Inputs**: OAuth provider API documentation, existing authentication system.
    *   **Expected Output**: Backend successfully authenticates users via OAuth.
    *   **Success Criteria**: Users can log in/register via OAuth provider.

*   **Task 5.1.3: Implement Frontend OAuth UI**
    *   **Objective**: Add UI buttons and logic to the login/registration page in the frontend to initiate OAuth flows.
    *   **Inputs**: Backend OAuth endpoints.
    *   **Expected Output**: Frontend displays OAuth login/register options.
    *   **Success Criteria**: Users can initiate OAuth login/registration from the frontend.

## Phase 3: Frontend Enhancements

### 29. Enhance frontend with advanced features

*   **29.1 Implement real-time UI updates**
    *   [backend] [websocket] Choose a WebSocket library for the Python backend (e.g., `FastAPI-WebSocket`, `websockets`).
    *   [backend] [websocket] Define WebSocket endpoints in the FastAPI application to handle real-time communication.
    *   [backend] [websocket] Integrate the WebSocket endpoints with the existing job matching and application status logic.
    *   [frontend] [websocket] Implement a WebSocket client in the Streamlit frontend to connect to the backend.
    *   [frontend] [ui] Create UI components to display real-time notifications for job matches and application status updates.
    *   [frontend] [ui] Develop a real-time analytics dashboard that updates with live data from the WebSocket.
    *   [test] [websocket] Write tests for the WebSocket endpoints.
    *   [test] [ui] Write tests for the real-time UI components.

*   **29.2 Add file upload and content generation UI**
    *   [frontend] [ui] Use Streamlit's `st.file_uploader` to create a resume upload interface.
    *   [frontend] [ui] Add drag-and-drop functionality using a Streamlit component or custom HTML/JavaScript.
    *   [frontend] [ui] Implement UI to show parsing status and progress.
    *   [frontend] [ui] Create Streamlit forms (`st.form`) for generating cover letters and tailored resumes.
    *   [frontend] [ui] Add input fields for job descriptions, user skills, and other relevant information.
    *   [frontend] [ui] Implement a preview and editing interface for the generated content.
    *   [test] [ui] Write tests for the file upload and content generation UI.

*   **29.3 Implement interview practice UI**
    *   [frontend] [ui] Design a Streamlit interface for the interview practice sessions.
    *   [frontend] [websocket] Implement a real-time Q&A flow using WebSockets or by triggering backend API calls.
    *   [frontend] [ui] Implement UI elements to display real-time feedback on user answers.
    *   [frontend] [ui] Create views to show interview history and performance analytics.
    *   [test] [ui] Write tests for the interview practice UI.

*   **29.4 Add OAuth login integration to frontend**
    *   [backend] [auth] Integrate an OAuth library (e.g., `Authlib`, `FastAPI-Users`) with the FastAPI backend.
    *   [backend] [auth] Configure OAuth providers (e.g., Google, LinkedIn).
    *   [backend] [auth] Implement callback endpoints to handle the OAuth flow.
    *   [frontend] [auth] Add social login buttons to the Streamlit frontend.
    *   [frontend] [auth] Implement the client-side logic to initiate the OAuth flow.
    *   [frontend] [auth] Handle the callback from the backend to complete the authentication process.
    *   [frontend] [auth] Create UI for account linking and profile setup after the first login.

## 31. Implement performance optimizations

*   **31.1 Add Redis caching for enhanced features**
    *   [backend] [caching] Cache LLM responses for content generation.
    *   [backend] [caching] Cache parsed resume data and job descriptions.
    *   [backend] [caching] Cache interview questions and feedback.
    *   [backend] [caching] Implement cache invalidation strategies.

*   **31.2 Implement background job processing**
    *   [backend] [celery] Add Celery for asynchronous task processing.
    *   [backend] [celery] Move resume parsing to background jobs.
    *   [backend] [celery] Implement async content generation.
    *   [backend] [celery] Add job queue monitoring and management.

*   **31.3 Add database optimizations for new features**
    *   [database] [optimization] Create indexes for new tables and queries.
    *   [database] [optimization] Implement database connection pooling.
    *   [database] [optimization] Add query optimization for complex analytics.
    *   [database] [optimization] Implement database partitioning for large datasets.