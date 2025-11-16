# Frontend Features & Documentation Hub

> Comprehensive guide to Career Copilot frontend architecture, components, and features

## Quick Links
- [[../../docs/index|Main Documentation Hub]]
- [[../../README|Project README]]
- [[../README|Frontend README]]
- [[../../docs/FRONTEND_QUICK_START|Frontend Quick Start]]
- [[../../docs/DEVELOPER_GUIDE|Developer Guide]]
- [[../../docs/components/README|Component Documentation Hub (190+ components)]]

## 🎯 Frontend Overview

The Career Copilot frontend is built with:
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: React Context + Zustand
- **API Client**: Unified fetch wrapper (`src/lib/api/client.ts`)
- **Error Monitoring**: Sentry
- **Testing**: Jest (unit) + Playwright (E2E)

## 📚 Feature Documentation

### 🚀 Performance Optimization

#### Lazy Loading & Code Splitting
**Location**: [[../src/components/lazy/README.md]]

- **Implementation**: `src/components/lazy/`
- **Usage Examples**: [[../src/components/lazy/USAGE_EXAMPLES.md]]
- **Components**:
  - [[../../docs/components/LazyAdvancedSearch|LazyAdvancedSearch]]
  - [[../../docs/components/LazyCommandPalette|LazyCommandPalette]]
  - [[../../docs/components/LazyEnhancedDashboard|LazyEnhancedDashboard]]
  - [[../../docs/components/LazyAnalyticsPage|LazyAnalyticsPage]]
  - [[../../docs/components/LazyDataTable|LazyDataTable]]
  - [[../../docs/components/LazyBulkActionBar|LazyBulkActionBar]]
  - [[../../docs/components/LazyNotificationCenter|LazyNotificationCenter]]
  - [[../../docs/components/LazyRichTextEditor|LazyRichTextEditor]]

**Benefits**:
- Reduces initial bundle size by 40%+
- Improves Time to Interactive (TTI)
- Code-split heavy components (charts, editors, data tables)

---

#### Loading States
**Location**: [[../src/components/ui/loading/README.md]]

Standardized loading UI patterns:
- Skeleton loaders for content placeholders
- Spinner components for async operations
- Suspense boundaries for React 18
- Progressive loading for large datasets

**Implementation**:
```typescript
import { Skeleton } from '@/components/ui/skeleton';

<Suspense fallback={<Skeleton className="h-96 w-full" />}>
  <LazyDataTable />
</Suspense>
```

---

### 🎨 UI Component Libraries

#### DataTable Component
**Location**: [[../src/components/ui/DataTable/README.md]]

Advanced data table with:
- Sorting, filtering, pagination
- Column visibility controls
- Row selection (single/multi)
- Export to CSV/Excel
- Responsive design

**Integration Guide**: [[../src/components/ui/DataTable/INTEGRATION_GUIDE.md]]

---

#### Card2 Enhancement
**Test Documentation**:
- [[../src/components/ui/__tests__/Card2.implementation-summary.md]]
- [[../src/components/ui/__tests__/Card2.verification.md]]
- [[../src/components/ui/__tests__/Card2.before-after.md]]

Enhanced Card component with:
- Dark mode support
- Improved accessibility (ARIA labels)
- Better contrast ratios
- Visual consistency

---

### 🌙 Dark Mode Support

**Test Reports**:
- [[../src/components/ui/__tests__/DARK_MODE_TEST_REPORT.md]] - Comprehensive test results
- [[../src/components/ui/__tests__/DARK_MODE_VERIFICATION.md]] - Verification checklist
- [[../src/components/ui/__tests__/DARK_MODE_MANUAL_TEST_CHECKLIST.md]] - Manual testing guide

**Dashboard Tests**:
- [[../src/components/pages/__tests__/Dashboard.contrast-verification.md]]
- [[../src/components/pages/__tests__/Dashboard.implementation-summary.md]]

**Features**:
- System preference detection
- Manual toggle override
- Persistent user preference
- Smooth transitions
- WCAG AA contrast compliance

**Implementation**:
```typescript
import { useTheme } from 'next-themes';

const { theme, setTheme } = useTheme();
<button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
  Toggle Theme
</button>
```

---

### 📊 Domain-Specific Components

#### Jobs Module
**Location**: [[../src/components/jobs/README.md]]

- Job search interface
- Job detail views
- Application tracking
- Job recommendations

**Integration**: [[../src/components/jobs/INTEGRATION_GUIDE.md]]

---

#### Applications Module
**Location**: [[../src/components/applications/README.md]]

- Application list/grid views
- Application status tracking
- Document management
- Timeline visualization

**Quick Start**: [[../src/components/applications/QUICK_START.md]]  
**Integration**: [[../src/components/applications/INTEGRATION_GUIDE.md]]

---

### 🛠️ Developer Tools & Features

