import { test, expect, Page } from '@playwright/test';

/**
 * Comprehensive Functional Testing Suite
 * 
 * Tests all user flows end-to-end:
 * - Sign up → Onboarding → Dashboard
 * - Browse jobs → Save job → Apply
 * - Track application → Update status
 * - View analytics
 * - Form validation and error handling
 * - CRUD operations
 * - Error scenarios
 */

// Test configuration
const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';

// Helper functions
async function login(page: Page, email: string, password: string) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL(`${BASE_URL}/dashboard`);
}

// Test data
const testUser = {
  email: `test-${Date.now()}@example.com`,
  password: 'TestPassword123!',
  name: 'Test User',
  jobTitle: 'Software Engineer',
};

const testJob = {
  title: 'Senior Frontend Developer',
  company: 'Tech Corp',
  location: 'San Francisco, CA',
  salary: '150000',
  url: 'https://example.com/job/123',
  description: 'Great opportunity for experienced frontend developer',
};

test.describe('User Flow 1: Sign up → Onboarding → Dashboard', () => {
  test('should complete full signup and onboarding flow', async ({ page }) => {
    // Step 1: Navigate to signup page
    await page.goto(`${BASE_URL}/signup`);
    await expect(page).toHaveTitle(/Sign Up/i);

    // Step 2: Fill signup form
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.fill('input[name="confirmPassword"]', testUser.password);
    await page.fill('input[name="name"]', testUser.name);

    // Step 3: Submit signup form
    await page.click('button[type="submit"]');

    // Step 4: Verify redirect to onboarding
    await page.waitForURL(`${BASE_URL}/onboarding`);
    await expect(page.locator('h1')).toContainText(/Welcome/i);

    // Step 5: Complete onboarding - Profile info
    await page.fill('input[name="jobTitle"]', testUser.jobTitle);
    await page.fill('input[name="experience"]', '5');
    await page.click('button:has-text("Next")');

    // Step 6: Complete onboarding - Preferences
    await page.check('input[value="remote"]');
    await page.check('input[value="full-time"]');
    await page.click('button:has-text("Next")');

    // Step 7: Complete onboarding - Skills
    await page.fill('input[placeholder*="skill"]', 'React');
    await page.press('input[placeholder*="skill"]', 'Enter');
    await page.fill('input[placeholder*="skill"]', 'TypeScript');
    await page.press('input[placeholder*="skill"]', 'Enter');
    await page.click('button:has-text("Complete")');

    // Step 8: Verify redirect to dashboard
    await page.waitForURL(`${BASE_URL}/dashboard`);
    await expect(page.locator('h1')).toContainText(/Dashboard/i);

    // Step 9: Verify dashboard elements
    await expect(page.locator('[data-testid="stats-card"]')).toBeVisible();
    await expect(page.locator('[data-testid="recent-applications"]')).toBeVisible();
    await expect(page.locator('[data-testid="activity-feed"]')).toBeVisible();
  });

  test('should show validation errors for invalid signup data', async ({ page }) => {
    await page.goto(`${BASE_URL}/signup`);

    // Try to submit empty form
    await page.click('button[type="submit"]');
    await expect(page.locator('text=/email is required/i')).toBeVisible();

    // Try invalid email
    await page.fill('input[name="email"]', 'invalid-email');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=/valid email/i')).toBeVisible();

    // Try weak password
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', '123');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=/password.*8 characters/i')).toBeVisible();

    // Try mismatched passwords
    await page.fill('input[name="password"]', 'Password123!');
    await page.fill('input[name="confirmPassword"]', 'Different123!');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=/passwords.*match/i')).toBeVisible();
  });
});

