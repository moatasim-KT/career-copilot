# Frontend-Backend Integration Gap Analysis Report

**Generated:** 2025-11-12 02:40:27

## Executive Summary

- **Total Gaps:** 38
- **Critical:** 0
- **High Priority:** 1
- **Medium Priority:** 26
- **Low Priority:** 11

## Statistics

- **Unique Endpoints Missing:** 26
- **Components Affected:** 20

### Gaps by Type

- **missing_endpoint:** 38

## Detected Gaps


### HIGH Priority Gaps

#### GET /api/v1/

**Type:** Missing Endpoint  
**Severity:** high  
**Component:** `components.analytics.AnalyticsDashboard`  
**Location:** `components/analytics/AnalyticsDashboard.tsx:126`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/ but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve  data. Add route handler in appropriate router file.

**Affected Features:** analytics

---


### MEDIUM Priority Gaps

#### PUT /api/v1/notifications/{id}/read

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotificationsQuery`  
**Location:** `hooks/useNotificationsQuery.ts:66`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notifications/{id}/read but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing read. Include ID validation and update logic.

**Affected Features:** useNotificationsQuery, useNotifications

---

#### PUT /api/v1/notifications/read-all

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotificationsQuery`  
**Location:** `hooks/useNotificationsQuery.ts:115`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notifications/read-all but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing read-all. Include ID validation and update logic.

**Affected Features:** useNotificationsQuery, useNotifications

---

#### DELETE /api/v1/notifications/{id}

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotificationsQuery`  
**Location:** `hooks/useNotificationsQuery.ts:159`  
**Status:** not_found  

**Description:** Frontend expects DELETE /api/v1/notifications/{id} but endpoint does not exist in backend

**Recommendation:** Implement DELETE endpoint to remove notifications. Include ID validation and deletion logic.

**Affected Features:** useNotificationsQuery, useNotifications

---

#### GET /api/v1/profile

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useUserProfile`  
**Location:** `hooks/useUserProfile.ts:20`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/profile but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve profile data. Add route handler in appropriate router file.

**Affected Features:** useUserProfile

---

#### PUT /api/v1/profile

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useUserProfile`  
**Location:** `hooks/useUserProfile.ts:39`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/profile but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing profile. Include ID validation and update logic.

**Affected Features:** useUserProfile, ResumeUpload

---

#### PUT /api/v1/notifications/{id}/read

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotifications`  
**Location:** `hooks/useNotifications.ts:84`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notifications/{id}/read but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing read. Include ID validation and update logic.

**Affected Features:** useNotificationsQuery, useNotifications

---

#### PUT /api/v1/notifications/{id}/unread

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotifications`  
**Location:** `hooks/useNotifications.ts:110`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notifications/{id}/unread but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing unread. Include ID validation and update logic.

**Affected Features:** useNotifications

---

#### PUT /api/v1/notifications/read-all

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotifications`  
**Location:** `hooks/useNotifications.ts:137`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notifications/read-all but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing read-all. Include ID validation and update logic.

**Affected Features:** useNotificationsQuery, useNotifications

---

#### DELETE /api/v1/notifications/{id}

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotifications`  
**Location:** `hooks/useNotifications.ts:162`  
**Status:** not_found  

**Description:** Frontend expects DELETE /api/v1/notifications/{id} but endpoint does not exist in backend

**Recommendation:** Implement DELETE endpoint to remove notifications. Include ID validation and deletion logic.

**Affected Features:** useNotificationsQuery, useNotifications

---

#### POST /api/v1/notifications/bulk-delete

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `hooks.useNotifications`  
**Location:** `hooks/useNotifications.ts:185`  
**Status:** not_found  

**Description:** Frontend expects POST /api/v1/notifications/bulk-delete but endpoint does not exist in backend

**Recommendation:** Implement POST endpoint to create new bulk-delete. Include request validation and database insertion. Support batch operations with transaction handling.

**Affected Features:** useNotifications

---

#### GET /api/applications

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.optimisticUpdates`  
**Location:** `lib/optimisticUpdates.ts:250`  
**Status:** not_found  

**Description:** Frontend expects GET /api/applications but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve applications data. Add route handler in appropriate router file.

**Affected Features:** optimisticUpdates, swr

---

#### GET /api/jobs

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.swr`  
**Location:** `lib/swr.ts:188`  
**Status:** not_found  

**Description:** Frontend expects GET /api/jobs but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve jobs data. Add route handler in appropriate router file.

**Affected Features:** swr

---

#### GET /api/applications

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.swr`  
**Location:** `lib/swr.ts:206`  
**Status:** not_found  

**Description:** Frontend expects GET /api/applications but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve applications data. Add route handler in appropriate router file.

**Affected Features:** optimisticUpdates, swr

---

#### GET /api/profile

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.swr`  
**Location:** `lib/swr.ts:224`  
**Status:** not_found  

**Description:** Frontend expects GET /api/profile but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve profile data. Add route handler in appropriate router file.

**Affected Features:** swr

---

#### GET /api/analytics/summary

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.swr`  
**Location:** `lib/swr.ts:243`  
**Status:** not_found  

**Description:** Frontend expects GET /api/analytics/summary but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve summary data. Add route handler in appropriate router file.

**Affected Features:** swr

---

#### GET /api/notifications

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.swr`  
**Location:** `lib/swr.ts:263`  
**Status:** not_found  

**Description:** Frontend expects GET /api/notifications but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve notifications data. Add route handler in appropriate router file.

**Affected Features:** swr

---

#### GET /api/v1/auth/refresh

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.api.examples`  
**Location:** `lib/api/examples.ts:61`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/auth/refresh but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve refresh data. Add route handler in appropriate router file.

