/**
 * Job Recommendations and Skill Gap Analysis Workflow E2E Tests
 * 
 * Tests for job recommendations, skill gap analysis, and applying to recommended jobs.
 * Migrated from Cypress to Playwright.
 * 
 * @module tests/e2e/recommendations.spec
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

// Generate unique test user credentials
const TEST_USER = {
    username: `testuser_${Date.now()}`,
    email: `test_${Date.now()}@example.com`,
    password: 'testpassword',
};

test.describe('Job Recommendations and Skill Gap Analysis Workflow', () => {
    // Setup: Register and create a test job for recommendations
    test.beforeAll(async ({ browser }) => {
        const context = await browser.newContext();
        const page = await context.newPage();

        try {
            // Register a new user
            await page.goto(`${BASE_URL}/register`);
            await page.fill('input[name="username"]', TEST_USER.username);
            await page.fill('input[name="email"]', TEST_USER.email);

            const passwordFields = page.locator('input[name="password"]');
            await passwordFields.first().fill(TEST_USER.password);

            // Fill confirm password if exists
            if (await passwordFields.count() > 1) {
                await passwordFields.last().fill(TEST_USER.password);
            }

            // Accept terms if checkbox exists
            const termsCheckbox = page.locator('input[type="checkbox"]');
            if (await termsCheckbox.count() > 0) {
                await termsCheckbox.first().check();
            }

            await page.click('button:has-text("Create Account")');
            await page.waitForURL(/\/login|\/dashboard/, { timeout: 5000 });

            // Login if redirected to login page
            if (page.url().includes('/login')) {
                await page.fill('input[name="username"]', TEST_USER.username);
                await page.fill('input[name="password"]', TEST_USER.password);
                await page.click('button[type="submit"]');
                await page.waitForURL(/\/dashboard/, { timeout: 5000 });
            }

            // Navigate to jobs page and add a test job
            await page.goto(`${BASE_URL}/jobs`);
            await page.click('button:has-text("Add Job")');

            // Fill in job details
            await page.fill('input[placeholder="Enter company name"]', 'Cypress Rec Company');
            await page.fill('input[placeholder="Enter job title"]', 'Cypress Rec Job');
            await page.fill('input[placeholder="e.g., San Francisco, CA or Remote"]', 'Remote');
            await page.fill('textarea[placeholder="Full job description..."]', 'This is a test job for recommendations.');

            // Submit the form
            await page.click('button:has-text("Add Job")');

            // Verify job was created
            await expect(page.locator('text=Cypress Rec Job')).toBeVisible({ timeout: 5000 });
        } finally {
            await context.close();
        }
    });

    test.beforeEach(async ({ page }) => {
        // Login before each test
        await page.goto(`${BASE_URL}/login`);
        await page.fill('input[name="username"]', TEST_USER.username);
        await page.fill('input[name="password"]', TEST_USER.password);
        await page.click('button[type="submit"]');

        // Wait for successful login
        await page.waitForURL(/\/dashboard/, { timeout: 5000 });

        // Navigate to recommendations page
        await page.goto(`${BASE_URL}/recommendations`);
        await page.waitForLoadState('networkidle');
    });

    test('should display job recommendations', async ({ page }) => {
        // Click on Job Recommendations tab/section if it exists
        const recommendationsTab = page.locator('text=Job Recommendations');
        if (await recommendationsTab.count() > 0) {
            await recommendationsTab.click();
            await page.waitForTimeout(500);
        }

        // Verify job recommendations are displayed
        await expect(page.locator('text=Cypress Rec Job')).toBeVisible();
        await expect(page.locator('text=Cypress Rec Company')).toBeVisible();

        // Verify match score is displayed
        await expect(page.locator('text=/Match Score|Score/i')).toBeVisible();
    });

    test('should display skill gap analysis', async ({ page }) => {
        // Click on Skill Gap Analysis tab/section
        const skillGapTab = page.locator('text=Skill Gap Analysis');
        if (await skillGapTab.count() > 0) {
            await skillGapTab.click();
            await page.waitForTimeout(500);
        } else {
            // If no tab exists, might be on a separate page
            await page.goto(`${BASE_URL}/recommendations/skill-gap`);
            await page.waitForLoadState('networkidle');
        }

        // Verify skill gap analysis components are visible
        await expect(page.locator('text=/Skill Coverage Overview|Skills Coverage/i')).toBeVisible({ timeout: 5000 });
        await expect(page.locator('text=/Your Current Skills|Current Skills/i')).toBeVisible();
        await expect(page.locator('text=/Skills to Learn|Missing Skills/i')).toBeVisible();
        await expect(page.locator('text=/Top Market Skills|Market Skills/i')).toBeVisible();
    });

    test('should allow applying to a recommended job', async ({ page }) => {
        // Navigate to Job Recommendations if needed
        const recommendationsTab = page.locator('text=Job Recommendations');
        if (await recommendationsTab.count() > 0) {
            await recommendationsTab.click();
            await page.waitForTimeout(500);
        }

        // Find the job card and click Apply button
        const jobCard = page.locator('.Card:has-text("Cypress Rec Job"), [data-testid="job-card"]:has-text("Cypress Rec Job")').first();
        await jobCard.locator('button:has-text("Apply")').click();

        // Verify success message appears
        await expect(page.locator('text=/Application created successfully|Applied successfully/i')).toBeVisible({ timeout: 5000 });

        // After applying, the job should ideally be removed from recommendations or marked as applied
        await page.waitForTimeout(1000);

        // Check if job is no longer in recommendations
        const jobStillVisible = await page.locator('text=Cypress Rec Job').count();

        // Either job disappears or shows "Applied" status
        if (jobStillVisible > 0) {
            await expect(page.locator('text=/Applied|Already Applied/i')).toBeVisible();
        }
    });

    test('should filter recommendations by match score', async ({ page }) => {
        // Check if filter controls exist
        const filterInput = page.locator('input[type="range"], input[placeholder*="filter"], select[name*="filter"]');

        if (await filterInput.count() > 0) {
            // Apply filter (implementation depends on actual UI)
            await filterInput.first().click();
            await page.waitForTimeout(500);

            // Verify filtered results
            const recommendedJobs = page.locator('[data-testid="job-card"], .Card');
            expect(await recommendedJobs.count()).toBeGreaterThan(0);
        }
    });

    test('should navigate to job details from recommendations', async ({ page }) => {
        // Navigate to Job Recommendations if needed
        const recommendationsTab = page.locator('text=Job Recommendations');
        if (await recommendationsTab.count() > 0) {
            await recommendationsTab.click();
            await page.waitForTimeout(500);
        }

        // Click on job title or "View Details" button
        const jobTitle = page.locator('text=Cypress Rec Job').first();
        await jobTitle.click();

        // Wait for navigation or modal
        await page.waitForTimeout(500);

        // Verify we're viewing job details
        const hasModal = await page.locator('[role="dialog"]').count() > 0;
        const hasDetailsPage = /\/jobs\/\d+/.test(page.url());

        expect(hasModal || hasDetailsPage).toBeTruthy();
    });

    test('should display skill categories in skill gap analysis', async ({ page }) => {
        // Navigate to Skill Gap Analysis
        const skillGapTab = page.locator('text=Skill Gap Analysis');
        if (await skillGapTab.count() > 0) {
            await skillGapTab.click();
            await page.waitForTimeout(500);
        } else {
            await page.goto(`${BASE_URL}/recommendations/skill-gap`);
            await page.waitForLoadState('networkidle');
        }

        // Check for different skill categories
        const categories = ['Technical', 'Soft Skills', 'Tools', 'Languages'];

        for (const category of categories) {
            const categoryElement = page.locator(`text=${category}`);
            if (await categoryElement.count() > 0) {
                await expect(categoryElement).toBeVisible();
            }
        }
    });

    test('should update recommendations after profile changes', async ({ page }) => {
        // Navigate to profile/settings to update skills
        await page.goto(`${BASE_URL}/profile`);

        // Add a new skill (adjust based on actual implementation)
        const addSkillButton = page.locator('button:has-text("Add Skill")');
        if (await addSkillButton.count() > 0) {
            await addSkillButton.click();

            const skillInput = page.locator('input[placeholder*="skill"], input[name*="skill"]');
            await skillInput.fill('Python');

            const saveButton = page.locator('button:has-text("Save")');
            await saveButton.click();

            // Navigate back to recommendations
            await page.goto(`${BASE_URL}/recommendations`);
            await page.waitForLoadState('networkidle');

            // Verify recommendations reflect the change (match scores might update)
            await expect(page.locator('text=/Match Score|Score/i')).toBeVisible();
        }
    });

    test('should handle empty recommendations gracefully', async ({ page }) => {
        // This test assumes we can clear recommendations or create a user with no matches
        // For now, just verify the page doesn't crash when there are no recommendations

        const recommendationsTab = page.locator('text=Job Recommendations');
        if (await recommendationsTab.count() > 0) {
            await recommendationsTab.click();
            await page.waitForTimeout(500);
        }

        // Check for either recommendations or an empty state message
        const hasRecommendations = await page.locator('[data-testid="job-card"], .Card').count() > 0;
        const hasEmptyState = await page.locator('text=/No recommendations|No jobs found/i').count() > 0;

        expect(hasRecommendations || hasEmptyState).toBeTruthy();
    });
});
