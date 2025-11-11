# Onboarding Wizard and Data Visualization Charts TODO List

### Phase 1: Onboarding Wizard Implementation

- [x] **1. Create `OnboardingWizard` Component** `[frontend]`
  - [x] 1.1. Create `frontend/src/components/onboarding/OnboardingWizard.tsx`.
  - [x] 1.2. Implement a multi-step wizard structure using React state.
  - [x] 1.3. Add a progress indicator using `ProgressBar`.
  - [x] 1.4. Implement Next, Back, and Skip buttons.
  - [x] 1.5. Implement smooth transitions between steps using `framer-motion`.
  - [x] 1.6. Integrate `Modal` to host the wizard.

- [x] **2. Create Step 1: Welcome & Profile Setup (`WelcomeStep.tsx`)** `[frontend]`
  - [x] 2.1. Create `frontend/src/components/onboarding/steps/WelcomeStep.tsx`.
  - [x] 2.2. Display a welcome message and value proposition.
  - [x] 2.3. Collect user's name, email (pre-fill if available).
  - [x] 2.4. Add optional profile photo upload using `FileUpload`.
  - [x] 2.5. Add input for job title/role using `Input`.
  - [x] 2.6. Add dropdown for years of experience using `Select`.
  - [x] 2.7. Implement form validation.
  - [x] 2.8. Save progress to backend using `apiClient.user.updateProfile()`. `[backend]`

- [x] **3. Create Step 2: Skills & Expertise (`SkillsStep.tsx`)** `[frontend]`
  - [x] 3.1. Create `frontend/src/components/onboarding/steps/SkillsStep.tsx`.
  - [x] 3.2. Implement multi-select skill tags.
  - [x] 3.3. Show popular skill suggestions.
  - [x] 3.4. Add a search functionality for skills.
  - [x] 3.5. Allow users to add custom skills.
  - [x] 3.6. Add optional proficiency level per skill.
  - [x] 3.7. Save progress to backend using `apiClient.user.updateProfile()`. `[backend]`

- [x] **4. Create Step 3: Resume Upload (`ResumeStep.tsx`)** `[frontend]`
  - [x] 4.1. Create `frontend/src/components/onboarding/steps/ResumeStep.tsx`.
  - [x] 4.2. Add file upload with drag & drop functionality using `FileUpload`.
  - [x] 4.3. Support PDF and DOCX formats.
  - [x] 4.4. Implement parsing of resume with AI (call backend API). `[backend]`
  - [x] 4.5. Auto-fill skills from the parsed resume.
  - [x] 4.6. Allow skipping this step.
  - [x] 4.7. Save progress to backend. `[backend]`

- [x] **5. Create Step 4: Job Preferences (`PreferencesStep.tsx`)** `[frontend]`
  - [x] 5.1. Create `frontend/src/components/onboarding/steps/PreferencesStep.tsx`.
  - [x] 5.2. Add multi-select for preferred job titles.
  - [x] 5.3. Add input for preferred locations.
  - [x] 5.4. Add salary expectations.
  - [x] 5.5. Add work arrangement preference.
  - [x] 5.6. Add optional company size preference.
  - [x] 5.7. Add optional industry preference.
  - [x] 5.8. Save progress to backend using `apiClient.user.updateProfile()`. `[backend]`

- [x] **6. Create Step 5: Feature Tour (`FeatureTourStep.tsx`)** `[frontend]`
  - [x] 6.1. Create `frontend/src/components/onboarding/steps/FeatureTourStep.tsx`.
  - [x] 6.2. Implement an interactive tour of key features.
  - [x] 6.3. Use animated pointers and tooltips.

- [x] **7. Create Completion Screen (`CompletionStep.tsx`)** `[frontend]`
  - [x] 7.1. Create `frontend/src/components/onboarding/steps/CompletionStep.tsx`.
  - [x] 7.2. Show a success animation.
  - [x] 7.3. Display first recommended jobs.
  - [x] 7.4. Add CTA buttons: "View Dashboard", "Browse Jobs".
  - [ ] 7.5. Add an option to retake onboarding in settings.

- [x] **8. Implement Skip and Resume Logic** `[frontend]` `[backend]`
  - [x] 8.1. Allow skipping individual steps.
  - [x] 8.2. Allow skipping the entire onboarding process.
  - [x] 8.3. Save onboarding progress to the backend after each step.
  - [x] 8.4. Resume from the last incomplete step if interrupted.
  - [ ] 8.5. Display onboarding progress in the user's profile.