test.describe('User Flow 2: Browse jobs → Save job → Apply', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUser.email, testUser.password);
  });

  test('should browse jobs and save a job', async ({ page }) => {
    // Step 1: Navigate to jobs page
    await page.click('a[href="/jobs"]');
    await page.waitForURL(`${BASE_URL}/jobs`);
    await expect(page.locator('h1')).toContainText(/Jobs/i);

    // Step 2: Verify job list loads
    await expect(page.locator('[data-testid="job-card"]').first()).toBeVisible();

    // Step 3: Apply filters
    await page.fill('input[placeholder*="Search"]', 'Frontend');
    await page.selectOption('select[name="location"]', 'Remote');
    await page.click('button:has-text("Apply Filters")');

    // Step 4: Wait for filtered results
    await page.waitForTimeout(1000);

    // Step 5: Save a job
    const firstJob = page.locator('[data-testid="job-card"]').first();
    await firstJob.locator('button[aria-label*="Save"]').click();
    await expect(page.locator('text=/saved/i')).toBeVisible();

    // Step 6: Verify job appears in saved jobs
    await page.click('button:has-text("Saved")');
    await expect(page.locator('[data-testid="job-card"]')).toHaveCount(1);
  });

  test('should apply to a job', async ({ page }) => {
    // Step 1: Navigate to jobs page
    await page.goto(`${BASE_URL}/jobs`);

    // Step 2: Click on a job to view details
    await page.locator('[data-testid="job-card"]').first().click();
    await expect(page.locator('[data-testid="job-details"]')).toBeVisible();

    // Step 3: Click apply button
    await page.click('button:has-text("Apply")');

    // Step 4: Fill application form
    await page.fill('textarea[name="coverLetter"]', 'I am very interested in this position...');
    await page.fill('input[name="resumeUrl"]', 'https://example.com/resume.pdf');
    await page.fill('input[name="portfolioUrl"]', 'https://example.com/portfolio');

    // Step 5: Submit application
    await page.click('button[type="submit"]:has-text("Submit Application")');

    // Step 6: Verify success message
    await expect(page.locator('text=/application submitted/i')).toBeVisible();

    // Step 7: Verify redirect to applications page
    await page.waitForURL(`${BASE_URL}/applications`);
    await expect(page.locator('[data-testid="application-card"]')).toHaveCount(1);
  });

  test('should handle job search with no results', async ({ page }) => {
    await page.goto(`${BASE_URL}/jobs`);

    // Search for non-existent job
    await page.fill('input[placeholder*="Search"]', 'NonExistentJobTitle12345');
    await page.click('button:has-text("Apply Filters")');

    // Verify empty state
    await expect(page.locator('text=/no jobs found/i')).toBeVisible();
    await expect(page.locator('[data-testid="job-card"]')).toHaveCount(0);
  });
});

test.describe('User Flow 3: Track application → Update status', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUser.email, testUser.password);
  });

  test('should view and update application status', async ({ page }) => {
    // Step 1: Navigate to applications page
    await page.goto(`${BASE_URL}/applications`);
    await expect(page.locator('h1')).toContainText(/Applications/i);

    // Step 2: Verify application list
    await expect(page.locator('[data-testid="application-card"]').first()).toBeVisible();

    // Step 3: Click on application to view details
    await page.locator('[data-testid="application-card"]').first().click();
    await expect(page.locator('[data-testid="application-details"]')).toBeVisible();

    // Step 4: Update status
    await page.click('button:has-text("Update Status")');
    await page.selectOption('select[name="status"]', 'interviewing');
    await page.fill('textarea[name="notes"]', 'Had first round interview today');
    await page.click('button[type="submit"]:has-text("Save")');

    // Step 5: Verify status updated
    await expect(page.locator('text=/interviewing/i')).toBeVisible();
    await expect(page.locator('text=/Had first round interview/i')).toBeVisible();

    // Step 6: Add interview event
    await page.click('button:has-text("Add Event")');
    await page.selectOption('select[name="eventType"]', 'interview');
    await page.fill('input[name="eventDate"]', '2024-12-20');
    await page.fill('input[name="eventTime"]', '14:00');
    await page.fill('textarea[name="eventNotes"]', 'Technical interview with team');
    await page.click('button[type="submit"]:has-text("Add Event")');

    // Step 7: Verify event added
    await expect(page.locator('text=/Technical interview with team/i')).toBeVisible();
  });

  test('should filter applications by status', async ({ page }) => {
    await page.goto(`${BASE_URL}/applications`);

    // Filter by status
    await page.selectOption('select[name="statusFilter"]', 'interviewing');
    await page.waitForTimeout(500);

    // Verify filtered results
    const applications = page.locator('[data-testid="application-card"]');
    const count = await applications.count();

    for (let i = 0; i < count; i++) {
      await expect(applications.nth(i)).toContainText(/interviewing/i);
    }
  });

  test('should delete an application', async ({ page }) => {
    await page.goto(`${BASE_URL}/applications`);

    // Get initial count
    const initialCount = await page.locator('[data-testid="application-card"]').count();

    // Delete first application
    await page.locator('[data-testid="application-card"]').first().hover();
    await page.locator('[data-testid="application-card"]').first().locator('button[aria-label*="Delete"]').click();

    // Confirm deletion
    await page.click('button:has-text("Confirm")');

    // Verify application deleted
    await expect(page.locator('text=/deleted/i')).toBeVisible();
    await expect(page.locator('[data-testid="application-card"]')).toHaveCount(initialCount - 1);
  });
});