**Affected Features:** api

---

#### GET /api/v1/auth/refresh

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.api.examples`  
**Location:** `lib/api/examples.ts:130`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/auth/refresh but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve refresh data. Add route handler in appropriate router file.

**Affected Features:** api

---

#### GET /api/v1/auth/refresh

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.api.examples`  
**Location:** `lib/api/examples.ts:130`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/auth/refresh but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve refresh data. Add route handler in appropriate router file.

**Affected Features:** api

---

#### GET /api/v1/jobs/cached

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.api.examples`  
**Location:** `lib/api/examples.ts:178`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/jobs/cached but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve cached data. Add route handler in appropriate router file.

**Affected Features:** api

---

#### GET /api/v1/analytics

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.api.examples`  
**Location:** `lib/api/examples.ts:179`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/analytics but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve analytics data. Add route handler in appropriate router file.

**Affected Features:** api

---

#### GET /api/refresh-token

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.api.config`  
**Location:** `lib/api/config.ts:161`  
**Status:** not_found  

**Description:** Frontend expects GET /api/refresh-token but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve refresh-token data. Add route handler in appropriate router file.

**Affected Features:** api

---

#### GET /api/refresh-token

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.api.config`  
**Location:** `lib/api/config.ts:188`  
**Status:** not_found  

**Description:** Frontend expects GET /api/refresh-token but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve refresh-token data. Add route handler in appropriate router file.

**Affected Features:** api

---

#### GET /api/v1/jobs/cached

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `lib.api.config`  
**Location:** `lib/api/config.ts:89`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/jobs/cached but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve cached data. Add route handler in appropriate router file.

**Affected Features:** api

---

#### PUT /api/v1/notificationsettings/{id}

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `components.settings.NotificationPreferences`  
**Location:** `components/settings/NotificationPreferences.tsx:260`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/notificationsettings/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing notificationsettings. Include ID validation and update logic.

**Affected Features:** settings

---

#### PUT /api/v1/profile

**Type:** Missing Endpoint  
**Severity:** medium  
**Component:** `components.features.ResumeUpload`  
**Location:** `components/features/ResumeUpload.tsx:190`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/profile but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing profile. Include ID validation and update logic.

**Affected Features:** useUserProfile, ResumeUpload

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

**Affected Features:** useOfflineMode, monitoring

---

#### GET /api/push/subscribe

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `lib.pushNotifications`  
**Location:** `lib/pushNotifications.ts:175`  
**Status:** not_found  

**Description:** Frontend expects GET /api/push/subscribe but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve subscribe data. Add route handler in appropriate router file.

**Affected Features:** pushNotifications

---

#### PUT /api/v1/status/{id}

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `lib.utils.optimistic`  
**Location:** `lib/utils/optimistic.ts:20`  
**Status:** not_found  

**Description:** Frontend expects PUT /api/v1/status/{id} but endpoint does not exist in backend

**Recommendation:** Implement PUT endpoint to update existing status. Include ID validation and update logic.

**Affected Features:** optimistic

---

#### GET /api/sentry-example-api

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `app.sentry-example-page.page`  
**Location:** `app/sentry-example-page/page.tsx:55`  
**Status:** not_found  

**Description:** Frontend expects GET /api/sentry-example-api but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve sentry-example-api data. Add route handler in appropriate router file.

**Affected Features:** app

---

#### GET /api/v1/health/comprehensive

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `app.health.page`  
**Location:** `app/health/page.tsx:27`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/health/comprehensive but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve comprehensive data. Add route handler in appropriate router file.

**Affected Features:** app

---

#### GET /api/v1/health/comprehensive

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `app.health.page`  
**Location:** `app/health/page.tsx:27`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/health/comprehensive but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve comprehensive data. Add route handler in appropriate router file.

**Affected Features:** app

---

#### DELETE /api/v1/search/{id}

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.features.SavedSearches`  
**Location:** `components/features/SavedSearches.tsx:376`  
**Status:** not_found  

**Description:** Frontend expects DELETE /api/v1/search/{id} but endpoint does not exist in backend

**Recommendation:** Implement DELETE endpoint to remove search. Include ID validation and deletion logic. Include query parameters for filtering and pagination.

**Affected Features:** SavedSearches

---

#### GET /api/v1/interview/start

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.features.InterviewPractice`  
**Location:** `components/features/InterviewPractice.tsx:130`  
**Status:** not_found  

**Description:** Frontend expects GET /api/v1/interview/start but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve start data. Add route handler in appropriate router file.

**Affected Features:** InterviewPractice

---

#### POST /api/v1/content/generate

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.features.ContentGeneration`  
**Location:** `components/features/ContentGeneration.tsx:89`  
**Status:** not_found  

**Description:** Frontend expects POST /api/v1/content/generate but endpoint does not exist in backend

**Recommendation:** Implement POST endpoint to create new generate. Include request validation and database insertion.

**Affected Features:** ContentGeneration

---

#### GET /api/health

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.monitoring.HealthMonitor`  
**Location:** `components/monitoring/HealthMonitor.tsx:76`  
**Status:** not_found  

**Description:** Frontend expects GET /api/health but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve health data. Add route handler in appropriate router file.

**Affected Features:** useOfflineMode, monitoring

---

#### GET /api/feedback

**Type:** Missing Endpoint  
**Severity:** low  
**Component:** `components.help.FeedbackWidget`  
**Location:** `components/help/FeedbackWidget.tsx:148`  
**Status:** not_found  

**Description:** Frontend expects GET /api/feedback but endpoint does not exist in backend

**Recommendation:** Implement GET endpoint to retrieve feedback data. Add route handler in appropriate router file.

**Affected Features:** help

---