### Phase 2: Data Visualization Charts Implementation

- [x] **1. Create `ChartWrapper` Component** `[frontend]`
  - [x] 1.1. Create `frontend/src/components/charts/ChartWrapper.tsx`.
  - [x] 1.2. Add consistent styling.
  - [x] 1.3. Implement a loading skeleton state.
  - [x] 1.4. Implement an error state.
  - [x] 1.5. Add an export button.
  - [x] 1.6. Add a full-screen mode toggle.

- [x] **2. Create `ApplicationStatusChart`** `[frontend]` (Parallel)
  - [x] 2.1. Create `frontend/src/components/charts/ApplicationStatusChart.tsx`.
  - [x] 2.2. Implement a pie or donut chart using `recharts`.
  - [x] 2.3. Add interactive tooltips.
  - [x] 2.4. Implement click functionality on slices.
  - [x] 2.5. Add smooth animations.
  - [x] 2.6. Ensure dark mode support.
  - [x] 2.7. Fetch data using `apiClient.analytics`. `[backend]`

- [x] **3. Create `ApplicationTimelineChart`** `[frontend]` (Parallel)
  - [x] 3.1. Create `frontend/src/components/charts/ApplicationTimelineChart.tsx`.
  - [x] 3.2. Implement a line chart using `recharts`.
  - [x] 3.3. Add an optional trend line.
  - [x] 3.4. Add hover tooltips.
  - [x] 3.5. Implement zoom/pan controls.
  - [x] 3.6. Ensure dark mode support.
  - [x] 3.7. Fetch data using `apiClient.analytics`. `[backend]`

- [x] **4. Create `SalaryDistributionChart`** `[frontend]` (Parallel)
  - [x] 4.1. Create `frontend/src/components/charts/SalaryDistributionChart.tsx`.
  - [x] 4.2. Implement a bar chart or histogram using `recharts`.
  - [x] 4.3. Highlight the user's target salary range.
  - [x] 4.4. Add interactive tooltips.
  - [x] 4.5. Ensure dark mode support.
  - [x] 4.6. Fetch data using `apiClient.analytics`. `[backend]`

- [x] **5. Create `SkillsDemandChart`** `[frontend]` (Parallel)
  - [x] 5.1. Create `frontend/src/components/charts/SkillsDemandChart.tsx`.
  - [x] 5.2. Implement a bar chart using `recharts`.
  - [x] 5.3. Compare with user's skills.
  - [x] 5.4. Implement clickable bars.
  - [x] 5.5. Add sorting options.
  - [x] 5.6. Ensure dark mode support.
  - [x] 5.7. Fetch data using `apiClient.analytics`. `[backend]`

- [x] **6. Create `SuccessRateChart`** `[frontend]` (Parallel)
  - [x] 6.1. Create `frontend/src/components/charts/SuccessRateChart.tsx`.
  - [x] 6.2. Implement a funnel chart using `recharts`.
  - [x] 6.3. Show conversion rates.
  - [x] 6.4. Add optional benchmarking.
  - [x] 6.5. Add interactive hover states.
  - [x] 6.6. Ensure dark mode support.
  - [x] 6.7. Fetch data using `apiClient.analytics`. `[backend]`

- [x] **7. Add Chart Interactivity** `[frontend]`
  - [x] 7.1. Implement zoom/pan controls for time-series charts.
  - [x] 7.2. Add legend toggle.
  - [x] 7.3. Add data export button.
  - [x] 7.4. Add full-screen mode.
  - [x] 7.5. Ensure responsive charts.

- [x] **8. Integrate Charts into Dashboard** `[frontend]`
  - [x] 8.1. Update `frontend/src/components/pages/Dashboard.tsx`.
  - [x] 8.2. Create a responsive chart grid layout.
  - [x] 8.3. Add chart loading skeletons.
  - [ ] 8.4. Test with real data. `[test]`

### Phase 3: WebSocket Real-time Updates Implementation

- [x] **1. Enhance `WebSocketClient`** `[frontend]`
  - [x] 1.1. Review `frontend/src/lib/api/websocket.ts`.
  - [x] 1.2. Ensure robust connection lifecycle, auto-reconnect, event subscription, and offline message queue.