#### Error Monitoring - Sentry Integration
**Location**: [[../src/lib/SENTRY_INTEGRATION_GUIDE.md]]

**Features**:
- Automatic error reporting
- User session tracking
- Performance monitoring
- Breadcrumb trails
- Source map support

**Configuration**:
- `sentry.server.config.ts` - Server-side error tracking
- `sentry.edge.config.ts` - Edge runtime error tracking

**Environment Variables**:
```bash
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn
SENTRY_AUTH_TOKEN=your-auth-token
```

---

#### Contextual Help System
**Location**: [[../src/components/help/CONTEXTUAL_HELP_INTEGRATION_GUIDE.md]]

On-demand help tooltips and guides:
- Context-aware help bubbles
- Interactive walkthroughs
- Feature discovery
- Keyboard shortcuts guide

---

### 🧪 Testing Infrastructure

#### Testing Guides

**Functional Testing**: [[FUNCTIONAL_TESTING_GUIDE.md]]
- Form submission and validation
- Navigation and routing
- API integration testing
- Error handling scenarios
- Cross-browser compatibility

**User Acceptance Testing (UAT)**: [[UAT_GUIDE.md]]
- Test planning and preparation
- User scenarios and workflows
- Feedback collection templates
- Bug reporting procedures
- UAT templates: [[uat/]]

**Browser Compatibility**: [[BROWSER_COMPATIBILITY.md]]
- Supported browsers and versions
- Compatibility testing procedures
- Known issues and workarounds
- Progressive enhancement strategies

**Security Testing**: [[SECURITY_GUIDE.md]]
- XSS prevention
- CSRF protection
- Content Security Policy (CSP)
- Secure authentication flows
- Input validation

**Performance Auditing**: [[PERFORMANCE_AUDIT_GUIDE.md]]
- Lighthouse audits
- Core Web Vitals monitoring
- Bundle size analysis
- Load testing procedures
- Performance budgets

#### UI Component Tests
**Location**: [[../src/components/ui/__tests__/README.md]]

- Unit tests for all UI components
- Dark mode verification tests
- Accessibility (a11y) tests
- Visual regression tests

**Test Categories**:
- **Dark Mode**: DARK_MODE_TEST_REPORT.md
- **Card Enhancements**: Card2.*.md
- **Dashboard**: Dashboard.*.md

---

## 🔗 Frontend-Backend Integration

### API Client
**Location**: `frontend/src/lib/api/client.ts`

Unified API client with:
- Automatic error handling
- Request/response interceptors
- Type-safe endpoints (generated from OpenAPI)
- Authentication token management (when enabled)

**Usage**:
```typescript
import { fetchApi } from '@/lib/api/client';

const jobs = await fetchApi<Job[]>('/jobs', {
  method: 'GET',
  params: { limit: 10 },
  requiresAuth: false
});
```

---

### Endpoint Discovery & Gap Analysis
**Backend Documentation**:
- [[../../backend/app/testing/README.md]] - Endpoint Discovery Framework
- [[../../backend/app/testing/README_GAP_ANALYSIS.md]] - Frontend-Backend Gap Analysis

**Gap Analysis Reports**:
- [[../../backend/reports/gap_analysis/gap_analysis.md]]
- [[../../backend/reports/gap_analysis_demo/gap_analysis.md]]

**Purpose**: Automatically detect mismatches between:
- Frontend API calls
- Backend endpoint implementations
- Request/response type definitions

---

### OpenAPI Integration
**Spec Location**: `frontend/openapi.json` (auto-generated)

Generated by: [[../../scripts/generate_openapi_docs.py]]

Used for:
- Type-safe API client generation
- API documentation (Swagger UI)
- Frontend-backend contract validation

---

## 📖 Documentation Structure

### Frontend Source Documentation
All feature-specific documentation lives in `frontend/src/` subdirectories:

```
frontend/src/
├── components/
│   ├── lazy/
│   │   ├── README.md                     # Lazy loading guide
│   │   └── USAGE_EXAMPLES.md             # Code examples
│   ├── ui/
│   │   ├── loading/README.md             # Loading states guide
│   │   ├── DataTable/
│   │   │   ├── README.md                 # DataTable documentation
│   │   │   └── INTEGRATION_GUIDE.md      # Integration steps
│   │   └── __tests__/
│   │       ├── README.md                 # Test documentation
│   │       ├── DARK_MODE_TEST_REPORT.md
│   │       ├── DARK_MODE_VERIFICATION.md
│   │       ├── Card2.*.md                # Card2 test docs
│   │       └── ...
│   ├── jobs/
│   │   ├── README.md
│   │   └── INTEGRATION_GUIDE.md
│   ├── applications/
│   │   ├── README.md
│   │   ├── QUICK_START.md
│   │   └── INTEGRATION_GUIDE.md
│   └── help/
│       └── CONTEXTUAL_HELP_INTEGRATION_GUIDE.md
└── lib/
    └── SENTRY_INTEGRATION_GUIDE.md       # Error monitoring
```

