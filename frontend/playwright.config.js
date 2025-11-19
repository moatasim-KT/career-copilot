// Playwright E2E Testing Configuration
/** @type {import('@playwright/test').PlaywrightTestConfig} */
module.exports = {
    testDir: './tests/e2e',
    timeout: 60000,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: [
        ['html'],
        ['list'],
        process.env.CI ? ['github'] : ['list'],
    ],
    use: {
        baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        headless: true,
    },
    projects: [
        {
            name: 'chromium',
            use: { browserName: 'chromium' },
        },
        {
            name: 'firefox',
            use: { browserName: 'firefox' },
        },
        {
            name: 'webkit',
            use: { browserName: 'webkit' },
        },
    ],
    webServer: {
        command: 'npm run dev',
        port: 3000,
        timeout: 120000,
        reuseExistingServer: !process.env.CI,
    },
};
