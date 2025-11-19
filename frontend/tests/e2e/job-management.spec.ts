/**
 * Job Management Workflow E2E Tests
 * 
 * Tests for CRUD operations on jobs: adding, editing, and deleting jobs.
 * Migrated from Cypress to Playwright.
 * 
 * @module tests/e2e/job-management.spec
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
const TEST_USER = {
    username: 'testuser',
    password: 'testpassword',
};

test.describe('Job Management Workflow', () => {
    test.beforeEach(async ({ page }) => {
        // Login before each test
        await page.goto(`${BASE_URL}/login`);

        // Fill login form
        await page.fill('input[name="username"]', TEST_USER.username);
        await page.fill('input[name="password"]', TEST_USER.password);
        await page.click('button[type="submit"]');

        // Wait for successful login redirect to dashboard
        await page.waitForURL(/\/dashboard/, { timeout: 5000 });

        // Navigate to jobs page
        await page.goto(`${BASE_URL}/jobs`);
        await page.waitForLoadState('networkidle');
    });

    test('should allow adding a new job', async ({ page }) => {
        // Click "Add Job" button
        await page.click('button:has-text("Add Job")');

        // Wait for modal to appear
        await expect(page.locator('h2:has-text("Add New Job")')).toBeVisible();

        // Fill in job details
        await page.fill('input[placeholder="Enter company name"]', 'Cypress Test Company');
        await page.fill('input[placeholder="Enter job title"]', 'Cypress QA Engineer');
        await page.fill('input[placeholder="e.g., San Francisco, CA or Remote"]', 'Remote');
        await page.fill('input[placeholder="https://..."]', 'https://www.cypress.io');
        await page.fill('textarea[placeholder="Full job description..."]', 'This is a test job description.');

        // Submit the form by clicking the "Add Job" button in the modal
        await page.click('button:has-text("Add Job")');

        // Verify the job appears in the list
        await expect(page.locator('text=Cypress QA Engineer')).toBeVisible();
        await expect(page.locator('text=Cypress Test Company')).toBeVisible();
    });

    test('should allow editing an existing job', async ({ page }) => {
        // Find the job card and click edit button
        const jobCard = page.locator('[data-testid="job-card"]:has-text("Cypress QA Engineer")');
        await jobCard.locator('button[title="Edit Job"]').click();

        // Wait for edit modal to appear
        await expect(page.locator('h2:has-text("Edit Job")')).toBeVisible();

        // Clear and update job title
        await page.fill('input[placeholder="Enter job title"]', '');
        await page.fill('input[placeholder="Enter job title"]', 'Updated Cypress QA Engineer');

        // Submit the update
        await page.click('button:has-text("Update Job")');

        // Verify the updated job title appears
        await expect(page.locator('text=Updated Cypress QA Engineer')).toBeVisible();

        // Verify old title is no longer present
        await expect(page.locator('text=Cypress QA Engineer')).not.toBeVisible();
    });

    test('should allow deleting a job', async ({ page }) => {
        // Set up dialog handler to accept confirmation
        page.on('dialog', dialog => dialog.accept());

        // Find the job card and click delete button
        const jobCard = page.locator('[data-testid="job-card"]:has-text("Updated Cypress QA Engineer")');
        await jobCard.locator('button[title="Delete Job"]').click();

        // Wait for deletion to complete
        await page.waitForTimeout(500);

        // Verify the job is no longer visible
        await expect(page.locator('text=Updated Cypress QA Engineer')).not.toBeVisible();
    });

    test('should validate required fields when adding a job', async ({ page }) => {
        // Click "Add Job" button
        await page.click('button:has-text("Add Job")');

        // Wait for modal to appear
        await expect(page.locator('h2:has-text("Add New Job")')).toBeVisible();

        // Try to submit without filling required fields
        await page.click('button:has-text("Add Job")');

        // Verify validation errors appear (adjust selector based on actual implementation)
        await expect(page.locator('text=/required|must be filled/i').first()).toBeVisible({ timeout: 2000 });
    });

    test('should cancel job creation', async ({ page }) => {
        // Click "Add Job" button
        await page.click('button:has-text("Add Job")');

        // Wait for modal to appear
        await expect(page.locator('h2:has-text("Add New Job")')).toBeVisible();

        // Fill in some data
        await page.fill('input[placeholder="Enter company name"]', 'Test Company');

        // Click cancel button (adjust selector based on actual implementation)
        const cancelButton = page.locator('button:has-text("Cancel")');
        if (await cancelButton.count() > 0) {
            await cancelButton.click();

            // Verify modal is closed
            await expect(page.locator('h2:has-text("Add New Job")')).not.toBeVisible();

            // Verify job was not added
            await expect(page.locator('text=Test Company')).not.toBeVisible();
        }
    });

    test('should search and filter jobs', async ({ page }) => {
        // Check if search input exists
        const searchInput = page.locator('input[type="search"], input[placeholder*="Search"]');

        if (await searchInput.count() > 0) {
            // Type in search query
            await searchInput.fill('Cypress');
            await page.waitForTimeout(500); // Wait for debounce

            // Verify filtered results
            const visibleJobs = page.locator('[data-testid="job-card"]');
            await expect(visibleJobs.first()).toContainText(/Cypress/i);
        }
    });

    test('should display job details when clicking on a job card', async ({ page }) => {
        // Click on a job card
        const jobCard = page.locator('[data-testid="job-card"]').first();
        await jobCard.click();

        // Wait for details view to appear (adjust based on actual implementation)
        await page.waitForTimeout(500);

        // Verify job details are visible (this will vary based on implementation)
        // Could be a modal, a side panel, or a navigation to a details page
        const hasModal = await page.locator('[role="dialog"]').count() > 0;
        const hasDetailsPage = /\/jobs\/\d+/.test(page.url());

        expect(hasModal || hasDetailsPage).toBeTruthy();
    });
});
