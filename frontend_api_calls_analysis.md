## Frontend API Client Call Analysis

This report details the API client calls identified within the frontend codebase, including their endpoints, HTTP methods, parameters, and the frontend components/files where they are made.

**Note on API Client Implementations:**
The frontend utilizes two primary API client implementations:
1.  **Class-based `APIClient` (from `frontend/src/lib/api/api.ts`):** This client is the default export of `@/lib/api` and provides specific methods for each API operation (e.g., `apiClient.getJobs()`).
2.  **Object-based `apiClient` (from `frontend/src/lib/api/client.ts`):** This client exposes nested service objects (e.g., `apiClient.jobs.list()`) and individual services (e.g., `JobsService`).

Some generic calls like `apiClient.post('/path')` were found, which are not explicitly defined in either client. These are treated as direct API calls with inferred methods.

---

### API Calls by Component/File

**1. `frontend/src/app/applications/page.tsx` (Component: `ApplicationsPage`)**
*   **Call:** `ApplicationsService.getApplicationsApiV1ApplicationsGet()`
    *   **Endpoint:** `/api/v1/applications`
    *   **Method:** `GET`
    *   **Parameters:** None

**2. `frontend/src/components/ui/FileUpload.tsx` (Component: `FileUpload`)**
*   **Call:** `apiClient.uploadResume(file)`
    *   **Endpoint:** `/api/v1/resume/upload`
    *   **Method:** `POST`
    *   **Parameters:** `file` (FormData)

**3. `frontend/src/components/features/InterviewPractice.tsx` (Component: `InterviewPractice`)**
*   **Call:** `apiClient.post('/api/v1/interview/start', sessionData)`
    *   **Endpoint:** `/api/v1/interview/start`
    *   **Method:** `POST`
    *   **Parameters:** `sessionData` (body)
*   **Call:** `apiClient.post(`/api/v1/interview/${currentSession.id}/answer`, answer)`
    *   **Endpoint:** `/api/v1/interview/{sessionId}/answer`
    *   **Method:** `POST`
    *   **Parameters:** `sessionId` (path), `answer` (body)

**4. `frontend/src/components/features/ResumeUpload.tsx` (Component: `ResumeUpload`)**
*   **Call:** `apiClient.uploadResume(file)`
    *   **Endpoint:** `/api/v1/resume/upload`
    *   **Method:** `POST`
    *   **Parameters:** `file` (FormData)

**5. `frontend/src/components/features/ContentGeneration.tsx` (Component: `ContentGeneration`)**
*   **Call:** `apiClient.generateContent(contentType, requestData)`
    *   **Endpoint:** `/api/v1/content/generate`
    *   **Method:** `POST`
    *   **Parameters:** `contentType`, `requestData` (body)

**6. `frontend/src/components/charts/ApplicationStatusChart.tsx` (Component: `ApplicationStatusChart`)**
*   **Call:** `apiClient.getAnalyticsSummary()`
    *   **Endpoint:** `/api/v1/analytics/summary`
    *   **Method:** `GET`
    *   **Parameters:** None

**7. `frontend/src/components/recommendations/SmartRecommendations.tsx` (Component: `SmartRecommendations`)**
*   **Call:** `apiClient.submitFeedback({ ... })`
    *   **Endpoint:** `/api/v1/feedback`
    *   **Method:** `POST`
    *   **Parameters:** `feedback_type`, `target_id`, `rating`, `comments` (body)

**8. `frontend/src/components/pages/AnalyticsPage.tsx` (Component: `AnalyticsPage`)**
*   **Call:** `apiClient.getAnalyticsSummary()`
    *   **Endpoint:** `/api/v1/analytics/summary`
    *   **Method:** `GET`
    *   **Parameters:** None
*   **Call:** `apiClient.getComprehensiveAnalytics(timeframe)`
    *   **Endpoint:** `/api/v1/analytics/comprehensive-dashboard?days={timeframe}`
    *   **Method:** `GET`
    *   **Parameters:** `days` (query)

**9. `frontend/src/components/pages/JobsPage.tsx` (Component: `JobsPage`)**
*   **Call:** `JobsService.update(jobId as number, prevJob)`
    *   **Endpoint:** `/api/v1/jobs/{jobId}`
    *   **Method:** `PUT`
    *   **Parameters:** `jobId` (path), `prevJob` (body)
*   **Call:** `JobsService.list()`
    *   **Endpoint:** `/api/v1/jobs`
    *   **Method:** `GET`
    *   **Parameters:** None
