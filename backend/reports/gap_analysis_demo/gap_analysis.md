# Frontend-Backend Integration Gap Analysis Report

**Generated:** 2025-11-11 21:27:40

## Executive Summary

- **Total Gaps:** 63
- **Critical:** 3
- **High Priority:** 22
- **Medium Priority:** 20
- **Low Priority:** 18

## Statistics

- **Unique Endpoints Missing:** 35
- **Components Affected:** 29

### Gaps by Type

- **missing_endpoint:** 63

## Detected Gaps


### CRITICAL Priority Gaps

#### GET /api/v1/auth/refresh

**Type:** Missing Endpoint  
**Severity:** critical  
**Component:** `lib.api.examples`  
**Location:** `lib/api/examples.ts:61`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/auth/refresh but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve refresh data. Add route handler in appropriate router file.

---

#### GET /api/v1/auth/refresh

**Type:** Missing Endpoint  
**Severity:** critical  
**Component:** `lib.api.examples`  
**Location:** `lib/api/examples.ts:130`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/auth/refresh but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve refresh data. Add route handler in appropriate router file.

---

#### GET /api/v1/auth/refresh

**Type:** Missing Endpoint  
**Severity:** critical  
**Component:** `lib.api.examples`  
**Location:** `lib/api/examples.ts:130`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/auth/refresh but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve refresh data. Add route handler in appropriate router file.

---


### HIGH Priority Gaps

#### GET /api/v1/jobs/search

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `hooks.useSearchJobs`  
**Location:** `hooks/useSearchJobs.ts:19`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/jobs/search but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve search data. Add route handler in appropriate router file. Include query parameters for filtering and pagination.

---

#### PUT /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `hooks.useUpdateApplication`  
**Location:** `hooks/useUpdateApplication.ts:12`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing applications. Include ID validation and update logic.

---

#### GET /api/v1/applications/search

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `hooks.useSearchApplications`  
**Location:** `hooks/useSearchApplications.ts:19`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/applications/search but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve search data. Add route handler in appropriate router file. Include query parameters for filtering and pagination.

---

#### GET /api/v1/analytics/comprehensive-dashboard

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `hooks.useAnalytics`  
**Location:** `hooks/useAnalytics.ts:37`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/analytics/comprehensive-dashboard but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve comprehensive-dashboard data. Add route handler in appropriate router file.

---

#### PUT /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.optimisticUpdates`  
**Location:** `lib/optimisticUpdates.ts:54`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing applications. Include ID validation and update logic.

---

#### GET /api/applications

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.optimisticUpdates`  
**Location:** `lib/optimisticUpdates.ts:250`  
**Status:** not_found  

**Description:** Frontend expects GET /api/applications but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve applications data. Add route handler in appropriate router file.

---

#### GET /api/jobs

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.swr`  
**Location:** `lib/swr.ts:188`  
**Status:** not_found  

**Description:** Frontend expects GET /api/jobs but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve jobs data. Add route handler in appropriate router file.

---

#### GET /api/applications

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.swr`  
**Location:** `lib/swr.ts:206`  
**Status:** not_found  

**Description:** Frontend expects GET /api/applications but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve applications data. Add route handler in appropriate router file.

---

#### PUT /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.bulkActions.applicationActions`  
**Location:** `lib/bulkActions/applicationActions.ts:35`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing applications. Include ID validation and update logic.

---

#### PUT /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.bulkActions.applicationActions`  
**Location:** `lib/bulkActions/applicationActions.ts:71`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing applications. Include ID validation and update logic.

---

#### PUT /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.bulkActions.applicationActions`  
**Location:** `lib/bulkActions/applicationActions.ts:107`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing applications. Include ID validation and update logic.

---

#### PUT /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.bulkActions.applicationActions`  
**Location:** `lib/bulkActions/applicationActions.ts:143`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing applications. Include ID validation and update logic.

---

#### PUT /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.bulkActions.applicationActions`  
**Location:** `lib/bulkActions/applicationActions.ts:179`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing applications. Include ID validation and update logic.

---

#### PUT /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.bulkActions.applicationActions`  
**Location:** `lib/bulkActions/applicationActions.ts:215`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing applications. Include ID validation and update logic.

---

#### PUT /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.bulkActions.applicationActions`  
**Location:** `lib/bulkActions/applicationActions.ts:251`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing applications. Include ID validation and update logic.

---

#### DELETE /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.bulkActions.applicationActions`  
**Location:** `lib/bulkActions/applicationActions.ts:338`  
**Status:** not_found  

**Description:** Frontend expects DELETE /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement DELETE endpoint to remove applications. Include ID validation and deletion logic.

---

