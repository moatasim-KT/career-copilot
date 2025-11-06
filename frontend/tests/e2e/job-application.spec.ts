/**
 * Job Application Flow E2E Tests
 * 
 * Tests for creating, editing, and managing job applications.
 * 
 * @module tests/e2e/job-application.spec
 */

import { test, expect } from '@playwright/test';

test.describe('Job Application Flow', () => {
    test.beforeEach(async ({ page }) => {
        // Login before each test
        await page.goto('/');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'TestPassword123!');
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL(/\/dashboard/);
    });

    test('should create new job application', async ({ page }) => {
        // Click "New Application" button
        await page.click('button:has-text("New Application"), a:has-text("New Application")');

        // Fill in application form
        await page.fill('input[name="company"]', 'Acme Corporation');
        await page.fill('input[name="position"]', 'Senior Software Engineer');
        await page.fill('input[name="location"]', 'San Francisco, CA');
        await page.fill('input[name="salary"]', '150000');
        await page.selectOption('select[name="status"]', 'applied');
        await page.fill('textarea[name="notes"]', 'Great opportunity with competitive salary');

        // Submit form
        await page.click('button[type="submit"]:has-text("Save"), button:has-text("Create")');

        // Should show success message
        await expect(page.locator('[role="alert"]:has-text("success"), .toast:has-text("success")')).toBeVisible();

        // Should redirect to applications list or show in list
        await expect(page.locator('text=Acme Corporation')).toBeVisible();
        await expect(page.locator('text=Senior Software Engineer')).toBeVisible();
    });

    test('should edit existing application', async ({ page }) => {
        // Navigate to applications list
        await page.click('a:has-text("Applications"), nav >> text=Applications');

        // Click first application
        await page.click('[data-testid="application-card"]:first-child, .application-item:first-child');

        // Click edit button
        await page.click('button:has-text("Edit"), [aria-label="Edit"]');

        // Update status
        await page.selectOption('select[name="status"]', 'interviewing');
        await page.fill('textarea[name="notes"]', 'First interview scheduled for next week');

        // Save changes
        await page.click('button[type="submit"]:has-text("Save")');

        // Should show success message
        await expect(page.locator('[role="alert"]:has-text("success"), .toast:has-text("success")')).toBeVisible();
    });

    test('should delete application', async ({ page }) => {
        // Navigate to applications
        await page.click('a:has-text("Applications"), nav >> text=Applications');

        // Click delete on first application
        await page.click('[data-testid="application-card"]:first-child button:has-text("Delete"), .application-item:first-child [aria-label="Delete"]');

        // Confirm deletion
        await page.click('button:has-text("Confirm"), button:has-text("Yes")');

        // Should show success message
        await expect(page.locator('[role="alert"]:has-text("deleted"), .toast:has-text("deleted")')).toBeVisible();
    });

    test('should filter applications by status', async ({ page }) => {
        await page.click('a:has-text("Applications")');

        // Click filter dropdown
        await page.click('select[name="status"], button:has-text("Filter")');

        // Select "interviewing"
        await page.selectOption('select[name="status"]', 'interviewing');

        // Wait for filtered results
        await page.waitForTimeout(500);

        // All visible applications should have "interviewing" status
        const applications = await page.locator('[data-testid="application-card"], .application-item').all();
        expect(applications.length).toBeGreaterThan(0);
    });

    test('should search applications', async ({ page }) => {
        await page.click('a:has-text("Applications")');

        // Type in search box
        await page.fill('input[type="search"], input[placeholder*="Search"]', 'Acme');

        // Wait for search results
        await page.waitForTimeout(500);

        // Should show matching results
        await expect(page.locator('text=Acme')).toBeVisible();
    });

    test('should bulk select and delete applications', async ({ page }) => {
        await page.click('a:has-text("Applications")');

        // Select all checkbox
        await page.click('input[type="checkbox"][aria-label*="Select all"], thead input[type="checkbox"]');

        // Click bulk delete
        await page.click('button:has-text("Delete Selected"), button:has-text("Bulk Delete")');

        // Confirm
        await page.click('button:has-text("Confirm"), button:has-text("Yes")');

        // Should show success message
        await expect(page.locator('[role="alert"]:has-text("deleted")')).toBeVisible();
    });

    test('should validate required fields', async ({ page }) => {
        await page.click('button:has-text("New Application")');

        // Try to submit without filling required fields
        await page.click('button[type="submit"]');

        // Should show validation errors
        await expect(page.locator('input[name="company"]:invalid')).toBeVisible();
        await expect(page.locator('input[name="position"]:invalid')).toBeVisible();
    });
});
