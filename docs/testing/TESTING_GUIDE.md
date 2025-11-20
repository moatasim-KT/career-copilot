# Testing Guide

> **Consolidated Guide**: This document combines all testing-related documentation for easier reference.
> - Formerly: `testing/TESTING_AND_UI_REFACTORING_OVERVIEW.md`, `testing/ACCESSIBILITY_TESTING.md`, `testing/ACCESSIBILITY_AUDIT_SUMMARY.md`, `development/testing-strategies.md`, `TESTING_AND_UI_REF

ACTORING_OVERVIEW.md`, `TESTING_UI_REFACTORING_COMPLETION.md`

**Quick Links**: [[index|Documentation Hub]] | [[DEVELOPER_GUIDE|Developer Guide]] | [[GETTING_STARTED|Getting Started]]

---

## Table of Contents

1. [Overview](#overview)
2. [Testing Pyramid](#testing-pyramid)
3. [Quick Commands](#quick-commands)
4. [Backend Testing](#backend-testing)
5. [Frontend Testing](#frontend-testing)
6. [Accessibility Testing](#accessibility-testing)
7. [End-to-End Testing](#end-to-end-testing)
8. [Performance Testing](#performance-testing)
9. [Testing Strategies](#testing-strategies)
10. [CI/CD Integration](#cicd-integration)

---

## Overview

Career Copilot uses comprehensive testing across multiple layers to ensure stability, accessibility, and performance of the FastAPI + Next.js stack.

### Testing Coverage

- **Backend**: Pytest (unit + integration tests)
- **Frontend**: Jest (unit tests) + Playwright (E2E)
- **Accessibility**: jest-axe + axe-core + manual WCAG 2.1 AA checks
- **Performance**: Lighthouse + custom benchmarks
- **Security**: Bandit + npm audit

---

## Testing Pyramid

| Layer | Scope | Tools | Commands |
|-------|-------|-------|----------|
| **Unit** | Pure logic (services, hooks, components) | pytest, jest | `pytest backend/tests/unit`, `npm run test` |
| **Integration** | Service boundaries (DB, Celery, API routes) | pytest with fixtures, Playwright mocks | `pytest backend/tests/integration` |
| **E2E** | User flows (browser + API) | Playwright | `npm run test:e2e` |
| **Non-Functional** | Accessibility, performance, security | jest-axe, Lighthouse, quality checks | `npm run test:a11y`, `make quality-check` |

---

## Quick Commands

```bash
# Full quality sweep (lint + types + security)
make quality-check

# All tests (backend + frontend + accessibility)
make test

# Backend only
cd backend && pytest -v

# Frontend coverage
cd frontend && npm run test:coverage

# Accessibility tests
cd frontend && npm run test:a11y

# E2E tests
cd frontend && npm run test:e2e

# Specific test file
npm run test -- Badge.test.tsx
```

---

## Backend Testing

### Unit Tests (Pytest)

**Location**: `backend/tests/unit/`

**Purpose**: Test pure services (`job_service`, `notification_service`, etc.) and helpers.

**Run**:
```bash
cd backend
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ -v --cov=backend --cov-report=term-missing

# Specific test
pytest tests/unit/test_job_service_ingestion.py -vv
```

**Example**:
```python
import pytest
from app.services.job_service import JobService

def test_job_deduplication(db_session):
    """Test that duplicate jobs are identified correctly."""
    service = JobService(db_session)
    
    job1 = {"title": "Python Developer", "company": "Tech Corp", ...}
    job2 = {"title": "Python Developer", "company": "Tech Corp", ...}
    
    result1 = await service.create_job(job1)
    result2 = await service.create_job(job2)
    
    assert result2.is_duplicate
```

### Integration Tests

**Location**: `backend/tests/integration/` + `backend/tests/test_*.py`

**Purpose**: Test API routes, schedulers, scraping harnesses with real database.

**Run**:
```bash
pytest tests/integration/ -v

# With Docker stack
docker-compose up backend db redis -d
pytest tests/integration/test_api_endpoints.py
```

### Fixtures

Defined in `backend/tests/conftest.py`:
- `db_session`: In-memory SQLite or test database
- `client`: FastAPI test client
- `celery_app`: Celery stub for async tasks
- `mock_redis`: Redis mock for caching tests

---

## Frontend Testing

### Jest Unit/Component Tests

**Location**: `frontend/src/**/__tests__/**/*.test.ts(x)`

**Config**: `frontend/.tools/jest.config.js` with setup at `.tools/jest.setup.js`

**Run**:
```bash
cd frontend

# All tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage

# Specific file
npm run test -- Button.test.tsx
```

**Example**:
```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Button from '../Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick handler', async () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    
    await userEvent.click(screen.getByText('Click'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Testing Library Best Practices

1. **Query by role first**: `screen.getByRole('button', { name: 'Submit' })`
2. **Avoid implementation details**: Don't test class names or internal state
3. **Test user behavior**: Simulate what users actually do
4. **Use userEvent over fireEvent**: More realistic interactions

---

## Accessibility Testing

### Automated Testing (jest-axe)

**Command**: `npm run test:a11y`

**Location**: `frontend/src/**/__tests__/**/*.a11y.test.tsx`

**Example**:
```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('Button Accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper ARIA label', () => {
    render(<Button aria-label="Submit form">Submit</Button>);
    expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Submit form');
  });
});
```

### Full Site Audit

**Tool**: axe-core with Puppeteer

**Run**:
```bash
cd frontend

# Audit all pages
npm run accessibility:audit

# Verbose output
npm run accessibility:audit:verbose

# Specific page
npm run accessibility:audit -- --url=http://localhost:3000/jobs
```

### WCAG 2.1 AA Checklist

#### Perceivable
- [ ] All images have alt text
- [ ] Color is not the only visual means of conveying information
- [ ] Text has sufficient contrast (4.5:1 for normal text)
- [ ] Content is presentable in different ways

#### Operable
- [ ] All functionality available via keyboard
- [ ] Users have enough time to read and use content
- [ ] No content flashes more than 3 times per second
- [ ] Users can navigate, find content, and determine where they are

#### Understandable
- [ ] Text is readable and understandable
- [ ] Content appears and operates in predictable ways
- [ ] Users are helped to avoid and correct mistakes

#### Robust
- [ ] Content is compatible with current and future user tools
- [ ] Valid HTML with proper ARIA roles
- [ ] Status messages are programmatically determined

### Manual Testing with Screen Readers

**Tools**:
- **NVDA** (Windows - Free): https://www.nvaccess.org/
- **VoiceOver** (macOS - Built-in): `Cmd+F5` to enable
- **TalkBack** (Android - Built-in)

**Test Scenarios**:
1. Navigate entire page using only keyboard
2. Tab through all interactive elements
3. Verify form labels are read correctly
4. Check that error messages are announced
5. Confirm modal dialogs trap focus

### Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Missing alt text | Add `alt=""` for decorative images, descriptive alt for content |
| Low contrast | Use [[DESIGN_SYSTEM#colors\|design system colors]] with sufficient contrast |
| Missing labels | Add `aria-label` or visible `<label>` elements |
| Keyboard trap | Ensure focus can move freely, implement focus trap for modals only |
| Missing ARIA roles | Add appropriate roles (`button`, `navigation`, `main`, etc.) |

---

## End-to-End Testing

### Playwright E2E Tests

**Location**: `frontend/tests/e2e/`

**Run**:
```bash
cd frontend

# Headless mode
npm run test:e2e

# Interactive UI mode (debugging)
npm run test:e2e:ui

# Specific test file
npm run test:e2e -- job-application.spec.ts
```

**Prerequisites**: Requires full stack running (`docker-compose up -d`)

**Example**:
```typescript
import { test, expect } from '@playwright/test';

test('user can create job application', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Navigate to jobs page
  await page.click('text=Jobs');
  
  // Click on a job
  await page.click('[data-testid="job-card"]').first();
  
  // Apply to job
  await page.click('text=Apply');
  
  // Verify success message
  await expect(page.locator('text=Application submitted')).toBeVisible();
});
```

### E2E Best Practices

1. **Use data-testid attributes**: More stable than text selectors
2. **Wait for network idle**: Use `await page.waitForLoadState('networkidle')`
3. **Screenshot on failure**: Playwright automatically captures screenshots
4. **Test critical user flows only**: Don't duplicate unit test coverage

---

## Performance Testing

### Lighthouse Audits

**Run**:
```bash
cd frontend

# Run Lighthouse audit
npm run lighthouse

# Save report
npm run lighthouse -- --output-path=./reports/lighthouse-$(date +%Y%m%d).html
```

**Metrics Monitored**:
- **Performance**: Score > 90
- **Accessibility**: Score > 95
- **Best Practices**: Score > 90
- **SEO**: Score > 90

### Bundle Size Analysis

```bash
cd frontend

# Analyze bundle
npm run analyze

# Build and check size
npm run build
npm run size
```

**Budgets**:
- Initial bundle: < 200KB gzipped
- Route chunks: < 50KB gzipped
- Total JS: < 500KB gzipped

---

## Testing Strategies

### When to Write Each Type of Test

| Scenario | Test Type | Reason |
|----------|-----------|--------|
| Pure function logic | Unit test | Fast, isolated, easy to debug |
| Component rendering | Component test | Verify UI output |
| API endpoint | Integration test | Test request/response cycle |
| User workflow | E2E test | Verify end-to-end functionality |
| Accessibility | A11y test | Ensure WCAG compliance |
| Performance | Lighthouse | Monitor page load metrics |

### Test Coverage Goals

- **Backend**: > 80% code coverage
- **Frontend**: > 70% code coverage
- **Accessibility**: 100% of components tested
- **E2E**: All critical user flows covered

### Writing Effective Tests

1. **AAA Pattern**: Arrange, Act, Assert
2. **One assertion per test**: Keep tests focused
3. **Descriptive names**: Test name should be a sentence
4. **Mock external dependencies**: Use fixtures and mocks
5. **Test edge cases**: Not just happy path

---

## CI/CD Integration

### GitHub Actions Workflow

Tests run automatically on:
- Pull request creation
- Push to main/develop branches
- Manual workflow dispatch

### Quality Gates

All must pass before merge:
- ✅ Backend pytest (all tests)
- ✅ Frontend Jest (coverage > 70%)
- ✅ Accessibility tests (no violations)
- ✅ ESLint + Prettier (no errors)
- ✅ TypeScript type check (no errors)
- ✅ Security audit (no high/critical vulnerabilities)

### Running Locally Before Push

```bash
# Run all quality checks
make quality-check

# Run all tests
make test

# Quick pre-commit check
make pre-commit
```

---

## Additional Resources

- **Developer Guide**: [[DEVELOPER_GUIDE|Full Developer Documentation]]
- **Design System**: [[DESIGN_SYSTEM|Component Standards]]
- **Troubleshooting**: [[troubleshooting/COMMON_ISSUES|Common Issues]]
- **API Reference**: [[api/API|API Documentation]]

---

**Last Updated**: November 2025  
**Testing Coverage**: ~75% (Backend: 82%, Frontend: 71%)