#### GET /api/v1/jobs/cached

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.api.examples`  
**Location:** `lib/api/examples.ts:178`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/jobs/cached but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve cached data. Add route handler in appropriate router file.

---

#### GET /api/v1/jobs/cached

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `lib.api.config`  
**Location:** `lib/api/config.ts:89`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/jobs/cached but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve cached data. Add route handler in appropriate router file.

---

#### GET /api/v1/analytics/comprehensive-dashboard

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `components.pages.AnalyticsPage`  
**Location:** `components/pages/AnalyticsPage.tsx:93`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/analytics/comprehensive-dashboard but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve comprehensive-dashboard data. Add route handler in appropriate router file.

---

#### PUT /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `components.pages.ApplicationsPage`  
**Location:** `components/pages/ApplicationsPage.tsx:117`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing applications. Include ID validation and update logic.

---

#### PUT /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `components.pages.ApplicationsPage`  
**Location:** `components/pages/ApplicationsPage.tsx:184`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing applications. Include ID validation and update logic.

---

#### PUT /api/v1/applications/{id}

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `components.pages.ApplicationsPage`  
**Location:** `components/pages/ApplicationsPage.tsx:209`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/applications/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing applications. Include ID validation and update logic.

---


### MEDIUM Priority Gaps

#### GET /api/v1/notifications

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotificationsQuery`  
**Location:** `hooks/useNotificationsQuery.ts:29`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/notifications but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve notifications data. Add route handler in appropriate router file.

---

#### GET /api/v1/notifications/preferences

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotificationsQuery`  
**Location:** `hooks/useNotificationsQuery.ts:47`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/notifications/preferences but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve preferences data. Add route handler in appropriate router file.

---

#### PUT /api/v1/notifications/{id}/read

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotificationsQuery`  
**Location:** `hooks/useNotificationsQuery.ts:66`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notifications/{id}/read but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing read. Include ID validation and update logic.

---

#### PUT /api/v1/notifications/read-all

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotificationsQuery`  
**Location:** `hooks/useNotificationsQuery.ts:115`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notifications/read-all but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing read-all. Include ID validation and update logic.

---

#### DELETE /api/v1/notifications/{id}

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotificationsQuery`  
**Location:** `hooks/useNotificationsQuery.ts:159`  
**Status:** not_found  

**Description:** Frontend expects DELETE /api/v1/notifications/{id} but endpoint does not exist in backend

**Recommendation:** Implement DELETE endpoint to remove notifications. Include ID validation and deletion logic.

---

#### PUT /api/v1/notifications/preferences

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotificationsQuery`  
**Location:** `hooks/useNotificationsQuery.ts:204`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notifications/preferences but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing preferences. Include ID validation and update logic.

---

#### GET /api/v1/profile

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useUserProfile`  
**Location:** `hooks/useUserProfile.ts:20`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/profile but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve profile data. Add route handler in appropriate router file.

---

#### PUT /api/v1/profile

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useUserProfile`  
**Location:** `hooks/useUserProfile.ts:39`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/profile but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing profile. Include ID validation and update logic.

---

#### GET /api/v1/notifications

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotifications`  
**Location:** `hooks/useNotifications.ts:55`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/notifications but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve notifications data. Add route handler in appropriate router file.

---

#### PUT /api/v1/notifications/{id}/read

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotifications`  
**Location:** `hooks/useNotifications.ts:84`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notifications/{id}/read but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing read. Include ID validation and update logic.

---

#### PUT /api/v1/notifications/{id}/unread

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotifications`  
**Location:** `hooks/useNotifications.ts:110`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notifications/{id}/unread but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing unread. Include ID validation and update logic.

---

#### PUT /api/v1/notifications/read-all

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotifications`  
**Location:** `hooks/useNotifications.ts:137`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notifications/read-all but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing read-all. Include ID validation and update logic.

---

#### DELETE /api/v1/notifications/{id}

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotifications`  
**Location:** `hooks/useNotifications.ts:162`  
**Status:** not_found  

**Description:** Frontend expects DELETE /api/v1/notifications/{id} but endpoint does not exist in backend

**Recommendation:** Implement DELETE endpoint to remove notifications. Include ID validation and deletion logic.

---

#### POST /api/v1/notifications/bulk-delete

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotifications`  
**Location:** `hooks/useNotifications.ts:185`  
**Status:** not_found  

**Description:** Frontend expects POST /api/v1/notifications/bulk-delete but endpoint does not exist in backend

**Recommendation:** Implement POST endpoint to create new bulk-delete. Include request validation and database insertion. Support batch operations with transaction handling.

---

#### GET /api/profile

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.swr`  
**Location:** `lib/swr.ts:224`  
**Status:** not_found  

**Description:** Frontend expects GET /api/profile but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve profile data. Add route handler in appropriate router file.

---

#### GET /api/analytics/summary

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.swr`  
**Location:** `lib/swr.ts:243`  
**Status:** not_found  

**Description:** Frontend expects GET /api/analytics/summary but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve summary data. Add route handler in appropriate router file.

---

#### GET /api/notifications

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.swr`  
**Location:** `lib/swr.ts:263`  
**Status:** not_found  

**Description:** Frontend expects GET /api/notifications but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve notifications data. Add route handler in appropriate router file.

---

