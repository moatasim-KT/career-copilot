# Frontend UX Improvement Plan

This plan details the implementation of the UX improvements outlined in `RESEARCH.md`. The work is divided into three phases to deliver iterative enhancements to the Career Copilot frontend.

## Phase 1: Foundational UI/UX Improvements (High Priority)

### 1.1. Enhance Metric Cards (`src/components/ui/MetricCard.tsx`)

*   **Goal:** Improve the visual hierarchy and information density of dashboard metric cards.
*   **Steps:**
    1.  Modify the `MetricCard` component to accept new props for trend indicators (e.g., `trend: 'up' | 'down' | 'neutral'`).
    2.  Add a visual element (e.g., an arrow icon) to display the trend.
    3.  Incorporate a slot for a mini-chart (placeholder for now).
    4.  Wrap the card in a link or add a clickable element to allow for drill-downs into more detailed views.
    5.  Update the `Dashboard` page (`src/components/pages/Dashboard.tsx`) to pass the new props to the `MetricCard` components.

### 1.2. Redesign Job Cards

*   **Goal:** Make job listings easier to scan and compare.
*   **Steps:**
    1.  Create a new component `src/components/ui/JobCard.tsx` based on the existing `Card.tsx` but specialized for job listings.
    2.  The `JobCard` will prominently display: Company, Title, and a "Match Score" (placeholder value for now).
    3.  Ensure action buttons (e.g., "View", "Apply") are always visible on the card.
    4.  Refactor the `JobsPage` (`src/components/pages/JobsPage.tsx`) to use the new `JobCard` component.

### 1.3. Implement Multiple View Options on Jobs Page

*   **Goal:** Allow users to choose between different layouts for viewing job listings.
*   **Steps:**
    1.  In `src/components/pages/JobsPage.tsx`, introduce a state variable to manage the current view (`'grid'`, `'list'`, `'table'`).
    2.  Create a view-switcher UI (e.g., a button group) to toggle between the view states.
    3.  Create new components for the new views:
        *   `src/components/pages/jobs/JobListView.tsx`
        *   `src/components/pages/jobs/JobTableView.tsx`
    4.  Use conditional rendering in `JobsPage.tsx` to display the appropriate view based on the selected state.

### 1.4. Organize Job Filters

*   **Goal:** Improve the accessibility and usability of job filtering options.
*   **Steps:**
    1.  Create a new `FilterPanel` component in `src/components/pages/jobs/FilterPanel.tsx`.
    2.  This component will be a sticky side panel on the `JobsPage`.
    3.  Organize filter controls into logical categories (e.g., "Job Details", "Location", "Salary").
    4.  Refactor the layout of `JobsPage.tsx` to a two-column layout, with the `FilterPanel` on one side and the job listings on the other.

## Phase 2: Enhancing Actionability and Workflow (Medium Priority)

### 2.1. Create Activity Timeline

*   **Goal:** Provide users with a chronological overview of their recent activities.
*   **Steps:**
    1.  Create an `ActivityTimelineItem.tsx` component in `src/components/ui/`.
    2.  Create an `ActivityTimeline.tsx` component that renders a list of `ActivityTimelineItem`s.
    3.  Add the `ActivityTimeline` to the `Dashboard` page.
    4.  (Backend dependency) Define the API endpoint to fetch activity data.

### 2.2. Add Quick Actions Panel

*   **Goal:** Give users quick access to common tasks from the dashboard.
*   **Steps:**
    1.  Create a `QuickActionCard.tsx` component in `src/components/ui/`.
    2.  Create a `QuickActionsPanel.tsx` component that displays a series of `QuickActionCard`s (e.g., "Add a Job", "Upload Resume").
    3.  Add the `QuickActionsPanel` to the `Dashboard` page.

### 2.3. Implement Saved Filters

*   **Goal:** Allow users to save and reuse common filter combinations on the Jobs page.
*   **Steps:**
    1.  Add a "Save Filters" button to the `FilterPanel`.
    2.  Create a UI for managing saved filters (e.g., a dropdown list).
    3.  Implement logic to store and retrieve filter presets (using local storage for now).

### 2.4. Streamline Job Form with Progressive Disclosure

*   **Goal:** Make the add/edit job form less overwhelming.
*   **Steps:**
    1.  Refactor the existing job form into a multi-step or accordion-style interface.
    2.  Initially, show only the most critical fields (e.g., Job Title, Company, URL).
    3.  Allow users to expand sections to fill in more details.
    4.  Implement real-time validation feedback on fields as the user types.

## Phase 3: Future Enhancements

This phase includes advanced features that will be planned in more detail after the completion of Phases 1 and 2.

*   **Job Comparison Tool**
*   **Advanced Analytics and Visualizations**
*   **Customizable Dashboard**
*   **Fully Optimized Mobile Views**

