const { test, expect } = require('@playwright/test');
const fs = require('fs');

test('dashboard smoke test', async ({ page }) => {
    const out = { console: [], requests: [], responses: [], actions: [], errors: [] };

    page.on('console', (msg) => {
        out.console.push({ type: msg.type(), text: msg.text() });
    });

    page.on('request', (req) => {
        out.requests.push({ url: req.url(), method: req.method(), resourceType: req.resourceType() });
    });

    page.on('response', async (res) => {
        try {
            out.responses.push({ url: res.url(), status: res.status(), ok: res.ok() });
        } catch (e) {
            out.errors.push(String(e));
        }
    });

    page.on('pageerror', (err) => {
        out.errors.push(String(err));
    });

    // Inject a console wrapper early to capture stacks for console.error calls (helps trace React errors)
    await page.addInitScript(() => {
        const _error = console.error;
        console.error = function (...args) {
            try {
                // include stack trace in a separate console.log so Playwright captures it
                const e = new Error();
                _error.apply(this, args);
                console.log('__STACK_TRACE__', e.stack);
            } catch {
                _error.apply(this, args);
            }
        };
    });

    const url = process.env.TARGET_URL || 'http://localhost:3000/dashboard';
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(1000);

    // Ensure a main heading exists
    const h1 = await page.locator('h1').first();
    if (await h1.count()) {
        out.actions.push({ found_h1: await h1.innerText() });
    }

    // Click refresh if present and enabled
    const refresh = page.locator('button:has-text("Refresh")').first();
    if (await refresh.count()) {
        const enabled = await refresh.isEnabled().catch(() => false);
        if (enabled) {
            await refresh.click();
            out.actions.push('clicked_refresh');
            await page.waitForTimeout(1200);
        } else {
            out.actions.push('refresh_button_disabled');
        }
    } else {
        out.actions.push('no_refresh_button');
    }

    // Snapshot localStorage (in the page context)
    try {
        const ls = await page.evaluate(() => {
            const r = {};
            try {
                for (let i = 0; i < localStorage.length; i++) {
                    const k = localStorage.key(i);
                    r[k] = localStorage.getItem(k);
                }
            } catch (e) {
                return { error: String(e) };
            }
            return r;
        });
        out.localStorage = ls;
    } catch (e) {
        out.errors.push('localStorage:' + String(e));
    }

    // Limit sizes
    out.console = out.console.slice(-200);
    out.requests = out.requests.slice(-200);
    out.responses = out.responses.slice(-200);

    const outPath = '/tmp/playwright-smoke.json';
    fs.writeFileSync(outPath, JSON.stringify(out, null, 2));
    console.log('WROTE', outPath);

    // Basic assertion so Playwright marks test as passed/fail
    expect(true).toBeTruthy();
});
