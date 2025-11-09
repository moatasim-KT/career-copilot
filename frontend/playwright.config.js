// Minimal Playwright config to run smoke test
/** @type {import('@playwright/test').PlaywrightTestConfig} */
module.exports = {
    timeout: 60000,
    use: {
        headless: true,
    },
    projects: [
        {
            name: 'chromium',
            use: { browserName: 'chromium' },
        },
    ],
};
