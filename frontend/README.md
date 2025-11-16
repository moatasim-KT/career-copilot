# Career Copilot - Frontend

Next.js 15 frontend with App Router, TypeScript, Tailwind CSS, and unified API client for AI-powered career management.

## Quick Links

- **📚 Frontend Features Hub**: [[docs/README|Frontend Documentation]] - **Complete frontend documentation**
- **Setup**: [[../LOCAL_SETUP|Local Setup]] - Complete development guide
- **App Entry**: [[src/app/layout.tsx|Root Layout]] - Root layout
- **API Client**: [[src/lib/api/client.ts|API Client]] - Backend communication
- **Component Docs**: [[../docs/components/README|Component Documentation]] - 190+ component documentation
- **Running**: http://localhost:3000 (dev mode)

## Frontend Features Documentation

See **[[docs/README|Frontend Documentation]]** for comprehensive documentation on:

- 🚀 **Performance**: [[src/components/lazy/README|Lazy loading]], [[src/components/ui/loading/README|loading states]], code splitting
- 🎨 **UI Components**: [[src/components/ui/DataTable/README|DataTable]], Card2 enhancements, dark mode
- 📊 **Domain Features**: [[src/components/jobs/README|Jobs]], [[src/components/applications/README|Applications]]
- 🛠️ **Developer Tools**: [[src/lib/SENTRY_INTEGRATION_GUIDE|Sentry]], [[src/components/help/CONTEXTUAL_HELP_INTEGRATION_GUIDE|contextual help]]
- 🧪 **Testing**: [[src/components/ui/__tests__/README|UI tests]], [[src/components/ui/__tests__/DARK_MODE_TEST_REPORT|dark mode tests]], accessibility

## Architecture

**App Router Pages** ([[src/app/|App Directory]]):

- [[src/app/dashboard/|Dashboard]] - Main dashboard
- [[src/app/jobs/|Jobs]] - Job search and listings
- [[src/app/applications/|Applications]] - Application tracking
- [[src/app/knowledge-base/|Knowledge Base]] - Career resources
- [[src/app/profile/|Profile]] - User profile

### Component Organization

**UI Components** ([[src/components/ui/|UI Directory]]):
- shadcn/ui primitives (Button, Card, Dialog, etc.)
- Located in [[src/components/ui/|UI Directory]]
- Styled with Tailwind CSS

**Feature Components**:
- [[src/components/pages/|Pages]] - Page-level components
- [[src/components/forms/|Forms]] - Form components
- [[src/components/layout/|Layout]] - Layout components (Navbar, Sidebar)
- [[src/components/charts/|Charts]] - Data visualization

**Key Components**:
- [[src/components/layout/navbar.tsx|Navbar]] - Main navigation
- [[src/components/layout/sidebar.tsx|Sidebar]] - Sidebar navigation
- [[src/components/pages/DashboardPage.tsx|Dashboard Page]] - Dashboard view

### API Integration

**Unified API Client**: [[src/lib/api/client.ts|API Client]]

All backend communication through `fetchApi`:

```typescript
import { fetchApi } from '@/lib/api/client';

// Type-safe API calls
const response = await fetchApi<Job[]>('/jobs/matches', {
  params: { limit: 10 },
  requiresAuth: false  // Auth disabled by default
});

if (response.error) {
  console.error(response.error);
  return;
}
const jobs = response.data;
```

**API Endpoints** (see [[src/lib/api/|API Directory]]):
- [[src/lib/api/jobs.ts|Jobs API]] - Job API
- [[src/lib/api/applications.ts|Applications API]] - Application API
- [[src/lib/api/notifications.ts|Notifications API]] - Notification API

### State Management

**Context Providers** ([[src/contexts/]]):
- [[src/contexts/AuthContext.tsx]] - Authentication state
- [[src/contexts/ThemeContext.tsx]] - Theme management

**Zustand Stores** ([[src/stores/]]):
- Complex state management (if applicable)

**React Hooks** ([[src/hooks/]]):
- [[src/hooks/use-auth.ts]] - Authentication hook

- [[src/hooks/use-theme.ts]] - Theme hook├── 📂 Logs & Data

- Custom hooks for data fetching│   └── logs/                 # Application logs

│

### TypeScript Types└── 📂 Hidden/Archive

    └── .archive/             # Old configs, backups

**Type Definitions** ([[src/types/]]):        └── eslint.config.mjs.backup

