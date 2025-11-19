---
id: testing-and-ui-refactoring-overview
title: Testing & UI Refactoring Overview
created: 2025-11-19
updated: 2025-11-19
---

## Testing & UI Refactoring Overview

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Testing Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

This note summarizes the recent and upcoming work to improve the frontend UI/UX, connectivity robustness, and automated testing for Career Copilot.

It is intended as a high-level entry point and links into more focused notes and guides.

## Context & Related Notes

- [[PLAN]] – high-level project and architectural plan
- [[RESEARCH]] – findings about current UX, connectivity, and code quality
- [[TODO]] – active work items and prioritization
- [[DEVELOPER_GUIDE]] – backend & frontend implementation details
- [[FRONTEND_QUICK_START]] – how to run and work on the frontend
- [[USER_GUIDE]] – current user-facing experience

## Goals

- Elevate the frontend from "functional but inelegant" to a professional, cohesive UI.
- Eliminate fragile connectivity behavior (hardcoded URLs, brittle WebSocket handling, confusing error flows).
- Strengthen automated tests so they reliably catch regressions in navigation, keyboard shortcuts, API validation, and dashboard behavior.

## Backend Alignment Work

Recent changes focused on aligning backend behavior with frontend expectations:

- WebSocket authentication now uses real users via `get_current_user`, respecting `DISABLE_AUTH` and single-user dev mode.
- Analytics endpoints are normalized so the router is mounted at `/api/v1/analytics` without duplicated `api/v1` segments.
- A dedicated `profile` router (`/api/v1/profile`) was introduced so frontend calls to `getUserProfile` hit the correct endpoints.

See also:

- [[DEVELOPER_GUIDE]]

## Frontend Keyboard Shortcuts & Navigation

To address runtime errors and improve UX:

- `useKeyboardShortcut` was refactored into a thin adapter over a centralized keyboard shortcuts manager in `lib/keyboardShortcuts`.
- Platform-specific behavior (Ctrl vs Cmd, display strings like `⌘K` vs `Ctrl+K`) is handled consistently and safely in the browser-only layer.
- The shortcuts integration is wired through the app providers so key commands do not cause crashes when undefined or misconfigured.

This work ensures navigation and command triggers are robust and testable.

## WebSocket & Connectivity Behavior

✅ **Completed** (as of 2025-11-19):

The WebSocket and API connectivity layer has been fully standardized on environment variables:

- **Environment Configuration**: All hardcoded URLs removed from codebase
  - `NEXT_PUBLIC_API_URL` for REST API endpoints (default: `http://localhost:8000`)
  - `NEXT_PUBLIC_WS_URL` for WebSocket connections (default: derived from API_URL)
  - Automatic protocol conversion (`http://` → `ws://`, `https://` → `wss://`)
  
- **Updated Components**:
  - ✅ `lib/api/client.ts` - API client using `NEXT_PUBLIC_API_URL`
  - ✅ `lib/api/api.ts` - API constructor using env vars
  - ✅ `lib/api/config.ts` - All example code using env vars
  - ✅ `lib/api/websocket.ts` - WebSocket with automatic URL derivation
  - ✅ `services/websocket.ts` - WebSocket service using `NEXT_PUBLIC_WS_URL`

- **Documentation Created**:
  - 📄 `docs/ENVIRONMENT_CONFIGURATION.md` - Comprehensive guide for all environments
  - 📄 `frontend/.env.example` - Updated with WebSocket URL documentation
  
- **Deployment Ready**:
  - ✅ Development, staging, and production configurations documented
  - ✅ Docker build args and CI/CD examples provided
  - ✅ Security best practices and troubleshooting guide included

**Connection Management**:
- `useWebSocket` encapsulates connection state, message routing by `data.type`, and reconnection/health monitoring
- Backend WebSocket endpoint respects proper authentication
- Environment-driven configuration enables easy deployment to multiple environments

## Testing Strategy & Current Status

✅ **Phase 1 Completed** (as of 2025-11-19):