*   **Call:** `JobsService.scrape()`
    *   **Endpoint:** `/api/v1/jobs/scrape`
    *   **Method:** `POST`
    *   **Parameters:** None
*   **Call:** `JobsService.update(editingJob.id, formData)`
    *   **Endpoint:** `/api/v1/jobs/{jobId}`
    *   **Method:** `PUT`
    *   **Parameters:** `jobId` (path), `formData` (body)
*   **Call:** `JobsService.create(formData)`
    *   **Endpoint:** `/api/v1/jobs`
    *   **Method:** `POST`
    *   **Parameters:** `formData` (body)
*   **Call:** `JobsService.delete(jobId)`
    *   **Endpoint:** `/api/v1/jobs/{jobId}`
    *   **Method:** `DELETE`
    *   **Parameters:** `jobId` (path)
*   **Call:** `ApplicationsService.create({ ... })`
    *   **Endpoint:** `/api/v1/applications`
    *   **Method:** `POST`
    *   **Parameters:** `job_id`, `status`, `notes` (body)
*   **Call:** `JobsService.create({ ... })`
    *   **Endpoint:** `/api/v1/jobs`
    *   **Method:** `POST`
    *   **Parameters:** `jobData` (body)

**10. `frontend/src/components/pages/Dashboard.tsx` (Component: `Dashboard`)**
*   **Call:** `apiClient.getAnalyticsSummary()`
    *   **Endpoint:** `/api/v1/analytics/summary`
    *   **Method:** `GET`
    *   **Parameters:** None
*   **Call:** `apiClient.getApplications(0, 5)`
    *   **Endpoint:** `/api/v1/applications?skip=0&limit=5`
    *   **Method:** `GET`
    *   **Parameters:** `skip=0`, `limit=5` (query)

**11. `frontend/src/components/pages/RecommendationsPage.tsx` (Component: `RecommendationsPage`)**
*   **Call:** `apiClient.getRecommendations(0, 10)`
    *   **Endpoint:** `/api/v1/recommendations?skip=0&limit=10`
    *   **Method:** `GET`
    *   **Parameters:** `skip=0`, `limit=10` (query)
*   **Call:** `apiClient.getSkillGapAnalysis()`
    *   **Endpoint:** `/api/v1/skill-gap`
    *   **Method:** `GET`
    *   **Parameters:** None

**12. `frontend/src/components/pages/EnhancedDashboard.tsx` (Component: `EnhancedDashboard`)**
*   **Call:** `apiClient.getAnalyticsSummary()`
    *   **Endpoint:** `/api/v1/analytics/summary`
    *   **Method:** `GET`
    *   **Parameters:** None

**13. `frontend/src/components/onboarding/steps/ResumeStep.tsx` (Component: `ResumeStep`)**
*   **Call:** `apiClient.post('/resume/parse', formData)` (commented out, inferred)
    *   **Endpoint:** `/resume/parse`
    *   **Method:** `POST`
    *   **Parameters:** `formData` (body)

**14. `frontend/src/components/analytics/AnalyticsDashboard.tsx` (Component: `AnalyticsDashboard`)**
*   **Call:** `apiClient.get('/api/v1/analytics/summary')`
    *   **Endpoint:** `/api/v1/analytics/summary`
    *   **Method:** `GET`
    *   **Parameters:** None

**15. `frontend/src/hooks/useNotificationsQuery.ts` (Component: `useNotificationsQuery`, `useNotificationPreferences`, `useMarkNotificationAsRead`, `useMarkAllNotificationsAsRead`, `useDeleteNotification`, `useUpdateNotificationPreferences`)**
*   **Call:** `apiClient.getNotifications(skip, limit)`
    *   **Endpoint:** `/api/v1/notifications?skip={skip}&limit={limit}`
    *   **Method:** `GET`
    *   **Parameters:** `skip`, `limit` (query)
*   **Call:** `apiClient.getNotificationPreferences()`
    *   **Endpoint:** `/api/v1/notifications/preferences`
    *   **Method:** `GET`
    *   **Parameters:** None
*   **Call:** `apiClient.markNotificationAsRead(notificationId)`
    *   **Endpoint:** `/api/v1/notifications/{notificationId}/read`
    *   **Method:** `PUT`
    *   **Parameters:** `notificationId` (path)
*   **Call:** `apiClient.markAllNotificationsAsRead()`
    *   **Endpoint:** `/api/v1/notifications/read-all`
    *   **Method:** `PUT`
    *   **Parameters:** None
*   **Call:** `apiClient.deleteNotification(notificationId)`
    *   **Endpoint:** `/api/v1/notifications/{notificationId}`
    *   **Method:** `DELETE`
    *   **Parameters:** `notificationId` (path)
