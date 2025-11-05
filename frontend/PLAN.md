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