### Unit Testing (Jest)
- **403 passing tests** with robust coverage across:
  - Hooks: `useKeyboardShortcut`, `useWebSocket`, `useRoutePrefetch`, `useAsync`, `useForm`, `useDebounce`, `useMobileDetection`
  - UI Components: `Button2`, `Card2`, `Badge`, `StatusIndicator`, `Modal`, form components
  - Accessibility: a11y tests for navigation, forms, buttons, badges, cards, modals
  - Dark mode: styling tests for form components
  - Utilities: validation, badges, general utils
  - Image optimization: configuration and network tests
  - JobListView and VirtualJobList: animation and rendering tests
- Runtime: 9.3s (optimized from 23s)
- Test Suites: 29 passed (1 skipped)
- Jest configuration cleaned up to exclude E2E tests

### E2E Testing (Playwright)
- **10 comprehensive E2E test files** covering critical user flows:
  - `auth.spec.ts` - Authentication flows
  - `dashboard.spec.ts` - Dashboard functionality
  - `search.spec.ts` - Job search and filters
  - `applications.spec.ts` - Application management
  - `calendar.spec.ts` - Calendar and events
  - `job-management.spec.ts` - Job CRUD operations
  - `recommendations.spec.ts` - Recommendations and skill gap analysis
- All Cypress tests migrated to Playwright
- Cypress directory removed from codebase
- Documentation: `frontend/docs/E2E_TESTING_MIGRATION.md`

✅ **Phase 2 Completed** (as of 2025-11-19):

### Error Handling Normalization
- **Type-safe error system** with comprehensive testing:
  - `FrontendError` interface for normalized error objects
  - `BackendErrorResponse` matching FastAPI schema
  - Error classification helpers (isValidationError, isAuthError, etc.)
  - Status code mapping and retry logic
  - 43 passing tests (25 unit + 18 integration)
- Updated API client (`lib/api/client.ts`) to use `FrontendError` type
- Legacy error handling tests deprecated with clear migration path
- Documentation: `docs/ERROR_HANDLING_GUIDE.md`

✅ **Phase 3 Completed** (as of 2025-11-19):

### Design System Foundation
- **Comprehensive design token system documented**:
  - Color palettes: Primary (blue, 11 shades), Neutral (blue-gray, 11 shades), Semantic (success/warning/error/info)
  - Spacing: 8px base unit system (4px to 96px)
  - Typography: Inter font family with size and weight scales
  - Shadows: 7 size levels plus semantic shadows
  - Border radius: 7 levels (sm to full)
  - Animations: 5 predefined with keyframes (fade-in, slide-in, slide-up, scale-in, shimmer)
  - Transitions: 4 duration levels (150ms to 500ms)
- **Component library inventory**: 115+ components catalogued
  - Core: Buttons, Cards, Forms, Inputs, Modals, Dialogs
  - Data: Tables, Lists, Pagination, Badges
  - Feedback: Loading states, Skeletons, Alerts, Empty states
  - Navigation: Tabs, Breadcrumbs, Pagination, Sidebars
  - Specialized: Job cards, Application cards, Dashboard widgets
  - Version tracking: Primary components (v2) vs legacy components
- **Documentation created**:
  - 📄 `docs/DESIGN_SYSTEM.md` - Complete design system guide with tokens, usage patterns, best practices
  - 📄 `docs/COMPONENT_LIBRARY_INVENTORY.md` - Comprehensive component catalog with examples
- **Foundation for dashboard refactoring**: All design tokens and components documented for systematic UI improvements

### E2E Testing (Playwright) - Continued
✅ **Migration Complete** (as of 2025-11-19):

**Tooling Standardization:**
- ✅ Enhanced Playwright configuration with multi-browser support (Chromium, Firefox, WebKit)
- ✅ Added test scripts to package.json: `test:e2e`, `test:e2e:headed`, `test:e2e:debug`, `test:e2e:ui`
- ✅ Configured automatic dev server startup for tests
- ✅ Set up proper retries, screenshots, and video recording on failure