- [[src/types/api.ts]] - API response types```

- [[src/types/job.ts]] - Job types

- [[src/types/application.ts]] - Application types## 🚀 Quick Start

- [[src/types/user.ts]] - User types

### Prerequisites

## Configuration

- Node.js 18+ (LTS recommended)

### Environment Variables- npm 9+ or pnpm 8+



Template: [[.env.example]] → Copy to `.env.local`### Installation



```bash```bash

# Backend API# Navigate to frontend

NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1cd frontend/



# Sentry (production monitoring)# Install dependencies

NEXT_PUBLIC_SENTRY_DSN=...npm install

SENTRY_AUTH_TOKEN=...# or

SENTRY_ORG=...pnpm install

SENTRY_PROJECT=...

```# Set up environment

cp .env.example .env.local

```

See [[.env.example]] for complete list and [[../LOCAL_SETUP.md#frontend-setup]].

### Config Files

- **Next.js**: [[next.config.js]]
- **TypeScript**: [[tsconfig.json]]
- **Tailwind**: [[tailwind.config.ts]]
- **ESLint**: [[eslint.config.mjs]]
- **Prettier**: [[.tools/.prettierrc.json]]
- **PostCSS**: [[postcss.config.mjs]]

## Development

### Running Locally

**Via Docker** (recommended):
```bash
docker-compose up -d frontend
```

**Manual**:
```bash
npm install
npm run dev  # http://localhost:3000
```

See [[../LOCAL_SETUP.md#frontend-setup]] for complete setup guide.

### Testing

**Unit Tests** (Jest):
```bash
npm test                    # All tests
npm run test:watch          # Watch mode
npm run test:coverage       # With coverage
npm run test:a11y           # Accessibility regression tests (jest-axe)
```

**E2E Tests** (Playwright):
```bash
npm run test:e2e            # E2E tests
npm run test:e2e:ui         # Interactive mode
```

**Test Files**:
- [[src/__tests__/]] - Component tests
- [[src/lib/api/__tests__/]] - API client tests# Edit .env.local with your configuration



### Config Files# Run development server

npm run dev

- **Next.js**: [[next.config.js]]# or

- **TypeScript**: [[tsconfig.json]]pnpm dev

- **Tailwind**: [[tailwind.config.ts]]```

- **ESLint**: [[eslint.config.mjs]]

- **Prettier**: [[.tools/.prettierrc.json]]### Access the Application

- **PostCSS**: [[postcss.config.mjs]]

- **Development**: http://localhost:3000

## Development- **API Docs**: http://localhost:3000/api-doc (if available)



### Running Locally## 📂 Directory Purpose Guide



**Via Docker** (recommended):### Application Code (`src/`)

```bash

docker-compose up -d frontend| Directory | Purpose | Examples |

```|-----------|---------|----------|

| `app/` | Next.js App Router pages | Routes, layouts, page components |

**Manual**:| `components/ui/` | UI components (shadcn/ui) | Button, Input, Card, Dialog |

```bash| `components/forms/` | Form components | FormWizard, validation wrappers |

npm install| `components/pages/` | Page-level components | Dashboard, JobsPage, ProfilePage |

npm run dev  # http://localhost:3000| `components/layout/` | Layout components | Header, Footer, Sidebar, Navigation |

```| `components/charts/` | Data visualization | Charts, graphs, analytics widgets |

| `lib/api/` | API client | HTTP client, API endpoints |

