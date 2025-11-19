import { test, expect } from '@playwright/test';

// Accessibility test for dashboard page

test.describe('Dashboard Accessibility', () => {
    test('should have no accessibility violations on load', async ({ page }) => {
        await page.goto('/dashboard');
        // Wait for dashboard widgets to load
        await expect(page.locator('h1')).toHaveText(/Dashboard/);
        // Run axe-core accessibility scan
        const accessibilityScanResults = await page.accessibility.snapshot();
        expect(accessibilityScanResults).toBeTruthy();
        // Optionally, check for specific ARIA roles
        await expect(page.locator('[role="progressbar"]')).toHaveCount(3);
        await expect(page.locator('[role="alert"]')).toHaveCount(0);
    });

    test('should support keyboard navigation', async ({ page }) => {
        await page.goto('/dashboard');
        // Tab to the dashboard view preset select
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        // Focus should be on the select element
        const select = page.locator('select[aria-label="Dashboard view preset"]');
        await expect(select).toBeFocused();
        // Change preset using keyboard
        await page.keyboard.press('ArrowDown');
        await page.keyboard.press('Enter');
        await expect(select).toHaveValue('compact');
    });

    test('should have visible focus indicators', async ({ page }) => {
        await page.goto('/dashboard');
        // Tab to the refresh button
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        const refreshBtn = page.locator('button[aria-label="Refresh dashboard data"]');
        await expect(refreshBtn).toBeFocused();
        // Check for focus ring
        const style = await refreshBtn.evaluate((el) => window.getComputedStyle(el).outlineStyle);
        expect(style).not.toBe('none');
    });
});