- [x] **2. Create `ConnectionStatus` Component** `[frontend]`
  - [x] 2.1. Create `frontend/src/components/ui/ConnectionStatus.tsx`.
  - [x] 2.2. Display a connection status indicator.
  - [x] 2.3. Add a tooltip with the status message.
  - [x] 2.4. Add a manual reconnect button.

- [x] **3. Implement Real-time Job Recommendations** `[frontend]`
  - [x] 3.1. Listen for `job:recommendation` WebSocket events.
  - [x] 3.2. Show toast notifications for new job matches.
  - [ ] 3.3. Update the jobs list in real-time.
  - [ ] 3.4. Add a badge on the Jobs tab.
  - [ ] 3.5. Implement smooth animation for new items.

- [x] **4. Implement Real-time Application Status Updates** `[frontend]`
  - [x] 4.1. Listen for `application:status_change` WebSocket events.
  * [x] 4.2. Update application status in the UI instantly.
  - [x] 4.3. Show toast notification.
  - [ ] 4.4. Update dashboard stats in real-time.
  - [ ] 4.5. Add a badge animation for status changes.

- [x] **5. Implement Real-time Notifications** `[frontend]`
  - [x] 5.1. Listen for `notification:new` WebSocket events.
  - [x] 5.2. Display toast notifications.
  - [ ] 5.3. Update the notification bell badge count.
  - [ ] 5.4. Add new notifications to the notification center list.
  - [ ] 5.5. Implement sound playback based on user preferences.

- [x] **6. Handle Reconnection and Offline Mode** `[frontend]`
  - [x] 6.1. Detect network offline/online events.
  - [x] 6.2. Show a "reconnecting" toast message.
  - [x] 6.3. Ensure `WebSocketService` handles reconnection.
  - [ ] 6.4. Implement data resynchronization on reconnect.
  - [x] 6.5. Ensure `WebSocketService` handles offline message queue.

- [ ] **7. Test WebSocket Functionality** `[test]`
  - [ ] 7.1. Test real-time updates across multiple browser tabs.
  - [ ] 7.2. Test reconnection after network disruption.
  - [ ] 7.3. Test on mobile devices.
  - [ ] 7.4. Test with slow network conditions.

### Phase 4: Drag & Drop Features Implementation

- [ ] **1. Create Draggable Dashboard Widgets** `[frontend]`
  - [ ] 1.1. Update the Dashboard component to use `@dnd-kit`.
  - [ ] 1.2. Make dashboard cards/widgets draggable.
  - [ ] 1.3. Allow reordering of widgets.
  - [ ] 1.4. Save widget layout to user preferences. `[backend]`
  - [ ] 1.5. Add a "Reset layout" button.
  - [ ] 1.6. Implement visual feedback during drag.

- [ ] **2. Create Kanban Board for Applications** `[frontend]`
  - [ ] 2.1. Create `frontend/src/components/pages/ApplicationKanban.tsx`.
  - [ ] 2.2. Create columns: Applied, Interviewing, Offer, Rejected.
  - [ ] 2.3. Make application cards draggable.
  - [ ] 2.4. Update application status on drop. `[backend]`
  - [ ] 2.5. Implement optimistic updates with rollback.
  - [ ] 2.6. Add smooth animations.

- [ ] **3. Add Drag-to-Reorder for Lists** `[frontend]`
  - [ ] 3.1. Implement drag-to-reorder for custom job lists.
  - [ ] 3.2. Implement drag-to-reorder for saved searches.
  - [ ] 3.3. Save the new order to the backend. `[backend]`
  - [ ] 3.4. Add visual feedback.

- [ ] **4. Add Keyboard Support for Drag & Drop** `[frontend]`
  - [ ] 4.1. Implement keyboard navigation for drag & drop.
  - [ ] 4.2. Announce drag/drop actions to screen readers.
  - [ ] 4.3. Add ARIA live regions for status updates.

- [ ] **5. Test Drag & Drop Functionality** `[test]`
  - [ ] 5.1. Test on desktop browsers.
  - [ ] 5.2. Test touch drag on mobile/tablet.
  - [ ] 5.3. Test keyboard navigation.
  - [ ] 5.4. Test with a screen reader.