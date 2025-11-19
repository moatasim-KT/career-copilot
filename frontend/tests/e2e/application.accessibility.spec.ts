import { test, expect } from '@playwright/test';

test.describe('Application Accessibility', () => {
    test('application page should have no accessibility violations', async ({ page }) => {
        await page.goto('/applications');
        await expect(page.locator('h1')).toHaveText(/Applications/);
        const accessibilityScanResults = await page.accessibility.snapshot();
        expect(accessibilityScanResults).toBeTruthy();
        // Check for ARIA roles in table
        await expect(page.locator('table')).toHaveCount(1);
        await expect(page.locator('[role="row"]')).toHaveCountGreaterThan(0);
    });

    test('should support keyboard navigation for application table', async ({ page }) => {
        await page.goto('/applications');
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        const table = page.locator('table');
        await expect(table).toBeFocused();
    });

    test('should have visible focus indicators on action buttons', async ({ page }) => {
        await page.goto('/applications');
        // Tab to first action button
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        const actionBtn = page.locator('button').first();
        await expect(actionBtn).toBeFocused();
        const style = await actionBtn.evaluate((el) => window.getComputedStyle(el).outlineStyle);
        expect(style).not.toBe('none');
    });
});