---

## Phase 3: Data Management & State (High Priority)

### 3.1 State Management

#### 3.1.1 Global State with Zustand
*   **Goal:** Centralize and manage global application state efficiently using Zustand.
*   **Steps:**
    1.  **Install Zustand:** Add Zustand to the project dependencies.
    2.  **Create `userStore`:**
        *   Define a Zustand store for user authentication and profile data (`src/stores/userStore.ts`).
        *   Include state for `user` object (id, name, email, roles), `isAuthenticated`, `isLoading`, and `error`.
        *   Implement actions for `login`, `logout`, `setUser`, and `clearUser`.
    3.  **Create `jobsStore`:**
        *   Define a Zustand store for job listings, including filtering, sorting, and pagination states (`src/stores/jobsStore.ts`).
        *   Include state for `jobs` array, `filters`, `sortBy`, `pagination` (currentPage, totalPages), `isLoading`, and `error`.
        *   Implement actions for `setJobs`, `addJob`, `updateJob`, `deleteJob`, `setFilters`, `setSortBy`, and `setPagination`.
    4.  **Create `applicationsStore`:**
        *   Define a Zustand store for job applications, including their status and related data (`src/stores/applicationsStore.ts`).
        *   Include state for `applications` array, `isLoading`, and `error`.
        *   Implement actions for `setApplications`, `addApplication`, `updateApplication`, and `deleteApplication`.
    5.  **Create `notificationsStore`:**
        *   Define a Zustand store for managing in-app notifications (`src/stores/notificationsStore.ts`).
        *   Include state for `notifications` array (message, type, id), and actions to `addNotification`, `removeNotification`, and `clearNotifications`.
    6.  **Create `uiStore`:**
        *   Define a Zustand store for managing UI-specific states like modal visibility, drawer open/close, etc. (`src/stores/uiStore.ts`).
        *   Include state for `isModalOpen`, `modalContent`, `isDrawerOpen`, etc., and corresponding toggle actions.

#### 3.1.2 Local State Optimization
*   **Goal:** Improve component rendering performance.
*   **Steps:**
    1.  **Audit Component Re-renders:** Use React DevTools profiler to identify components that re-render unnecessarily.
    2.  **Implement `React.memo`:** Apply `React.memo` to functional components that receive the same props frequently and render the same output.
    3.  **Use `useMemo`/`useCallback`:** Optimize expensive calculations and prevent unnecessary re-creation of functions passed as props using `useMemo` and `useCallback`.
    4.  **Create Custom Hooks:** Develop custom hooks for common stateful logic to promote reusability and encapsulate complexity.

#### 3.1.3 Server State Management with React Query
*   **Goal:** Efficiently fetch, cache, and synchronize server data.
*   **Steps:**
    1.  **Install React Query:** Add `@tanstack/react-query` to the project dependencies.
    2.  **Configure `QueryClientProvider`:** Set up `QueryClientProvider` at the root of the application.
    3.  **Implement Data Fetching Hooks:**
        *   Create custom hooks (e.g., `useUser`, `useJobs`, `useApplications`) using `useQuery` for fetching data.
        *   Integrate with the existing API client for data fetching.
    4.  **Implement Mutations:**
        *   Use `useMutation` for creating, updating, and deleting data (e.g., `useAddJob`, `useUpdateApplication`).
        *   Configure `onSuccess` callbacks for cache invalidation and optimistic updates.
    5.  **Optimistic Updates:** Implement optimistic updates for key mutations to provide immediate UI feedback.
    6.  **Cache Invalidation Strategies:** Define and implement strategies for invalidating and refetching queries after mutations or specific events.
    7.  **Infinite Scroll/Pagination:** Implement `useInfiniteQuery` for lists that require infinite scrolling or advanced pagination.

### 3.2 Data Persistence

#### 3.2.1 Client-Side Storage
*   **Goal:** Securely and efficiently persist data on the client-side.
*   **Steps:**
    1.  **Implement `localStorage` Wrapper:**
        *   Create a utility (`src/lib/utils/localStorage.ts`) to wrap `localStorage` operations.
        *   Include basic encryption/decryption for sensitive data (e.g., using a simple XOR cipher or a more robust library if needed, but start simple).
        *   Add error handling for storage limits.
    2.  **Implement `sessionStorage` Wrapper:**
        *   Create a similar utility for `sessionStorage` for temporary data.
    3.  **Offline-First Data Sync (Placeholder):**
        *   For now, create a placeholder function/module (`src/lib/utils/offlineSync.ts`) that outlines the strategy for offline data synchronization (e.g., using a service worker and IndexedDB for queuing requests). Actual implementation will be a future task.
    4.  **Storage Quota Management (Monitoring):**
        *   Add basic logging or monitoring for `localStorage` and `sessionStorage` usage to prevent exceeding quotas.