### Component API Documentation
Complete component API docs in [[../../docs/components/README.md]]:
- 190+ component documentation files
- Props, usage, examples
- Auto-generated from TypeScript types

---

## 🚦 Getting Started

### Quick Start
See [[../../docs/FRONTEND_QUICK_START|Frontend Quick Start Guide]]

### Development Setup
```bash
# Install dependencies
cd frontend && npm install

# Run development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

### Environment Configuration
Copy `frontend/.env.example` to `frontend/.env`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn
```

---

## 🔧 Build & Deployment

### Build Optimization
- **Code Splitting**: Automatic via Next.js + lazy loading
- **Tree Shaking**: Removes unused code
- **Image Optimization**: Next.js Image component
- **Font Optimization**: Next.js Font optimization

### Production Build
```bash
npm run build
npm run start  # Production server
```

### Docker Deployment
See [[../../deployment/docker/Dockerfile.frontend]]

---

## 🧩 Integration Patterns

### Adding a New Feature Component

1. **Create Component**:
   ```bash
   frontend/src/components/features/MyFeature/
   ├── MyFeature.tsx
   ├── MyFeature.test.tsx
   └── README.md
   ```

2. **Document Component**:
   - Add README.md in component directory
   - Generate API docs: `npm run docs:generate`
   - Add wikilinks to this hub

3. **Add to Component Hub**:
   Link from [[../../docs/components/README.md]]

4. **Integration Testing**:
   - Unit tests (Jest)
   - Integration tests (React Testing Library)
   - E2E tests (Playwright)

---

## 🎯 Best Practices

### Component Development
- Use TypeScript for type safety
- Follow shadcn/ui component patterns
- Implement proper loading states
- Add dark mode support
- Write unit tests (>80% coverage target)
- Document props and usage

### Performance
- Lazy load heavy components (>50KB)
- Use React.memo() for expensive renders
- Implement virtualization for long lists
- Optimize images with Next.js Image
- Monitor bundle size with size-limit

### Accessibility
- Semantic HTML
- ARIA labels and roles
- Keyboard navigation
- Screen reader support
- WCAG AA contrast ratios

---

## 📦 Key Dependencies

### UI Framework
- `next` (15.x) - React framework
- `react` (18.x) - UI library
- `typescript` (5.x) - Type safety

### UI Components
- `@radix-ui/*` - Headless UI primitives
- `tailwindcss` - Utility-first CSS
- `lucide-react` - Icon library

### State & Data
- `zustand` - State management
- `react-hook-form` - Form handling
- `zod` - Schema validation

### Monitoring & Testing
- `@sentry/nextjs` - Error monitoring
- `jest` - Unit testing
- `@playwright/test` - E2E testing

---

## 🧪 User Acceptance Testing (UAT)

### UAT Documentation
- **[[./uat/INVITATION_EMAIL_TEMPLATE.md|UAT Invitation Email]]** - Participant invitation template
- **[[./uat/TESTING_CHECKLIST.md|UAT Testing Checklist]]** - Comprehensive testing tasks
- **[[./uat/BUG_REPORT_TEMPLATE.md|Bug Report Template]]** - Standardized bug reporting
- **[[./uat/SURVEY_TEMPLATE.md|UAT Survey]]** - Post-testing feedback survey

### UAT Process
1. **Recruit Participants**: Use invitation email template
2. **Conduct Testing**: Follow testing checklist
3. **Report Issues**: Use bug report template
4. **Collect Feedback**: Distribute survey template

---

## 🔍 Related Documentation

### Main Documentation
- [[../../docs/index|Documentation Hub]] - Central docs
- [[../../docs/DEVELOPER_GUIDE|Developer Guide]] - Development workflows
- [[../../docs/components/README|Component Docs]] - 190+ components

### Setup & Configuration
- [[../../docs/FRONTEND_QUICK_START|Frontend Quick Start]]
- [[../../LOCAL_SETUP|Local Setup Guide]]
- [[../../frontend/README|Frontend README]]

### Backend Integration
- [[../../backend/README|Backend README]]
- [[../../backend/app/testing/README.md|Endpoint Discovery]]
- [[../../backend/app/testing/README_GAP_ANALYSIS.md|Gap Analysis]]

### Testing
- [[../../docs/development/testing-strategies|Testing Strategies]]
- [[../src/components/ui/__tests__/README.md|UI Tests]]

---

## 🤝 Contributing

See [[../../CONTRIBUTING|Contributing Guide]] for:
- Code standards
- PR process
- Testing requirements
- Documentation guidelines

---

**Last Updated**: 2025-01-14 (Phase 4: Frontend Features Documentation)  
**Maintainers**: Career Copilot Frontend Team
