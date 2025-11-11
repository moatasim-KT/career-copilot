## Plan for Onboarding Wizard and Data Visualization Charts

### Phase 1: Onboarding Wizard Implementation

**Goal:** Implement a multi-step onboarding wizard to guide users through profile setup and preferences.

**Tasks:**

1.  **Create `OnboardingWizard` Component:**
    *   Create `frontend/src/components/onboarding/OnboardingWizard.tsx`.
    *   Implement a multi-step wizard structure using React state (e.g., `useState` for current step, `useReducer` for overall wizard state).
    *   Add a progress indicator (e.g., using `ProgressBar` from `frontend/src/components/ui/`).
    *   Implement Next, Back, and Skip buttons.
    *   Implement smooth transitions between steps (e.g., using `framer-motion`).
    *   Integrate `Modal` from `frontend/src/components/ui/` to host the wizard.

2.  **Create Step 1: Welcome & Profile Setup (`WelcomeStep.tsx`)**
    *   Create `frontend/src/components/onboarding/steps/WelcomeStep.tsx`.
    *   Display a welcome message and value proposition.
    *   Collect user's name, email (pre-fill if available from authentication context).
    *   Add optional profile photo upload using `FileUpload` from `frontend/src/components/ui/`.
    *   Add input for job title/role using `Input` from `frontend/src/components/ui/`.
    *   Add dropdown for years of experience (0-1, 1-3, 3-5, 5-10, 10+) using `Select` from `frontend/src/components/ui/`.
    *   Implement form validation for this step.
    *   Save progress to backend using `apiClient.user.updateProfile()`.

3.  **Create Step 2: Skills & Expertise (`SkillsStep.tsx`)**
    *   Create `frontend/src/components/onboarding/steps/SkillsStep.tsx`.
    *   Implement multi-select skill tags (e.g., using `MultiSelect2` or a custom component with `Checkbox` from `frontend/src/components/ui/`).
    *   Show popular skill suggestions.
    *   Add a search functionality for skills.
    *   Allow users to add custom skills.
    *   Add optional proficiency level per skill.
    *   Save progress to backend using `apiClient.user.updateProfile()`.

4.  **Create Step 3: Resume Upload (`ResumeStep.tsx`)**
    *   Create `frontend/src/components/onboarding/steps/ResumeStep.tsx`.
    *   Add file upload with drag & drop functionality using `FileUpload` from `frontend/src/components/ui/`.
    *   Support PDF and DOCX formats.
    *   Implement parsing of resume with AI (call backend API for this).
    *   Auto-fill skills from the parsed resume.
    *   Allow skipping this step if no resume is available.
    *   Save progress to backend.

5.  **Create Step 4: Job Preferences (`PreferencesStep.tsx`)**
    *   Create `frontend/src/components/onboarding/steps/PreferencesStep.tsx`.
    *   Add multi-select for preferred job titles.
    *   Add input for preferred locations (city, state, or remote).
    *   Add salary expectations (range slider or input fields).
    *   Add work arrangement preference (Remote, Hybrid, On-site).
    *   Add optional company size preference.
    *   Add optional industry preference.
    *   Save progress to backend using `apiClient.user.updateProfile()`.

6.  **Create Step 5: Feature Tour (`FeatureTourStep.tsx`)**
    *   Create `frontend/src/components/onboarding/steps/FeatureTourStep.tsx`.
    *   Implement an interactive tour of key features (dashboard, jobs, applications, command palette, notification center).
    *   Use animated pointers and tooltips to highlight features.

7.  **Create Completion Screen (`CompletionStep.tsx`)**
    *   Create `frontend/src/components/onboarding/steps/CompletionStep.tsx`.
    *   Show a success animation.
    *   Display first recommended jobs.
    *   Add CTA buttons: "View Dashboard", "Browse Jobs".
    *   Add an option to retake onboarding in settings.