See [[../LOCAL_SETUP.md#frontend-setup]] for complete setup guide.| `lib/utils/` | Utility functions | Formatters, validators, helpers |

| `lib/hooks/` | Custom React hooks | Data fetching, state management |

### Testing| `hooks/` | Additional hooks | useWebSocket, useAuth, useUser |

| `contexts/` | React Context | AuthContext, ThemeContext |

**Unit Tests** (Jest):| `types/` | TypeScript types | Type definitions, interfaces |

```bash| `styles/` | Global styles | CSS, Tailwind utilities |

npm test                    # All tests| `config/` | Configuration | App settings, constants |

npm run test:watch          # Watch mode

npm run test:coverage       # With coverage### Static Assets (`public/`)

```

| Directory | Purpose | Usage |

**E2E Tests** (Playwright):|-----------|---------|-------|

```bash| `images/` | Image assets | Logos, backgrounds, illustrations |

npm run test:e2e            # E2E tests| `icons/` | Icon files | SVG icons, favicons |

npm run test:e2e:ui         # Interactive mode| `fonts/` | Font files | Custom fonts |

```

### Testing

**Test Files**:

- [[src/__tests__/]] - Component tests| Directory | Purpose | Framework |

- [[src/lib/api/__tests__/]] - API client tests|-----------|---------|-----------|

| `tests/e2e/` | End-to-end tests | Playwright |

### Code Quality| `tests/integration/` | Integration tests | Vitest/Jest |

| `cypress/` | E2E tests (legacy) | Cypress |

Via [[../Makefile]]:| `coverage/` | Coverage reports | Jest/Vitest |

```bash| `*.test.ts(x)` | Unit tests (co-located) | Vitest/Jest |

make lint-frontend          # ESLint

make format-frontend        # Prettier### Configuration (`.tools/`)

make type-check-frontend    # TypeScript

```| File | Purpose | Notes |

|------|---------|-------|

## Key Patterns| `.prettierrc.json` | Code formatting | Prettier configuration |

| `.prettierignore` | Prettier ignore patterns | Files to skip formatting |

### App Router Pattern| `jest.config.js` | Unit testing | Jest configuration |

| `jest.setup.js` | Test setup | Global test utilities |

Uses Next.js 15 App Router (not Pages Router):| `vitest.config.ts` | Unit testing (modern) | Vitest configuration |

| `playwright.config.ts` | E2E testing | Playwright configuration |

```tsx| `commitlint.config.js` | Commit linting | Conventional commits |

// src/app/dashboard/page.tsx

export default async function DashboardPage() {## 🔧 Common Tasks

  // Server components by default

  // Use 'use client' for interactivity### Development

  return <DashboardLayout />

}```bash

```# Start development server

npm run dev

### API Client Pattern

# Build for production

Always use unified API client:npm run build



```typescript# Start production server

// ✅ CORRECTnpm start

import { fetchApi } from '@/lib/api/client';

const response = await fetchApi<T>('/endpoint');# Type check

npm run type-check

// ❌ WRONG - Don't use raw fetch

const response = await fetch('http://localhost:8000/api/v1/endpoint');# Lint code

```npm run lint



### Component Pattern# Fix linting issues

npm run lint:fix

```tsx

// src/components/pages/ExamplePage.tsx# Format code

'use client';  // If needs interactivitynpm run format



import { Button } from '@/components/ui/button';# Format check

npm run format:check

export function ExamplePage() {```

  return (

    <div className="container mx-auto">### Testing

      <Button>Click me</Button>

    </div>```bash

  );# Run all tests

}npm test

```

# Run unit tests

## Project Structurenpm run test:unit



```# Run tests in watch mode

frontend/npm run test:watch

├── src/

│   ├── app/              # Next.js App Router (pages)# Run E2E tests (Playwright)

│   │   ├── layout.tsx   # Root layoutnpm run test:e2e

│   │   ├── page.tsx     # Landing page

│   │   ├── dashboard/   # Dashboard pages# Run E2E tests (Cypress)

│   │   ├── jobs/        # Job pagesnpm run cypress:open

│   │   └── ...

│   ├── components/       # React components# Generate coverage report

│   │   ├── ui/          # shadcn/ui primitivesnpm run test:coverage

│   │   ├── pages/       # Page-level components```

│   │   ├── forms/       # Form components

│   │   └── layout/      # Layout components### Bundle Analysis

│   ├── lib/             # Utilities

│   │   ├── api/         # API client (PRIMARY)```bash

│   │   └── utils/       # Helper functions# Analyze bundle size

│   ├── hooks/           # Custom React hooksnpm run analyze

│   ├── context/         # React Context providers# or

│   ├── stores/          # State management (Zustand)npx ts-node bin/analyze-bundle.ts

│   ├── types/           # TypeScript types

│   └── styles/          # Global styles# Optimize bundle

├── public/              # Static assetsnpx ts-node bin/optimize-bundle.ts

├── .tools/              # Tool configurations```

├── .env.example         # Environment template

├── next.config.js       # Next.js config### Code Quality

└── package.json         # Dependencies

``````bash

# Type check

## Stylingnpm run type-check



**Tailwind CSS**: Utility-first CSS framework# Lint

npm run lint

```tsx

<div className="flex items-center justify-between p-4 bg-white rounded-lg shadow"># Format

  {/* Tailwind classes */}npm run format

</div>

```# Run all checks

npm run lint && npm run type-check && npm run format:check

**Global Styles**: [[src/styles/globals.css]]```



**Component Styles**: Use Tailwind classes, not CSS modules### Storybook (Component Development)



## Troubleshooting```bash

# Start Storybook

See [[../LOCAL_SETUP.md#troubleshooting]] for detailed troubleshooting.npm run storybook



**Quick checks**:# Build Storybook

```bashnpm run build-storybook

# Clear cache```

rm -rf .next node_modules package-lock.json

npm install## 🔐 Environment Variables



# Check API connectionSee `.env.example` and `.env.local.example` for all available environment variables.

curl http://localhost:8000/health

### Required Variables

# View logs

docker-compose logs -f frontend```bash

```# API Configuration

NEXT_PUBLIC_API_URL=http://localhost:8000

## Additional ResourcesNEXT_PUBLIC_API_VERSION=v1



- **Project Status**: [[../PROJECT_STATUS.md]]# WebSocket

- **Setup Guide**: [[../LOCAL_SETUP.md]]NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

- **Backend API**: [[../backend/README.md]]```

- **Next.js Docs**: https://nextjs.org/docs

- **shadcn/ui**: https://ui.shadcn.com/### Optional Variables


```bash
# Analytics
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# Sentry
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_AI_FEATURES=true
```

## 📊 Tech Stack

### Core Framework

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript 5.0+
- **React**: React 19.2+
- **Styling**: Tailwind CSS 3.4+

### UI Components

- **Component Library**: shadcn/ui (Radix UI)
- **Icons**: Lucide React
- **Charts**: Recharts, Chart.js
- **Forms**: React Hook Form + Zod validation

### State Management

- **Global State**: React Context API
- **Server State**: TanStack Query (React Query)
- **Forms**: React Hook Form

### Testing

- **Unit Tests**: Vitest (modern) / Jest (legacy)
- **E2E Tests**: Playwright (modern) / Cypress (legacy)
- **Component Tests**: React Testing Library
- **Coverage**: c8 (Vitest) / Istanbul (Jest)

### Development Tools

- **Linting**: ESLint 9+
- **Formatting**: Prettier 3+
- **Type Checking**: TypeScript
- **Git Hooks**: Husky + lint-staged
- **Commit Linting**: Commitlint (Conventional Commits)

### Build & Deployment

- **Bundler**: Next.js (Webpack/Turbopack)
- **Compiler**: SWC
- **Package Manager**: npm / pnpm
- **Deployment**: Vercel / Docker

## 🏗️ Application Architecture

### App Router Structure

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

### Component Organization

```
src/components/
├── ui/                  # Base UI components (shadcn/ui)
│   ├── button.tsx
│   ├── input.tsx
│   ├── card.tsx
│   └── ...
├── forms/               # Form components
│   ├── FormWizard.tsx
│   └── ...
├── pages/               # Page-level components
│   ├── Dashboard.tsx
│   ├── JobsPage.tsx
│   └── ...
└── layout/              # Layout components
    ├── Header.tsx
    ├── Footer.tsx
    └── ...
```

### API Client Architecture

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

## 🧪 Testing Strategy

### Unit Tests (Vitest/Jest)

Located alongside the code they test (`*.test.ts(x)`).

```typescript
// src/components/ui/Button.test.tsx
import { render, screen } from '@testing-library/react'
import { Button } from './Button'

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })
})
```

### Integration Tests

Located in `tests/integration/`.

```typescript
// tests/integration/auth.test.ts
describe('Authentication Flow', () => {
  it('logs in user successfully', async () => {
    // Test complete auth flow
  })
})
```

### E2E Tests (Playwright)

Located in `tests/e2e/`.

```typescript
// tests/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test'