test.describe('User Flow 4: View analytics', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUser.email, testUser.password);
  });

  test('should view analytics dashboard', async ({ page }) => {
    // Step 1: Navigate to analytics page
    await page.goto(`${BASE_URL}/analytics`);
    await expect(page.locator('h1')).toContainText(/Analytics/i);

    // Step 2: Verify charts are visible
    await expect(page.locator('[data-testid="applications-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="status-distribution-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="timeline-chart"]')).toBeVisible();

    // Step 3: Change time range
    await page.selectOption('select[name="timeRange"]', '30');
    await page.waitForTimeout(500);

    // Step 4: Verify charts update
    await expect(page.locator('[data-testid="applications-chart"]')).toBeVisible();

    // Step 5: Verify stats cards
    await expect(page.locator('[data-testid="total-applications"]')).toBeVisible();
    await expect(page.locator('[data-testid="response-rate"]')).toBeVisible();
    await expect(page.locator('[data-testid="interview-rate"]')).toBeVisible();
  });

  test('should export analytics data', async ({ page }) => {
    await page.goto(`${BASE_URL}/analytics`);

    // Click export button
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export")');
    const download = await downloadPromise;

    // Verify download
    expect(download.suggestedFilename()).toMatch(/analytics.*\.csv/i);
  });
});

test.describe('Form Validation and Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUser.email, testUser.password);
  });

  test('should validate job creation form', async ({ page }) => {
    await page.goto(`${BASE_URL}/jobs/new`);

    // Try to submit empty form
    await page.click('button[type="submit"]');
    await expect(page.locator('text=/title is required/i')).toBeVisible();
    await expect(page.locator('text=/company is required/i')).toBeVisible();

    // Fill with invalid data
    await page.fill('input[name="title"]', 'A'); // Too short
    await page.fill('input[name="salary"]', '-1000'); // Negative
    await page.fill('input[name="url"]', 'not-a-url'); // Invalid URL

    await page.click('button[type="submit"]');
    await expect(page.locator('text=/at least 2 characters/i')).toBeVisible();
    await expect(page.locator('text=/positive number/i')).toBeVisible();
    await expect(page.locator('text=/valid url/i')).toBeVisible();
  });

  test('should validate application form', async ({ page }) => {
    await page.goto(`${BASE_URL}/applications/new`);

    // Try to submit without required fields
    await page.click('button[type="submit"]');
    await expect(page.locator('text=/job.*required/i')).toBeVisible();

    // Fill with invalid URL
    await page.fill('input[name="resumeUrl"]', 'invalid-url');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=/valid url/i')).toBeVisible();
  });

  test('should validate settings form', async ({ page }) => {
    await page.goto(`${BASE_URL}/settings/profile`);

    // Clear required field
    await page.fill('input[name="name"]', '');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=/name is required/i')).toBeVisible();

    // Invalid email
    await page.fill('input[name="email"]', 'invalid');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=/valid email/i')).toBeVisible();
  });
});

