import { expect, test } from '@playwright/test';

/**
 * End-to-End Authentication Flow Tests
 * Tests the complete authentication system including login, register, OAuth, and WebSocket
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
const TEST_USER = {
    username: 'testuser_' + Date.now(),
    email: `testuser_${Date.now()}@example.com`,
    password: 'TestPassword123!',
};

test.describe('Authentication Flow', () => {
    test.beforeEach(async ({ page }) => {
        // Clear storage before each test
        await page.context().clearCookies();
        await page.evaluate(() => {
            localStorage.clear();
            sessionStorage.clear();
        });
    });

    test('should display login page', async ({ page }) => {
        await page.goto(`${BASE_URL}/login`);

        // Check page title and elements
        await expect(page).toHaveTitle(/Career Copilot/);
        await expect(page.locator('h1')).toContainText(/Login|Sign in/i);

        // Check for login form elements
        await expect(page.locator('input[type="email"], input[type="text"]')).toBeVisible();
        await expect(page.locator('input[type="password"]')).toBeVisible();
        await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should display register page', async ({ page }) => {
        await page.goto(`${BASE_URL}/register`);

        await expect(page.locator('h1')).toContainText(/Register|Sign up/i);

        // Check for register form elements
        await expect(page.locator('input[name="username"]')).toBeVisible();
        await expect(page.locator('input[name="email"], input[type="email"]')).toBeVisible();
        await expect(page.locator('input[type="password"]')).toBeVisible();
    });

    test('should register new user successfully', async ({ page }) => {
        await page.goto(`${BASE_URL}/register`);

        // Fill registration form
        await page.fill('input[name="username"]', TEST_USER.username);
        await page.fill('input[name="email"], input[type="email"]', TEST_USER.email);
        const passwordFields = page.locator('input[type="password"]');
        await passwordFields.first().fill(TEST_USER.password);

        // Check for password confirmation field
        if (await passwordFields.count() > 1) {
            await passwordFields.last().fill(TEST_USER.password);
        }

        // Accept terms if checkbox exists
        const termsCheckbox = page.locator('input[type="checkbox"]');
        if (await termsCheckbox.count() > 0) {
            await termsCheckbox.check();
        }

        // Submit form
        await page.click('button[type="submit"]');

        // Should redirect to dashboard
        await page.waitForURL(/\/dashboard/, { timeout: 5000 });

        // Verify token is stored
        const token = await page.evaluate(() => localStorage.getItem('access_token'));
        expect(token).toBeTruthy();

        // Verify user data is stored
        const userData = await page.evaluate(() => localStorage.getItem('user'));
        expect(userData).toBeTruthy();
    });

    test('should login existing user successfully', async ({ page }) => {
        // First, register the user
        await page.goto(`${BASE_URL}/register`);
        await page.fill('input[name="username"]', TEST_USER.username);
        await page.fill('input[name="email"], input[type="email"]', TEST_USER.email);
        const passwordFields = page.locator('input[type="password"]');
        await passwordFields.first().fill(TEST_USER.password);
        if (await passwordFields.count() > 1) {
            await passwordFields.last().fill(TEST_USER.password);
        }
        const termsCheckbox = page.locator('input[type="checkbox"]');
        if (await termsCheckbox.count() > 0) {
            await termsCheckbox.check();
        }
        await page.click('button[type="submit"]');
        await page.waitForURL(/\/dashboard/, { timeout: 5000 });

        // Logout
        const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out"), a:has-text("Logout")');
        if (await logoutButton.count() > 0) {
            await logoutButton.first().click();
            await page.waitForURL(/\/login/, { timeout: 3000 });
        } else {
            await page.goto(`${BASE_URL}/login`);
        }

        // Now test login
        await page.fill('input[type="email"], input[type="text"]', TEST_USER.email);
        await page.fill('input[type="password"]', TEST_USER.password);
        await page.click('button[type="submit"]');

        // Should redirect to dashboard
        await page.waitForURL(/\/dashboard/, { timeout: 5000 });

        // Verify token is stored
        const token = await page.evaluate(() => localStorage.getItem('access_token'));
        expect(token).toBeTruthy();
    });

    test('should show error for invalid credentials', async ({ page }) => {
        await page.goto(`${BASE_URL}/login`);

        await page.fill('input[type="email"], input[type="text"]', 'invalid@example.com');
        await page.fill('input[type="password"]', 'wrongpassword');
        await page.click('button[type="submit"]');

        // Should show error message
        await expect(page.locator('text=/error|invalid|incorrect|failed/i')).toBeVisible({ timeout: 3000 });

        // Should not redirect
        await expect(page).toHaveURL(/\/login/);
    });

    test('should protect dashboard route when not authenticated', async ({ page }) => {
        await page.goto(`${BASE_URL}/dashboard`);

        // Should redirect to login
        await page.waitForURL(/\/login/, { timeout: 3000 });

        // Should preserve redirect URL
        expect(page.url()).toContain('redirect=');
    });

    test('should redirect authenticated user from login page', async ({ page }) => {
        // First login
        await page.goto(`${BASE_URL}/login`);
        await page.fill('input[type="email"], input[type="text"]', TEST_USER.email);
        await page.fill('input[type="password"]', TEST_USER.password);
        await page.click('button[type="submit"]');
        await page.waitForURL(/\/dashboard/, { timeout: 5000 });

        // Try to access login page again
        await page.goto(`${BASE_URL}/login`);

        // Should redirect to dashboard
        await page.waitForURL(/\/dashboard/, { timeout: 3000 });
    });

    test('should logout successfully', async ({ page }) => {
        // Login first
        await page.goto(`${BASE_URL}/login`);
        await page.fill('input[type="email"], input[type="text"]', TEST_USER.email);
        await page.fill('input[type="password"]', TEST_USER.password);
        await page.click('button[type="submit"]');
        await page.waitForURL(/\/dashboard/, { timeout: 5000 });

        // Verify token exists
        let token = await page.evaluate(() => localStorage.getItem('access_token'));
        expect(token).toBeTruthy();

        // Logout
        const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out"), a:has-text("Logout")');
        await logoutButton.first().click();

        // Should redirect to login
        await page.waitForURL(/\/login/, { timeout: 3000 });

        // Verify token is cleared
        token = await page.evaluate(() => localStorage.getItem('access_token'));
        expect(token).toBeNull();
    });

    test('should persist authentication across page reloads', async ({ page }) => {
        // Login
        await page.goto(`${BASE_URL}/login`);
        await page.fill('input[type="email"], input[type="text"]', TEST_USER.email);
        await page.fill('input[type="password"]', TEST_USER.password);
        await page.click('button[type="submit"]');
        await page.waitForURL(/\/dashboard/, { timeout: 5000 });

        // Reload page
        await page.reload();

        // Should still be on dashboard (not redirected to login)
        await expect(page).toHaveURL(/\/dashboard/);

        // Token should still exist
        const token = await page.evaluate(() => localStorage.getItem('access_token'));
        expect(token).toBeTruthy();
    });

    test('should display notification center', async ({ page }) => {
        // Login
        await page.goto(`${BASE_URL}/login`);
        await page.fill('input[type="email"], input[type="text"]', TEST_USER.email);
        await page.fill('input[type="password"]', TEST_USER.password);
        await page.click('button[type="submit"]');
        await page.waitForURL(/\/dashboard/, { timeout: 5000 });

        // Look for notification bell icon
        const notificationBell = page.locator('button:has([data-testid="bell-icon"]), button svg[class*="lucide-bell"]');
        await expect(notificationBell.first()).toBeVisible({ timeout: 5000 });
    });

    test('should display OAuth login options', async ({ page }) => {
        await page.goto(`${BASE_URL}/login`);

        // Check for OAuth buttons
        const oauthButtons = page.locator('button:has-text("Google"), button:has-text("LinkedIn"), button:has-text("GitHub")');
        const count = await oauthButtons.count();

        // Should have at least one OAuth option
        expect(count).toBeGreaterThan(0);
    });
});

test.describe('Protected Routes', () => {
    const protectedRoutes = [
        '/dashboard',
        '/jobs',
        '/applications',
        '/content',
        '/interview-practice',
        '/analytics',
        '/settings',
        '/profile',
    ];

    protectedRoutes.forEach((route) => {
        test(`should protect ${route} route`, async ({ page }) => {
            await page.goto(`${BASE_URL}${route}`);

            // Should redirect to login
            await page.waitForURL(/\/login/, { timeout: 3000 });

            // URL should contain redirect parameter
            expect(page.url()).toContain('redirect=');
        });
    });
});

test.describe('WebSocket Connection', () => {
    test('should connect to WebSocket after login', async ({ page }) => {
        // Login
        await page.goto(`${BASE_URL}/login`);
        await page.fill('input[type="email"], input[type="text"]', TEST_USER.email);
        await page.fill('input[type="password"]', TEST_USER.password);
        await page.click('button[type="submit"]');
        await page.waitForURL(/\/dashboard/, { timeout: 5000 });

        // Wait for WebSocket to connect (check console logs or connection indicator)
        await page.waitForTimeout(2000);

        // Check for connection status indicator
        const notificationBell = page.locator('button:has([data-testid="bell-icon"]), button svg[class*="lucide-bell"]');
        await expect(notificationBell.first()).toBeVisible();

        // WebSocket connection would be verified by checking for connected status
        // This would require implementing a data-testid on the notification center
    });
});
