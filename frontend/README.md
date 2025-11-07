# Career Copilot - Frontend

Next.js-based frontend application for the Career Copilot AI-powered career management platform.

## 📁 Directory Structure

```
frontend/
├── 📄 Core Files
│   ├── package.json           # Dependencies & scripts
│   ├── package-lock.json      # Locked dependencies
│   ├── tsconfig.json          # TypeScript configuration
│   ├── next.config.js         # Next.js configuration
│   ├── .env.example           # Environment variables template
│   ├── .gitignore             # Git ignore patterns
│   └── CONTRIBUTING.md        # Contribution guidelines
│
├── 🔧 Configuration
│   ├── .tools/                # Tool configurations
│   │   ├── .prettierignore   # Prettier ignore patterns
│   │   ├── .prettierrc.json  # Prettier config
│   │   ├── jest.config.js    # Jest testing config
│   │   ├── jest.setup.js     # Jest setup file
│   │   ├── vitest.config.ts  # Vitest config
│   │   ├── vitest.shims.d.ts # Vitest type shims
│   │   ├── playwright.config.ts # Playwright E2E config
│   │   └── commitlint.config.js # Commit linting config
│   │
│   ├── eslint.config.mjs      # ESLint configuration
│   ├── postcss.config.mjs     # PostCSS configuration
│   ├── tailwind.config.ts     # Tailwind CSS config
│   └── next-env.d.ts          # Next.js type definitions
│
├── 📂 Application Code
│   └── src/                   # Source code
│       ├── app/               # Next.js App Router pages
│       ├── components/        # React components
│       │   ├── ui/           # UI components (shadcn/ui)
│       │   ├── forms/        # Form components
│       │   ├── pages/        # Page-level components
│       │   ├── layout/       # Layout components
│       │   └── charts/       # Chart components
│       ├── lib/              # Utilities & helpers
│       │   ├── api/          # API client
│       │   ├── utils/        # Utility functions
│       │   └── hooks/        # Custom React hooks
│       ├── hooks/            # Additional hooks
│       ├── contexts/         # React Context providers
│       ├── types/            # TypeScript types
│       ├── styles/           # Global styles
│       └── config/           # App configuration
│
├── 📂 Static Assets
│   └── public/               # Static files
│       ├── images/           # Images
│       ├── icons/            # Icon files
│       └── fonts/            # Font files
│
├── 📂 Executable Scripts
│   └── bin/                  # Utility scripts
│       ├── analyze-bundle.ts      # Bundle analysis
│       ├── optimize-bundle.ts     # Bundle optimization
│       └── migrate-to-api-client.js # Migration script
│
├── 📂 Testing
│   ├── tests/                # Integration & E2E tests
│   │   ├── e2e/             # End-to-end tests
│   │   └── integration/     # Integration tests
│   ├── cypress/              # Cypress tests
│   └── coverage/             # Test coverage reports
│
├── 📂 Documentation
│   ├── docs/                 # Frontend-specific docs
│   ├── .storybook/           # Storybook configuration
│   └── TODO.md               # Todo list
│
├── 📂 Build & Development
│   ├── .next/                # Next.js build output
│   ├── node_modules/         # Dependencies
│   ├── .husky/               # Git hooks
│   ├── .swc/                 # SWC compiler cache
│   └── tsconfig.tsbuildinfo  # TypeScript build info
│
├── 📂 Logs & Data
│   └── logs/                 # Application logs
│
└── 📂 Hidden/Archive
    └── .archive/             # Old configs, backups
        └── eslint.config.mjs.backup
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm 9+ or pnpm 8+

### Installation

```bash
# Navigate to frontend
cd frontend/

# Install dependencies
npm install
# or
pnpm install

# Set up environment
cp .env.example .env.local
# Edit .env.local with your configuration

# Run development server
npm run dev
# or
pnpm dev
```

### Access the Application

- **Development**: http://localhost:3000
- **API Docs**: http://localhost:3000/api-doc (if available)

## 📂 Directory Purpose Guide

### Application Code (`src/`)

| Directory | Purpose | Examples |
|-----------|---------|----------|
| `app/` | Next.js App Router pages | Routes, layouts, page components |
| `components/ui/` | UI components (shadcn/ui) | Button, Input, Card, Dialog |
| `components/forms/` | Form components | FormWizard, validation wrappers |
| `components/pages/` | Page-level components | Dashboard, JobsPage, ProfilePage |
| `components/layout/` | Layout components | Header, Footer, Sidebar, Navigation |
| `components/charts/` | Data visualization | Charts, graphs, analytics widgets |
| `lib/api/` | API client | HTTP client, API endpoints |
| `lib/utils/` | Utility functions | Formatters, validators, helpers |
| `lib/hooks/` | Custom React hooks | Data fetching, state management |
| `hooks/` | Additional hooks | useWebSocket, useAuth, useUser |
| `contexts/` | React Context | AuthContext, ThemeContext |
| `types/` | TypeScript types | Type definitions, interfaces |
| `styles/` | Global styles | CSS, Tailwind utilities |
| `config/` | Configuration | App settings, constants |

### Static Assets (`public/`)

| Directory | Purpose | Usage |
|-----------|---------|-------|
| `images/` | Image assets | Logos, backgrounds, illustrations |
| `icons/` | Icon files | SVG icons, favicons |
| `fonts/` | Font files | Custom fonts |

### Testing

| Directory | Purpose | Framework |
|-----------|---------|-----------|
| `tests/e2e/` | End-to-end tests | Playwright |
| `tests/integration/` | Integration tests | Vitest/Jest |
| `cypress/` | E2E tests (legacy) | Cypress |
| `coverage/` | Coverage reports | Jest/Vitest |
| `*.test.ts(x)` | Unit tests (co-located) | Vitest/Jest |

### Configuration (`.tools/`)

| File | Purpose | Notes |
|------|---------|-------|
| `.prettierrc.json` | Code formatting | Prettier configuration |
| `.prettierignore` | Prettier ignore patterns | Files to skip formatting |
| `jest.config.js` | Unit testing | Jest configuration |
| `jest.setup.js` | Test setup | Global test utilities |
| `vitest.config.ts` | Unit testing (modern) | Vitest configuration |
| `playwright.config.ts` | E2E testing | Playwright configuration |
| `commitlint.config.js` | Commit linting | Conventional commits |

## 🔧 Common Tasks

### Development

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Type check
npm run type-check

# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Format check
npm run format:check
```

### Testing

```bash
# Run all tests
npm test

# Run unit tests
npm run test:unit

# Run tests in watch mode
npm run test:watch

# Run E2E tests (Playwright)
npm run test:e2e

# Run E2E tests (Cypress)
npm run cypress:open

# Generate coverage report
npm run test:coverage
```

### Bundle Analysis

```bash
# Analyze bundle size
npm run analyze
# or
npx ts-node bin/analyze-bundle.ts

# Optimize bundle
npx ts-node bin/optimize-bundle.ts
```

### Code Quality

```bash
# Type check
npm run type-check

# Lint
npm run lint

# Format
npm run format

# Run all checks
npm run lint && npm run type-check && npm run format:check
```

### Storybook (Component Development)

```bash
# Start Storybook
npm run storybook

# Build Storybook
npm run build-storybook
```

## 🔐 Environment Variables

See `.env.example` and `.env.local.example` for all available environment variables.

### Required Variables

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1

# WebSocket
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### Optional Variables

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