*   **Call:** `apiClient.updateNotificationPreferences(preferences)`
    *   **Endpoint:** `/api/v1/notifications/preferences`
    *   **Method:** `PUT`
    *   **Parameters:** `preferences` (body)

**16. `frontend/src/hooks/useUserProfile.ts` (Component: `useUserProfile`)**
*   **Call:** `apiClient.getUserProfile()`
    *   **Endpoint:** `/api/v1/profile`
    *   **Method:** `GET`
    *   **Parameters:** None

**17. `frontend/src/hooks/useAnalytics.ts` (Component: `useAnalyticsSummary`, `useComprehensiveAnalytics`)**
*   **Call:** `apiClient.getAnalyticsSummary()`
    *   **Endpoint:** `/api/v1/analytics/summary`
    *   **Method:** `GET`
    *   **Parameters:** None
*   **Call:** `apiClient.getComprehensiveAnalytics(days)`
    *   **Endpoint:** `/api/v1/analytics/comprehensive-dashboard?days={days}`
    *   **Method:** `GET`
    *   **Parameters:** `days` (query)

**18. `frontend/src/lib/prefetch.ts` (Multiple contexts)**
*   **Call:** `apiClient.getJobs(jobId, 1)`
    *   **Endpoint:** `/api/v1/jobs?skip={jobId}&limit=1`
    *   **Method:** `GET`
    *   **Parameters:** `skip={jobId}`, `limit=1` (query)
*   **Call:** `apiClient.getApplications(applicationId, 1)`
    *   **Endpoint:** `/api/v1/applications?skip={applicationId}&limit=1`
    *   **Method:** `GET`
    *   **Parameters:** `skip={applicationId}`, `limit=1` (query)
*   **Call:** `apiClient.getJobs(skip, limit)`
    *   **Endpoint:** `/api/v1/jobs?skip={skip}&limit={limit}`
    *   **Method:** `GET`
    *   **Parameters:** `skip`, `limit` (query)
*   **Call:** `apiClient.getApplications(skip, limit)`
    *   **Endpoint:** `/api/v1/applications?skip={skip}&limit={limit}`
    *   **Method:** `GET`
    *   **Parameters:** `skip`, `limit` (query)
*   **Call:** `apiClient.getAnalyticsSummary()`
    *   **Endpoint:** `/api/v1/analytics/summary`
    *   **Method:** `GET`
    *   **Parameters:** None

**19. `frontend/src/lib/bulkActions/jobActions.ts` (Component: `createJobBulkActions`)**
*   **Call:** `JobsService.updateJobApiV1JobsJobIdPut({ jobId, requestBody: { archived: true } as any })`
    *   **Endpoint:** `/api/v1/jobs/{jobId}`
    *   **Method:** `PUT`
    *   **Parameters:** `jobId` (path), `archived` (body)
*   **Call:** `JobsService.updateJobApiV1JobsJobIdPut({ jobId, requestBody: { is_saved: true } as any })`
    *   **Endpoint:** `/api/v1/jobs/{jobId}`
    *   **Method:** `PUT`
    *   **Parameters:** `jobId` (path), `is_saved` (body)
*   **Call:** `JobsService.updateJobApiV1JobsJobIdPut({ jobId, requestBody: { is_saved: false } as any })`
    *   **Endpoint:** `/api/v1/jobs/{jobId}`
    *   **Method:** `PUT`
    *   **Parameters:** `jobId` (path), `is_saved` (body)
*   **Call:** `JobsService.updateJobApiV1JobsJobIdPut({ jobId, requestBody: { is_viewed: true } as any })`
    *   **Endpoint:** `/api/v1/jobs/{jobId}`
    *   **Method:** `PUT`
    *   **Parameters:** `jobId` (path), `is_viewed` (body)
*   **Call:** `JobsService.updateJobApiV1JobsJobIdPut({ jobId, requestBody: { is_viewed: false } as any })`
    *   **Endpoint:** `/api/v1/jobs/{jobId}`
    *   **Method:** `PUT`
    *   **Parameters:** `jobId` (path), `is_viewed` (body)
*   **Call:** `JobsService.deleteJobApiV1JobsJobIdDelete({ jobId })`
    *   **Endpoint:** `/api/v1/jobs/{jobId}`
    *   **Method:** `DELETE`
    *   **Parameters:** `jobId` (path)

---

This analysis provides a comprehensive overview of how the frontend interacts with the backend API. The next steps would involve using this information to build the actual scanner logic, potentially automating the extraction and mapping process.