test('dashboard loads correctly', async ({ page }) => {
  await page.goto('/dashboard')
  await expect(page.locator('h1')).toContainText('Dashboard')
})
```

## 🎨 Code Style

### Component Structure

```typescript
// Recommended component structure
import React from 'react'
import { cn } from '@/lib/utils'

interface ComponentProps {
  // Props interface
}

export function Component({ prop1, prop2 }: ComponentProps) {
  // Hooks
  const [state, setState] = React.useState()
  
  // Event handlers
  const handleClick = () => {}
  
  // Effects
  React.useEffect(() => {}, [])
  
  // Render
  return <div>Component</div>
}
```

### Naming Conventions

- **Components**: PascalCase (`Button.tsx`, `JobCard.tsx`)
- **Hooks**: camelCase with "use" prefix (`useAuth.ts`, `useJobs.ts`)
- **Utilities**: camelCase (`formatDate.ts`, `validateEmail.ts`)
- **Types**: PascalCase (`User`, `JobListing`)
- **Constants**: UPPER_SNAKE_CASE (`API_URL`, `MAX_RETRIES`)

### Import Order

```typescript
// 1. React & Next.js
import React from 'react'
import { useRouter } from 'next/navigation'

// 2. External libraries
import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'

// 3. Internal components
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

// 4. Hooks & utilities
import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/lib/utils'