8.  **Implement Skip and Resume Logic:**
    *   Ensure each step can be skipped individually.
    *   Implement logic to skip the entire onboarding process.
    *   Save onboarding progress to the backend after each step.
    *   Implement logic to resume from the last incomplete step if interrupted.
    *   Display onboarding progress in the user's profile.

### Phase 2: Data Visualization Charts Implementation

**Goal:** Implement various data visualization charts using `recharts` to provide insights.

**Tasks:**

1.  **Create `ChartWrapper` Component:**
    *   Create `frontend/src/components/charts/ChartWrapper.tsx`.
    *   Add consistent styling using design tokens.
    *   Implement a loading skeleton state.
    *   Implement an error state.
    *   Add an export button (e.g., to CSV, PNG).
    *   Add a full-screen mode toggle.

2.  **Create `ApplicationStatusChart`:**
    *   Create `frontend/src/components/charts/ApplicationStatusChart.tsx`.
    *   Implement a pie or donut chart using `recharts`.
    *   Show status distribution (Applied, Interviewing, Offer, Rejected).
    *   Add interactive tooltips with counts and percentages.
    *   Implement click functionality on slices to filter applications by status.
    *   Add smooth animations on load and data changes.
    *   Ensure dark mode support.
    *   Fetch data using `apiClient.analytics`.

3.  **Create `ApplicationTimelineChart`:**
    *   Create `frontend/src/components/charts/ApplicationTimelineChart.tsx`.
    *   Implement a line chart using `recharts` showing applications over time.
    *   X-axis: dates, Y-axis: application count.
    *   Add an optional trend line.
    *   Add hover tooltips with exact count and date.
    *   Implement zoom/pan controls for large date ranges.
    *   Ensure dark mode support.
    *   Fetch data using `apiClient.analytics`.

4.  **Create `SalaryDistributionChart`:**
    *   Create `frontend/src/components/charts/SalaryDistributionChart.tsx`.
    *   Implement a bar chart or histogram using `recharts` showing salary ranges.
    *   X-axis: salary buckets, Y-axis: job count.
    *   Highlight the user's target salary range.
    *   Add interactive tooltips.
    *   Ensure dark mode support.
    *   Fetch data using `apiClient.analytics`.

5.  **Create `SkillsDemandChart`:**
    *   Create `frontend/src/components/charts/SkillsDemandChart.tsx`.
    *   Implement a bar chart using `recharts` showing top skills in job postings.
    *   Compare with user's skills (overlay).
    *   Implement clickable bars to filter jobs by skill.
    *   Add sorting options (frequency, match rate, trending).
    *   Ensure dark mode support.
    *   Fetch data using `apiClient.analytics`.

6.  **Create `SuccessRateChart`:**
    *   Create `frontend/src/components/charts/SuccessRateChart.tsx`.
    *   Implement a funnel chart using `recharts`: Applied → Interviewed → Offer → Accepted.
    *   Show conversion rates at each stage.
    *   Add optional benchmarking against averages.
    *   Add interactive hover states.
    *   Ensure dark mode support.
    *   Fetch data using `apiClient.analytics`.

7.  **Add Chart Interactivity:**
    *   Implement zoom/pan controls for time-series charts.
    *   Add legend toggle to show/hide datasets.
    *   Add data export button (CSV, PNG).
    *   Add full-screen mode for detailed analysis.
    *   Ensure responsive charts (adapt to mobile).

8.  **Integrate Charts into Dashboard:**
    *   Update `frontend/src/components/pages/Dashboard.tsx` to include the new charts.
    *   Create a responsive chart grid layout.
    *   Add chart loading skeletons.
    *   Test with real data.

### Phase 3: WebSocket Real-time Updates Implementation

**Goal:** Implement real-time updates for job recommendations, application status, and notifications using WebSockets.

**Tasks:**

