import { test, expect } from '@playwright/test';

test.describe('Auth Accessibility', () => {
    test('login page should have no accessibility violations', async ({ page }) => {
        await page.goto('/login');
        await expect(page.locator('h1')).toHaveText(/Sign In|Login/);
        const accessibilityScanResults = await page.accessibility.snapshot();
        expect(accessibilityScanResults).toBeTruthy();
        // Check for ARIA attributes on input fields
        await expect(page.locator('input[aria-label="Email"]')).toHaveCount(1);
        await expect(page.locator('input[aria-label="Password"]')).toHaveCount(1);
    });

    test('should support keyboard navigation for login form', async ({ page }) => {
        await page.goto('/login');
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        const emailInput = page.locator('input[aria-label="Email"]');
        await expect(emailInput).toBeFocused();
        await page.keyboard.press('Tab');
        const passwordInput = page.locator('input[aria-label="Password"]');
        await expect(passwordInput).toBeFocused();
    });

    test('should have visible focus indicators on login button', async ({ page }) => {
        await page.goto('/login');
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        const loginBtn = page.locator('button[type="submit"]');
        await expect(loginBtn).toBeFocused();
        const style = await loginBtn.evaluate((el) => window.getComputedStyle(el).outlineStyle);
        expect(style).not.toBe('none');
    });
});
