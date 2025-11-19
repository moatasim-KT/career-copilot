# E2E Testing Migration Guide: Cypress → Playwright

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

## Overview

Career Copilot is standardizing on **Playwright** for all end-to-end (E2E) testing. This guide explains the migration from Cypress and how to write new E2E tests.

## Why Playwright?

- ✅ **Better TypeScript support** - First-class TypeScript integration
- ✅ **Multi-browser testing** - Chromium, Firefox, WebKit out of the box
- ✅ **Modern APIs** - Auto-waiting, better error messages, native async/await
- ✅ **Better CI/CD integration** - Faster, more reliable, built-in retries
- ✅ **Active development** - Microsoft-backed with frequent updates
- ✅ **Unified tooling** - One tool for all E2E needs

## Current Status

### ✅ Migration Complete! (as of 2025-11-19)

All E2E tests have been successfully migrated to Playwright:

- `/tests/e2e/dashboard.spec.ts` - Dashboard navigation
- `/tests/e2e/auth-flow.spec.ts` - Authentication flows
- `/tests/e2e/search.spec.ts` - Search functionality
- `/tests/e2e/job-application.spec.ts` - Job application workflows
- `/tests/e2e/calendar.spec.ts` - Calendar features
- `/tests/e2e/dashboard-customization.spec.ts` - Dashboard customization
- `/tests/e2e/functional-tests.spec.ts` - General functionality
- `/tests/e2e/cross-browser.spec.ts` - Cross-browser compatibility
- `/tests/e2e/job-management.spec.ts` - **NEW** Job CRUD operations (migrated from Cypress)
- `/tests/e2e/recommendations.spec.ts` - **NEW** Job recommendations and skill gap analysis (migrated from Cypress)

### 🗑️ Deprecated (Cypress)
The following Cypress tests have been migrated and can be removed:
- `/cypress/integration/job_management.spec.js` → Migrated to `/tests/e2e/job-management.spec.ts`
- `/cypress/integration/recommendations.spec.js` → Migrated to `/tests/e2e/recommendations.spec.ts`

**Action Required**: Run `rm -rf cypress/` to remove deprecated Cypress tests and configuration.

## Setup

### Install Dependencies

```bash
npm install -D @playwright/test
npx playwright install
```

### Configuration

Playwright is configured in `playwright.config.js`:

```javascript
module.exports = {
    testDir: './tests/e2e',
    timeout: 60000,
    retries: process.env.CI ? 2 : 0,
    use: {
        baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
    },
    projects: [
        { name: 'chromium', use: { browserName: 'chromium' } },
        { name: 'firefox', use: { browserName: 'firefox' } },
        { name: 'webkit', use: { browserName: 'webkit' } },
    ],
};
```

## Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run in headed mode (see browser)
npm run test:e2e:headed

# Run specific test file
npx playwright test tests/e2e/dashboard.spec.ts

# Run in debug mode
npx playwright test --debug

# Run specific browser
npx playwright test --project=chromium

# Generate test report
npx playwright show-report
```

## Migration Examples

### Example 1: Basic Navigation

**Cypress:**
```javascript
describe('Dashboard', () => {
  beforeEach(() => {
    cy.visit('http://localhost:3000/dashboard');
  });

  it('should display dashboard', () => {
    cy.get('h1').should('contain', 'Dashboard');
  });
});
```

**Playwright:**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should display dashboard', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Dashboard');
  });
});
```

### Example 2: Form Interaction

**Cypress:**
```javascript
it('should add a job', () => {
  cy.get('button').contains('Add Job').click();
  cy.get('input[name="company"]').type('TechCorp');
  cy.get('input[name="title"]').type('Engineer');
  cy.get('button[type="submit"]').click();
  cy.contains('TechCorp').should('be.visible');
});
```

**Playwright:**
```typescript
test('should add a job', async ({ page }) => {
  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.fill('input[name="company"]', 'TechCorp');
  await page.fill('input[name="title"]', 'Engineer');
  await page.getByRole('button', { type: 'submit' }).click();
  await expect(page.getByText('TechCorp')).toBeVisible();
});
```

### Example 3: API Mocking

**Cypress:**
```javascript
cy.intercept('GET', '/api/jobs', { fixture: 'jobs.json' });
```

**Playwright:**
```typescript
await page.route('/api/jobs', route => {
  route.fulfill({
    status: 200,
    body: JSON.stringify(mockJobs),
  });
});
```

## Key Differences

| Feature    | Cypress     | Playwright                           |
| ---------- | ----------- | ------------------------------------ |
| Selectors  | `cy.get()`  | `page.locator()`, `page.getByRole()` |
| Assertions | `.should()` | `expect()`                           |
| Async      | Implicit    | Explicit `await`                     |
| Multi-tab  | ❌ Limited   | ✅ Full support                       |
| Browser    | Chrome only | Chrome, Firefox, Safari              |
| TypeScript | Add-on      | Native                               |

## Best Practices

### 1. Use Semantic Selectors

```typescript
// ✅ Good - Accessible and resilient
await page.getByRole('button', { name: 'Submit' });
await page.getByLabel('Email');
await page.getByText('Welcome');

// ❌ Avoid - Brittle
await page.locator('.btn-primary');
await page.locator('#submit-btn');
```

### 2. Auto-Waiting

Playwright automatically waits for elements to be ready:

```typescript
// No need for explicit waits
await page.click('button'); // Waits for element to be visible and enabled
await expect(page.locator('h1')).toContainText('Title'); // Waits up to timeout
```

### 3. Page Object Model

```typescript
// pages/DashboardPage.ts
export class DashboardPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/dashboard');
  }

  async getStats() {
    return await this.page.locator('[data-testid="stat-card"]').count();
  }
}

// dashboard.spec.ts
test('dashboard stats', async ({ page }) => {
  const dashboard = new DashboardPage(page);
  await dashboard.goto();
  expect(await dashboard.getStats()).toBe(4);
});
```

### 4. Fixtures for Test Data

```typescript
// tests/fixtures/jobs.ts
export const mockJobs = [
  { id: 1, title: 'Engineer', company: 'TechCorp' },
  { id: 2, title: 'Designer', company: 'DesignCo' },
];

// test file
import { mockJobs } from './fixtures/jobs';

test('display jobs', async ({ page }) => {
  await page.route('/api/v1/jobs', route => {
    route.fulfill({ body: JSON.stringify(mockJobs) });
  });
  // ... test logic
});
```

## Accessibility Testing

Playwright has built-in accessibility testing:

```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('dashboard should be accessible', async ({ page }) => {
  await page.goto('/dashboard');
  
  const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
  
  expect(accessibilityScanResults.violations).toEqual([]);
});
```

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

## Troubleshooting

### Tests timing out
- Increase timeout in config: `timeout: 90000`
- Use `test.setTimeout(120000)` for specific tests
- Check network requests aren't hanging

### Flaky tests
- Enable retries: `retries: 2`
- Use proper waiting: `await expect().toBeVisible()` instead of `waitForTimeout`
- Check for race conditions

### Screenshots not captured
- Ensure `screenshot: 'only-on-failure'` in config
- Check test is actually failing (not timing out before failure)

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright vs Cypress](https://playwright.dev/docs/why-playwright)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [API Reference](https://playwright.dev/docs/api/class-playwright)

## Next Steps

1. ✅ Migrate remaining Cypress tests to Playwright
2. ✅ Remove Cypress dependencies once migration is complete
3. Add visual regression testing with Playwright
4. Expand accessibility test coverage
5. Add performance testing with Playwright
