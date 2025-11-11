# Research Findings for Onboarding Wizard and Data Visualization Charts

This document outlines the research and plan for implementing the Onboarding Wizard and Data Visualization Charts features.

## 1. Onboarding Wizard

The onboarding wizard will be a new feature to guide users through the initial setup of their profile and preferences.

### 1.1. Component Structure

The main component will be `frontend/src/components/onboarding/OnboardingWizard.tsx`. It will manage the state of the wizard, including the current step and the user's progress. The wizard will consist of the following steps:

*   **Welcome & Profile Setup**: `frontend/src/components/onboarding/steps/WelcomeStep.tsx`
*   **Skills & Expertise**: `frontend/src/components/onboarding/steps/SkillsStep.tsx`
*   **Resume Upload**: `frontend/src/components/onboarding/steps/ResumeStep.tsx`
*   **Job Preferences**: `frontend/src/components/onboarding/steps/PreferencesStep.tsx`
*   **Feature Tour**: `frontend/src/components/onboarding/steps/FeatureTourStep.tsx`
*   **Completion**: `frontend/src/components/onboarding/steps/CompletionStep.tsx`

### 1.2. UI Components

The wizard will be built using the existing UI components from `frontend/src/components/ui/` to ensure a consistent look and feel. The following components will be used:

*   `Button`: For Next, Back, and Skip buttons.
*   `ProgressBar`: To show the user's progress through the wizard.
*   `Input`: For text inputs like name, email, and job title.
*   `Select`: For dropdowns like years of experience.
*   `Checkbox`: For multi-select options.
*   `FileUpload`: For resume uploads.
*   `Modal`: To host the wizard.

### 1.3. State Management

The state of the wizard will be managed using a combination of `useState` and `useReducer` hooks. The progress will be saved to the backend after each step using the `apiClient.user.updateProfile()` method.

### 1.4. Skip and Resume Logic

The wizard will allow users to skip individual steps or the entire onboarding process. The progress will be saved to the backend, so users can resume from where they left off.

## 2. Data Visualization Charts

The data visualization charts will provide users with insights into their job applications and the job market.

### 2.1. Charting Library

The project already uses `recharts`, so we will use it to create the new charts.

### 2.2. Chart Components

The following chart components will be created in `frontend/src/components/charts/`:

*   `ApplicationStatusChart.tsx`: A pie or donut chart showing the distribution of application statuses.
*   `ApplicationTimelineChart.tsx`: A line chart showing the number of applications over time.
*   `SalaryDistributionChart.tsx`: A bar chart or histogram showing the distribution of salary ranges.
*   `SkillsDemandChart.tsx`: A bar chart showing the top skills in job postings.
*   `SuccessRateChart.tsx`: A funnel chart showing the conversion rates at each stage of the application process.

Each chart component will be wrapped in a `ChartWrapper.tsx` component that provides consistent styling, loading skeletons, error states, and export/full-screen functionality.

### 2.3. Data Fetching

The data for the charts will be fetched from the backend using the `apiClient.analytics` methods.

## 3. WebSocket Real-time Updates

The application will use WebSockets to provide real-time updates for job recommendations and application status.

### 3.1. WebSocket Client

The `frontend/src/lib/api/websocket.ts` file already contains a `WebSocketService` class that handles the WebSocket connection. We will use this service to subscribe to the relevant channels and receive real-time updates.

### 3.2. Real-time Features

*   **Job Recommendations**: The application will listen for `job:recommendation` events and show a toast notification when a new job matches the user's profile.
*   **Application Status Updates**: The application will listen for `application:status_change` events and update the application status in the UI instantly.
*   **Notifications**: The application will listen for `notification:new` events and display a toast notification and update the notification bell badge.

## 4. Drag & Drop Features

The application will use the `@dnd-kit` library to implement drag and drop features.

### 4.1. Draggable Dashboard Widgets

The dashboard widgets will be made draggable using the `@dnd-kit/sortable` package. The layout of the widgets will be saved to the user's preferences.

### 4.2. Kanban Board for Applications

A Kanban board will be created to manage job applications. The application cards will be draggable between columns, and the status will be updated on drop.