#### GET /api/v1/analytics

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.api.examples`  
**Location:** `lib/api/examples.ts:179`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/analytics but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve analytics data. Add route handler in appropriate router file.

---

#### PUT /api/v1/notificationsettings/{id}

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `components.settings.NotificationPreferences`  
**Location:** `components/settings/NotificationPreferences.tsx:260`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notificationsettings/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing notificationsettings. Include ID validation and update logic.

---

#### PUT /api/v1/profile

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `components.features.ResumeUpload`  
**Location:** `components/features/ResumeUpload.tsx:190`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/profile but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing profile. Include ID validation and update logic.

---


### LOW Priority Gaps

#### GET /api/health

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `hooks.useOfflineMode`  
**Location:** `hooks/useOfflineMode.ts:44`  
**Status:** not_found  

**Description:** Frontend expects GET /api/health but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve health data. Add route handler in appropriate router file.

---

#### GET /api/push/subscribe

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `lib.pushNotifications`  
**Location:** `lib/pushNotifications.ts:175`  
**Status:** not_found  

**Description:** Frontend expects GET /api/push/subscribe but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve subscribe data. Add route handler in appropriate router file.

---

#### PUT /api/v1/status/{id}

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `lib.utils.optimistic`  
**Location:** `lib/utils/optimistic.ts:20`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/status/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing status. Include ID validation and update logic.

---

#### GET /api/refresh-token

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `lib.api.config`  
**Location:** `lib/api/config.ts:161`  
**Status:** not_found  

**Description:** Frontend expects GET /api/refresh-token but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve refresh-token data. Add route handler in appropriate router file.

---

#### GET /api/refresh-token

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `lib.api.config`  
**Location:** `lib/api/config.ts:188`  
**Status:** not_found  

**Description:** Frontend expects GET /api/refresh-token but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve refresh-token data. Add route handler in appropriate router file.

---

#### GET /api/sentry-example-api

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `app.sentry-example-page.page`  
**Location:** `app/sentry-example-page/page.tsx:55`  
**Status:** not_found  

**Description:** Frontend expects GET /api/sentry-example-api but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve sentry-example-api data. Add route handler in appropriate router file.

---

#### GET /api/v1/health/comprehensive

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `app.health.page`  
**Location:** `app/health/page.tsx:27`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/health/comprehensive but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve comprehensive data. Add route handler in appropriate router file.

---

#### GET /api/v1/health/comprehensive

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `app.health.page`  
**Location:** `app/health/page.tsx:27`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/health/comprehensive but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve comprehensive data. Add route handler in appropriate router file.

---

#### POST /api/v1/resume/upload

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.ui.FileUpload`  
**Location:** `components/ui/FileUpload.tsx:84`  
**Status:** not_found  

**Description:** Frontend expects POST /api/v1/resume/upload but endpoint does not exist in backend

**Recommendation:** Implement POST endpoint to create new upload. Include request validation and database insertion.

---

#### DELETE /api/v1/search/{id}

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.features.SavedSearches`  
**Location:** `components/features/SavedSearches.tsx:376`  
**Status:** not_found  

**Description:** Frontend expects DELETE /api/v1/search/{id} but endpoint does not exist in backend

**Recommendation:** Implement DELETE endpoint to remove search. Include ID validation and deletion logic. Include query parameters for filtering and pagination.

---

#### GET /api/v1/interview/start

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.features.InterviewPractice`  
**Location:** `components/features/InterviewPractice.tsx:130`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/interview/start but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve start data. Add route handler in appropriate router file.

---

#### POST /api/v1/resume/upload

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.features.ResumeUpload`  
**Location:** `components/features/ResumeUpload.tsx:114`  
**Status:** not_found  

**Description:** Frontend expects POST /api/v1/resume/upload but endpoint does not exist in backend

**Recommendation:** Implement POST endpoint to create new upload. Include request validation and database insertion.

---

#### POST /api/v1/content/generate

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.features.ContentGeneration`  
**Location:** `components/features/ContentGeneration.tsx:89`  
**Status:** not_found  

**Description:** Frontend expects POST /api/v1/content/generate but endpoint does not exist in backend

**Recommendation:** Implement POST endpoint to create new generate. Include request validation and database insertion.

---

#### GET /api/health

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.monitoring.HealthMonitor`  
**Location:** `components/monitoring/HealthMonitor.tsx:76`  
**Status:** not_found  

**Description:** Frontend expects GET /api/health but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve health data. Add route handler in appropriate router file.

---

#### GET /api/v1/recommendations

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.pages.RecommendationsPage`  
**Location:** `components/pages/RecommendationsPage.tsx:35`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/recommendations but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve recommendations data. Add route handler in appropriate router file.

---

#### GET /api/v1/skill-gap

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.pages.RecommendationsPage`  
**Location:** `components/pages/RecommendationsPage.tsx:42`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/skill-gap but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve skill-gap data. Add route handler in appropriate router file.

---

#### GET /api/feedback

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.help.FeedbackWidget`  
**Location:** `components/help/FeedbackWidget.tsx:148`  
**Status:** not_found  

**Description:** Frontend expects GET /api/feedback but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve feedback data. Add route handler in appropriate router file.

---

#### GET /api/v1/

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.analytics.AnalyticsDashboard`  
**Location:** `components/analytics/AnalyticsDashboard.tsx:126`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/ but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve  data. Add route handler in appropriate router file.

---