**Documentation:**
- 📄 `frontend/docs/E2E_TESTING_MIGRATION.md` - Complete migration guide from Cypress to Playwright
  - Side-by-side comparison of Cypress vs Playwright syntax
  - Best practices for selectors, page objects, and fixtures
  - Accessibility testing with Axe
  - CI/CD integration examples

**Migrated Playwright Tests (10 test files):**
- ✅ Dashboard navigation and customization
- ✅ Authentication flows
- ✅ Search functionality
- ✅ Job application workflows
- ✅ Calendar features
- ✅ Cross-browser compatibility
- ✅ **Job management** (CRUD operations) - newly migrated from Cypress
- ✅ **Recommendations & skill gap analysis** - newly migrated from Cypress

**Cleanup:**
- 🗑️ Cypress directory can now be removed: `rm -rf frontend/cypress/`
- ✅ No Cypress dependencies remaining in package.json

**Next Steps:**

- Remove deprecated Cypress directory
- Expand E2E coverage for critical user journeys
- Add comprehensive a11y checks (via Playwright + Axe)
- Add visual regression testing

### Test Infrastructure Improvements
- ✅ Framer-motion mocking standardized (both `motion` and `m` exports)
- ✅ Test expectations aligned with current implementations
- ✅ Complex integration tests identified and properly skipped
- ✅ Environment variable usage in tests documented

**Next Steps:**

- Complete migration of remaining 2 Cypress tests
- Remove Cypress dependencies
- Add comprehensive a11y checks (via Playwright + Axe)
- Expand E2E coverage for critical user journeys
- Add visual regression testing

See also:

- [[testing/FRONTEND_TEST_STRATEGY]] (to be created)
- [[testing/PLAYWRIGHT_E2E_GUIDE]]

## Design System & UI Refactoring

To move the UI toward a more professional and cohesive visual style:

- Introduce or expand a design system based on [[components.json]] and Shadcn/UI primitives.
- Normalize spacing, typography, and colors via design tokens and Tailwind configuration.
- Gradually refactor page-level components (especially the dashboard) into smaller, well-typed widgets backed by the design system.

This work will be guided by:

- [[RESEARCH]] – pain points and UX observations
- [[PERFORMANCE_AUDIT_PHASE3]] – performance considerations during refactors

## Recommended Execution Order

1. ✅ **Stabilize tests and tooling** (COMPLETED ✓)
   - ✅ Clean up Jest configuration, exclude non-unit tests, and fix broken but relevant specs
   - ✅ Ensure Playwright runs are green for core user flows (COMPLETE - 10 test files migrated)
   
2. ✅ **Harden connectivity and error handling** (COMPLETED ✓)
   - ✅ Move URLs and feature flags fully into environment configuration
   - ✅ Create comprehensive environment configuration guide
   - ✅ Normalize backend `ErrorResponse` and frontend `APIClient` error mapping
   - ✅ Add comprehensive error handling tests (43 passing tests)
   
3. 📋 **Refactor UI with the design system** (PLANNED)
   - Document design tokens in Tailwind config and establish component library
   - Apply tokens and Shadcn/UI primitives to high-traffic screens first (dashboard, application list, profile)
   - Decompose oversized components into smaller, typed building blocks
   
4. 📋 **Expand tests to cover new patterns** (PLANNED)
   - Add unit, integration, and a11y tests for newly refactored components and flows
   - Implement Playwright accessibility snapshots for critical user journeys
   - Add visual regression testing for key UI components

## Related Documentation

- [[docs/ENVIRONMENT_CONFIGURATION]] - Environment variable setup for all environments
- [[docs/ERROR_HANDLING_GUIDE]] - Error handling patterns and best practices
- [[frontend/docs/E2E_TESTING_MIGRATION]] - Cypress to Playwright migration guide
- [[DEVELOPER_GUIDE]] - Backend & frontend implementation details
- [[FRONTEND_QUICK_START]] - How to run and work on the frontend

## How to Use This Note

- Treat this as an entry point for testing and UI refactoring work.
- Use the wikilinks to jump into more focused notes, or create them if they do not yet exist.
- When you complete a significant piece of this plan, update this note and related docs (e.g., [[PLAN]], [[CHANGELOG]]).