test.describe('CRUD Operations', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUser.email, testUser.password);
  });

  test('should create, read, update, and delete a job', async ({ page }) => {
    // CREATE
    await page.goto(`${BASE_URL}/jobs/new`);
    await page.fill('input[name="title"]', testJob.title);
    await page.fill('input[name="company"]', testJob.company);
    await page.fill('input[name="location"]', testJob.location);
    await page.fill('input[name="salary"]', testJob.salary);
    await page.fill('input[name="url"]', testJob.url);
    await page.fill('textarea[name="description"]', testJob.description);
    await page.click('button[type="submit"]');

    // Verify creation
    await expect(page.locator('text=/job created/i')).toBeVisible();

    // READ
    await page.goto(`${BASE_URL}/jobs`);
    await expect(page.locator(`text=${testJob.title}`)).toBeVisible();
    await page.click(`text=${testJob.title}`);
    await expect(page.locator(`text=${testJob.company}`)).toBeVisible();
    await expect(page.locator(`text=${testJob.location}`)).toBeVisible();

    // UPDATE
    await page.click('button:has-text("Edit")');
    await page.fill('input[name="title"]', `${testJob.title} - Updated`);
    await page.click('button[type="submit"]');
    await expect(page.locator('text=/updated/i')).toBeVisible();
    await expect(page.locator(`text=${testJob.title} - Updated`)).toBeVisible();

    // DELETE
    await page.click('button:has-text("Delete")');
    await page.click('button:has-text("Confirm")');
    await expect(page.locator('text=/deleted/i')).toBeVisible();
    await page.goto(`${BASE_URL}/jobs`);
    await expect(page.locator(`text=${testJob.title}`)).not.toBeVisible();
  });

  test('should create, read, update, and delete an application', async ({ page }) => {
    // CREATE
    await page.goto(`${BASE_URL}/applications/new`);
    await page.fill('input[name="jobTitle"]', 'Test Job');
    await page.fill('input[name="company"]', 'Test Company');
    await page.selectOption('select[name="status"]', 'applied');
    await page.fill('textarea[name="notes"]', 'Test notes');
    await page.click('button[type="submit"]');

    // Verify creation
    await expect(page.locator('text=/application created/i')).toBeVisible();

    // READ
    await page.goto(`${BASE_URL}/applications`);
    await expect(page.locator('text=Test Job')).toBeVisible();
    await page.click('text=Test Job');
    await expect(page.locator('text=Test Company')).toBeVisible();

    // UPDATE
    await page.click('button:has-text("Edit")');
    await page.selectOption('select[name="status"]', 'interviewing');
    await page.fill('textarea[name="notes"]', 'Updated notes');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=/updated/i')).toBeVisible();
    await expect(page.locator('text=/interviewing/i')).toBeVisible();

    // DELETE
    await page.click('button:has-text("Delete")');
    await page.click('button:has-text("Confirm")');
    await expect(page.locator('text=/deleted/i')).toBeVisible();
  });
});

test.describe('Error Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUser.email, testUser.password);
  });

  test('should handle network failure gracefully', async ({ page, context }) => {
    // Go offline
    await context.setOffline(true);

    // Try to load page
    await page.goto(`${BASE_URL}/jobs`);

    // Verify offline message
    await expect(page.locator('text=/offline/i')).toBeVisible();
    await expect(page.locator('text=/check your connection/i')).toBeVisible();

    // Go back online
    await context.setOffline(false);
    await page.reload();

    // Verify page loads
    await expect(page.locator('h1')).toContainText(/Jobs/i);
  });

  test('should handle 404 errors', async ({ page }) => {
    // Navigate to non-existent page
    await page.goto(`${BASE_URL}/non-existent-page`);

    // Verify 404 page
    await expect(page.locator('text=/404/i')).toBeVisible();
    await expect(page.locator('text=/page not found/i')).toBeVisible();

    // Verify helpful links
    await expect(page.locator('a[href="/dashboard"]')).toBeVisible();
    await expect(page.locator('a[href="/jobs"]')).toBeVisible();
  });

  test('should handle server errors', async ({ page }) => {
    // Mock server error
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    // Try to load data
    await page.goto(`${BASE_URL}/jobs`);

    // Verify error message
    await expect(page.locator('text=/something went wrong/i')).toBeVisible();
    await expect(page.locator('button:has-text("Retry")')).toBeVisible();
  });

  test('should handle authentication errors', async ({ page }) => {
    // Mock 401 error
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 401,
        body: JSON.stringify({ error: 'Unauthorized' })
      });
    });

    // Try to access protected page
    await page.goto(`${BASE_URL}/dashboard`);

    // Verify redirect to login
    await page.waitForURL(`${BASE_URL}/login`);
    await expect(page.locator('text=/session expired/i')).toBeVisible();
  });

  test('should handle validation errors from server', async ({ page }) => {
    // Mock validation error
    await page.route('**/api/jobs', route => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 400,
          body: JSON.stringify({
            errors: {
              title: 'Title is too long',
              salary: 'Salary must be a positive number'
            }
          })
        });
      } else {
        route.continue();
      }
    });

    // Try to create job
    await page.goto(`${BASE_URL}/jobs/new`);
    await page.fill('input[name="title"]', 'Test Job');
    await page.fill('input[name="company"]', 'Test Company');
    await page.click('button[type="submit"]');

    // Verify error messages
    await expect(page.locator('text=/Title is too long/i')).toBeVisible();
    await expect(page.locator('text=/Salary must be a positive number/i')).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUser.email, testUser.password);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);

    // Tab through navigation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Verify focus is visible
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto(`${BASE_URL}/jobs`);

    // Verify ARIA labels
    await expect(page.locator('[aria-label="Search jobs"]')).toBeVisible();
    await expect(page.locator('[aria-label="Filter jobs"]')).toBeVisible();
    await expect(page.locator('[role="main"]')).toBeVisible();
  });
});