1.  **Create `WebSocketClient` (if not already robust):**
    *   Review `frontend/src/lib/api/websocket.ts`. Ensure it handles connection lifecycle, auto-reconnect with exponential backoff, event subscription, and a message queue for offline mode. If any of these are missing or not robust, enhance the existing `WebSocketService`.

2.  **Create `ConnectionStatus` Component:**
    *   Create `frontend/src/components/ui/ConnectionStatus.tsx`.
    *   Display a small indicator in the Navigation header (Connected: green, Connecting: yellow, Disconnected: red).
    *   Add a tooltip with the status message.
    *   Add a manual reconnect button.
    *   Utilize `webSocketService.getConnectionInfo()` and `webSocketService.getHealthStatus()`.

3.  **Implement Real-time Job Recommendations:**
    *   Listen for `job:recommendation` WebSocket events using `webSocketService.on()`.
    *   Show toast notifications for new job matches.
    *   Update the jobs list in real-time without page refresh.
    *   Add a badge on the Jobs tab: "X new matches".
    *   Implement smooth animation for new items appearing.

4.  **Implement Real-time Application Status Updates:**
    *   Listen for `application:status_change` WebSocket events.
    *   Update application status in the UI instantly.
    *   Show toast notification: "Application status changed to {status}".
    *   Update dashboard stats in real-time.
    *   Add a badge animation for status changes.

5.  **Implement Real-time Notifications:**
    *   Listen for `notification:new` WebSocket events.
    *   Display toast notifications.
    *   Update the notification bell badge count.
    *   Add new notifications to the notification center list.
    *   Implement sound playback based on user preferences.

6.  **Handle Reconnection and Offline Mode:**
    *   Detect network offline/online events.
    *   Show a "reconnecting" toast message.
    *   Ensure `WebSocketService` handles retry connection with exponential backoff.
    *   Implement data resynchronization on reconnect (fetch latest data).
    *   Ensure `WebSocketService` handles message queue for missed events during offline periods.

7.  **Test WebSocket Functionality:**
    *   Test real-time updates across multiple browser tabs.
    *   Test reconnection after network disruption.
    *   Test on mobile devices.
    *   Test with slow network conditions.

### Phase 4: Drag & Drop Features Implementation

**Goal:** Implement drag-and-drop functionality for dashboard widgets and a Kanban board.

**Tasks:**

1.  **Create Draggable Dashboard Widgets:**
    *   Update the Dashboard component to use `@dnd-kit`.
    *   Make dashboard cards/widgets draggable using `@dnd-kit/sortable`.
    *   Allow reordering of widgets.
    *   Save widget layout to user preferences (using `apiClient.user.updateSettings()`).
    *   Add a "Reset layout" button.
    *   Implement visual feedback during drag (ghost element, drop zones).

2.  **Create Kanban Board for Applications:**
    *   Create `frontend/src/components/pages/ApplicationKanban.tsx`.
    *   Create columns: Applied, Interviewing, Offer, Rejected.
    *   Make application cards draggable between columns.
    *   Update application status on drop (with API call using `apiClient.applications.update()`).
    *   Implement optimistic updates with rollback on error.
    *   Add smooth animations.

3.  **Add Drag-to-Reorder for Lists:**
    *   Implement drag-to-reorder for custom job lists.
    *   Implement drag-to-reorder for saved searches.
    *   Save the new order to the backend.
    *   Add visual feedback (drag handle, drop indicator).

4.  **Add Keyboard Support for Drag & Drop:**
    *   Implement keyboard navigation for drag & drop (Space to pick up, arrow keys to move, Enter to drop).
    *   Announce drag/drop actions to screen readers.
    *   Add ARIA live regions for status updates.

5.  **Test Drag & Drop Functionality:**
    *   Test on desktop browsers.
    *   Test touch drag on mobile/tablet.
    *   Test keyboard navigation.
    *   Test with a screen reader.

This plan covers all the requirements outlined in the research document.