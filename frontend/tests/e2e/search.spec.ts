/**
 * Search Functionality E2E Tests
 * 
 * Tests for global search, filters, and advanced search features.
 * 
 * @module tests/e2e/search.spec
 */

import { test, expect } from '@playwright/test';

test.describe('Search Functionality', () => {
    test.beforeEach(async ({ page }) => {
        // Login
        await page.goto('/');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'TestPassword123!');
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL(/\/dashboard/);
    });

    test('should open global search with keyboard shortcut', async ({ page }) => {
        // Press Ctrl+K or Cmd+K
        await page.keyboard.press(process.platform === 'darwin' ? 'Meta+K' : 'Control+K');

        // Search modal should open
        await expect(page.locator('[role="dialog"]:has-text("Search"), .search-modal')).toBeVisible();
        await expect(page.locator('input[type="search"]')).toBeFocused();
    });

    test('should search for applications', async ({ page }) => {
        // Open search
        await page.keyboard.press(process.platform === 'darwin' ? 'Meta+K' : 'Control+K');

        // Type search query
        await page.fill('input[type="search"]', 'Software Engineer');

        // Wait for results
        await page.waitForTimeout(500);

        // Should show matching results
        const results = page.locator('[role="option"], .search-result');
        await expect(results.first()).toBeVisible();
        await expect(page.locator('text=Software Engineer')).toBeVisible();
    });

    test('should navigate to result on click', async ({ page }) => {
        await page.keyboard.press(process.platform === 'darwin' ? 'Meta+K' : 'Control+K');
        await page.fill('input[type="search"]', 'Acme');
        await page.waitForTimeout(500);

        // Click first result
        await page.click('[role="option"]:first-child, .search-result:first-child');

        // Should navigate to detail page
        await expect(page).toHaveURL(/\/applications\/\w+/);
    });

    test('should navigate results with keyboard', async ({ page }) => {
        await page.keyboard.press(process.platform === 'darwin' ? 'Meta+K' : 'Control+K');
        await page.fill('input[type="search"]', 'Engineer');
        await page.waitForTimeout(500);

        // Press down arrow
        await page.keyboard.press('ArrowDown');
        await page.keyboard.press('ArrowDown');

        // Press Enter to select
        await page.keyboard.press('Enter');

        // Should navigate
        await expect(page).toHaveURL(/\/applications\/\w+/);
    });

    test('should show recent searches', async ({ page }) => {
        await page.keyboard.press(process.platform === 'darwin' ? 'Meta+K' : 'Control+K');

        // Should show recent searches section
        await expect(page.locator('text=Recent, text=History')).toBeVisible();
    });

    test('should filter by company', async ({ page }) => {
        await page.click('a:has-text("Applications")');

        // Click company filter
        await page.click('button:has-text("Company"), select[name="company"]');
        await page.selectOption('select[name="company"]', { index: 1 });

        // Wait for filtered results
        await page.waitForTimeout(500);

        // Results should be filtered
        const count = await page.locator('[data-testid="application-card"]').count();
        expect(count).toBeGreaterThan(0);
    });

    test('should filter by date range', async ({ page }) => {
        await page.click('a:has-text("Applications")');

        // Open date filter
        await page.click('button:has-text("Date"), input[name="dateFrom"]');

        // Select date range (last 30 days)
        await page.click('button:has-text("Last 30 days")');

        // Results should update
        await page.waitForTimeout(500);
    });

    test('should clear all filters', async ({ page }) => {
        await page.click('a:has-text("Applications")');

        // Apply some filters
        await page.selectOption('select[name="status"]', 'interviewing');
        await page.waitForTimeout(300);

        // Click "Clear Filters"
        await page.click('button:has-text("Clear"), button:has-text("Reset")');

        // All applications should be visible
        await page.waitForTimeout(300);
    });

    test('should show no results message', async ({ page }) => {
        await page.keyboard.press(process.platform === 'darwin' ? 'Meta+K' : 'Control+K');

        // Search for something that doesn't exist
        await page.fill('input[type="search"]', 'xyznonexistent12345');
        await page.waitForTimeout(500);

        // Should show no results message
        await expect(page.locator('text=No results, text=not found')).toBeVisible();
    });
});
