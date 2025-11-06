/**
 * Playwright Configuration
 * 
 * Enterprise-grade E2E testing configuration with cross-browser support,
 * parallel execution, and comprehensive reporting.
 * 
 * @see https://playwright.dev/docs/test-configuration
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests/e2e',

    // Maximum time one test can run
    timeout: 30 * 1000,

    // Test execution settings
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,

    // Reporter configuration
    reporter: [
        ['html', { outputFolder: 'playwright-report' }],
        ['json', { outputFile: 'playwright-report/results.json' }],
        ['junit', { outputFile: 'playwright-report/results.xml' }],
        ['list'],
    ],

    // Shared settings
    use: {
        // Base URL for all tests
        baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:3000',

        // Collect trace when retrying failed test
        trace: 'on-first-retry',

        // Screenshot settings
        screenshot: 'only-on-failure',

        // Video settings
        video: 'retain-on-failure',

        // Viewport size
        viewport: { width: 1280, height: 720 },

        // Ignore HTTPS errors
        ignoreHTTPSErrors: true,

        // Action timeout
        actionTimeout: 10 * 1000,

        // Navigation timeout
        navigationTimeout: 30 * 1000,
    },

    // Configure projects for major browsers
    projects: [
        // Desktop browsers
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
        {
            name: 'firefox',
            use: { ...devices['Desktop Firefox'] },
        },
        {
            name: 'webkit',
            use: { ...devices['Desktop Safari'] },
        },

        // Mobile browsers
        {
            name: 'Mobile Chrome',
            use: { ...devices['Pixel 5'] },
        },
        {
            name: 'Mobile Safari',
            use: { ...devices['iPhone 12'] },
        },

        // Tablet
        {
            name: 'iPad',
            use: { ...devices['iPad Pro'] },
        },

        // Microsoft Edge
        {
            name: 'Microsoft Edge',
            use: { ...devices['Desktop Edge'], channel: 'msedge' },
        },

        // Google Chrome
        {
            name: 'Google Chrome',
            use: { ...devices['Desktop Chrome'], channel: 'chrome' },
        },
    ],

    // Web server configuration
    webServer: {
        command: 'npm run dev',
        url: 'http://localhost:3000',
        reuseExistingServer: !process.env.CI,
        timeout: 120 * 1000,
    },

    // Output folder for test artifacts
    outputDir: 'test-results',
});
