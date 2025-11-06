/**
 * Authentication Flow E2E Tests
 * 
 * Tests for user authentication including login, logout, and session management.
 * 
 * @module tests/e2e/auth.spec
 */

import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should display login page', async ({ page }) => {
        await expect(page).toHaveTitle(/Career Copilot/);
        await expect(page.locator('h1')).toContainText(/sign in|login/i);
    });

    test('should login with valid credentials', async ({ page }) => {
        // Fill in login form
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'TestPassword123!');

        // Submit form
        await page.click('button[type="submit"]');

        // Should redirect to dashboard
        await expect(page).toHaveURL(/\/dashboard/);
        await expect(page.locator('h1')).toContainText(/dashboard|welcome/i);
    });

    test('should show error for invalid credentials', async ({ page }) => {
        await page.fill('input[name="email"]', 'wrong@example.com');
        await page.fill('input[name="password"]', 'wrongpassword');

        await page.click('button[type="submit"]');

        // Should show error message
        await expect(page.locator('[role="alert"]')).toBeVisible();
        await expect(page.locator('[role="alert"]')).toContainText(/invalid|incorrect/i);
    });

    test('should validate email format', async ({ page }) => {
        await page.fill('input[name="email"]', 'invalidemail');
        await page.fill('input[name="password"]', 'password123');

        await page.click('button[type="submit"]');

        // Should show validation error
        await expect(page.locator('input[name="email"]:invalid')).toBeVisible();
    });

    test('should logout successfully', async ({ page }) => {
        // Login first
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'TestPassword123!');
        await page.click('button[type="submit"]');

        await expect(page).toHaveURL(/\/dashboard/);

        // Click logout
        await page.click('button:has-text("Logout"), [aria-label="Logout"]');

        // Should redirect to login
        await expect(page).toHaveURL(/\/login|\/$/);
    });

    test('should persist session on page reload', async ({ page }) => {
        // Login
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'TestPassword123!');
        await page.click('button[type="submit"]');

        await expect(page).toHaveURL(/\/dashboard/);

        // Reload page
        await page.reload();

        // Should still be on dashboard
        await expect(page).toHaveURL(/\/dashboard/);
    });

    test('should redirect to login when accessing protected route', async ({ page }) => {
        await page.goto('/dashboard');

        // Should redirect to login
        await expect(page).toHaveURL(/\/login|\/$/);
    });
});
