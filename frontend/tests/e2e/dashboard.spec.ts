/**
 * Dashboard Navigation E2E Tests
 * 
 * Tests for dashboard navigation, sidebar, and route transitions.
 * 
 * @module tests/e2e/dashboard.spec
 */

import { test, expect } from '@playwright/test';

test.describe('Dashboard Navigation', () => {
    test.beforeEach(async ({ page }) => {
        // Login
        await page.goto('/');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'TestPassword123!');
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL(/\/dashboard/);
    });

    test('should display dashboard overview', async ({ page }) => {
        // Check for key dashboard elements
        await expect(page.locator('h1, h2')).toContainText(/dashboard|overview/i);
        await expect(page.locator('[data-testid="stats-card"], .stat-card')).toHaveCount(4);
    });

    test('should navigate to applications page', async ({ page }) => {
        await page.click('a:has-text("Applications"), nav >> text=Applications');

        await expect(page).toHaveURL(/\/applications/);
        await expect(page.locator('h1')).toContainText(/applications/i);
    });

    test('should navigate to analytics page', async ({ page }) => {
        await page.click('a:has-text("Analytics"), nav >> text=Analytics');

        await expect(page).toHaveURL(/\/analytics/);
        await expect(page.locator('h1')).toContainText(/analytics/i);
    });

    test('should navigate to settings page', async ({ page }) => {
        await page.click('a:has-text("Settings"), nav >> text=Settings');

        await expect(page).toHaveURL(/\/settings/);
        await expect(page.locator('h1')).toContainText(/settings/i);
    });

    test('should toggle sidebar on mobile', async ({ page }) => {
        // Set mobile viewport
        await page.setViewportSize({ width: 375, height: 667 });

        // Open sidebar
        await page.click('button[aria-label*="menu"], button:has-text("Menu")');

        // Sidebar should be visible
        await expect(page.locator('nav, [role="navigation"]')).toBeVisible();

        // Close sidebar
        await page.click('button[aria-label*="close"], button:has-text("Close")');

        // Sidebar should be hidden
        await expect(page.locator('nav, [role="navigation"]')).not.toBeVisible();
    });

    test('should show user profile dropdown', async ({ page }) => {
        // Click user avatar/profile
        await page.click('button[aria-label*="profile"], [data-testid="user-menu"]');

        // Dropdown should be visible
        await expect(page.locator('[role="menu"], .dropdown-menu')).toBeVisible();
        await expect(page.locator('text=Logout')).toBeVisible();
    });

    test('should navigate using keyboard shortcuts', async ({ page }) => {
        // Press Ctrl+K or Cmd+K for search
        await page.keyboard.press(process.platform === 'darwin' ? 'Meta+K' : 'Control+K');

        // Search modal should open
        await expect(page.locator('[role="dialog"]:has-text("Search"), .search-modal')).toBeVisible();

        // Press Escape to close
        await page.keyboard.press('Escape');

        await expect(page.locator('[role="dialog"]')).not.toBeVisible();
    });

    test('should display breadcrumbs correctly', async ({ page }) => {
        await page.click('a:has-text("Applications")');
        await page.click('[data-testid="application-card"]:first-child');

        // Should show breadcrumbs
        await expect(page.locator('nav[aria-label="breadcrumb"], .breadcrumbs')).toBeVisible();
        await expect(page.locator('text=Dashboard')).toBeVisible();
        await expect(page.locator('text=Applications')).toBeVisible();
    });
});