// 5. Types
import type { User } from '@/types'

// 6. Styles (if any)
import styles from './Component.module.css'
```

## 📝 Adding New Features

### 1. Create Component

```bash
# Create new component
mkdir -p src/components/features/MyFeature
touch src/components/features/MyFeature/MyFeature.tsx
touch src/components/features/MyFeature/MyFeature.test.tsx
```

### 2. Add Types

```typescript
// src/types/myFeature.ts
export interface MyFeature {
  id: string
  name: string
}
```

### 3. Create API Client

```typescript
// src/lib/api/endpoints/myFeature.ts
export const myFeatureAPI = {
  getFeatures: () => apiClient.get<MyFeature[]>('/features'),
  getFeature: (id: string) => apiClient.get<MyFeature>(`/features/${id}`),
}
```

### 4. Create Hook

```typescript
// src/hooks/useMyFeature.ts
export function useMyFeature() {
  return useQuery({
    queryKey: ['myFeature'],
    queryFn: () => myFeatureAPI.getFeatures(),
  })
}
```

### 5. Create Page

```typescript
// src/app/my-feature/page.tsx
import { MyFeature } from '@/components/features/MyFeature'

export default function MyFeaturePage() {
  return <MyFeature />
}
```

### 6. Add Tests

```typescript
// Component test
import { render, screen } from '@testing-library/react'
import { MyFeature } from './MyFeature'

describe('MyFeature', () => {
  it('renders correctly', () => {
    render(<MyFeature />)
    expect(screen.getByRole('heading')).toBeInTheDocument()
  })
})
```

## 🐛 Debugging

### Enable Debug Mode

```bash
# Set in .env.local
NODE_ENV=development
NEXT_PUBLIC_DEBUG=true
```

### React DevTools

Install [React Developer Tools](https://react.dev/learn/react-developer-tools) browser extension.

### Network Debugging

Use browser DevTools Network tab or:

```typescript
// Enable API logging
// lib/api/client.ts
const DEBUG = process.env.NEXT_PUBLIC_DEBUG === 'true'

if (DEBUG) {
  console.log('API Request:', url, data)
}
```

### Component Debugging

```typescript
// Use React DevTools or:
console.log('Component Props:', props)
console.log('Component State:', state)
```

## 🔗 Related Documentation

- [Main README](../README.md) - Project overview
- [Backend README](../backend/README.md) - Backend documentation
- [Installation Guide](../docs/setup/INSTALLATION.md) - Full setup guide
- [API Documentation](../docs/api/API.md) - API reference
- [Contributing Guide](./CONTRIBUTING.md) - How to contribute

## 📦 Project Scripts

| Script | Description | Usage |
|--------|-------------|-------|
| `dev` | Start development server | `npm run dev` |
| `build` | Build for production | `npm run build` |
| `start` | Start production server | `npm start` |
| `lint` | Lint code | `npm run lint` |
| `lint:fix` | Fix linting issues | `npm run lint:fix` |
| `format` | Format code with Prettier | `npm run format` |
| `format:check` | Check formatting | `npm run format:check` |
| `type-check` | TypeScript type checking | `npm run type-check` |
| `test` | Run all tests | `npm test` |
| `test:unit` | Run unit tests | `npm run test:unit` |
| `test:watch` | Run tests in watch mode | `npm run test:watch` |
| `test:e2e` | Run E2E tests | `npm run test:e2e` |
| `test:coverage` | Generate coverage report | `npm run test:coverage` |
| `storybook` | Start Storybook | `npm run storybook` |
| `build-storybook` | Build Storybook | `npm run build-storybook` |
| `analyze` | Analyze bundle size | `npm run analyze` |

## 📞 Support

- **Documentation**: Start with this README and `CONTRIBUTING.md`
- **Issues**: [GitHub Issues](https://github.com/moatasim-KT/career-copilot/issues)
- **Email**: <moatasimfarooque@gmail.com>

---

**Last Updated**: November 7, 2025  
**Version**: 1.0.0  
**Framework**: Next.js 14+ (App Router)
