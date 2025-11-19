# Frontend Architecture

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

The frontend of Career Copilot is a Next.js-based application that provides a modern and responsive user interface.

## Tech Stack

- **Framework**: Next.js (App Router)
- **Language**: TypeScript
- **React**: React 19.2+
- **Styling**: Tailwind CSS
- **Component Library**: shadcn/ui (Radix UI)
- **State Management**: React Context API, TanStack Query (React Query)
- **Testing**: Vitest, Playwright, React Testing Library

## App Router Structure

```
src/app/
├── (auth)/              # Auth routes group
│   ├── login/
│   └── register/
├── (dashboard)/         # Dashboard routes group
│   ├── dashboard/
│   ├── jobs/
│   ├── applications/
│   └── profile/
├── layout.tsx           # Root layout
├── page.tsx             # Home page
└── error.tsx            # Error boundary
```

## API Client Architecture

The frontend uses a unified API client to interact with the backend.

```typescript
// lib/api/client.ts - HTTP client
export const apiClient = {
  get: <T>(url: string) => Promise<T>,
  post: <T>(url: string, data: any) => Promise<T>,
  // ...
}

// lib/api/endpoints/ - API endpoints
export const jobsAPI = {
  getJobs: () => apiClient.get('/jobs'),
  getJob: (id: string) => apiClient.get(`/jobs/${id}`),
  // ...
}
```

[[Architecture]]