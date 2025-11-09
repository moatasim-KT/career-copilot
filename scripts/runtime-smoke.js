const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
    const out = {
        navigated: false,
        status: null,
        title: null,
        console: [],
        requests: [],
        errors: [],
        actions: [],
    };

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    page.on('console', (msg) => {
        try {
            out.console.push({ type: msg.type(), text: msg.text() });
        } catch (e) {
            out.console.push({ type: 'unknown', text: String(msg) });
        }
    });

    page.on('pageerror', (err) => {
        out.errors.push(String(err));
    });

    page.on('request', (req) => {
        out.requests.push({ url: req.url(), method: req.method(), type: req.resourceType(), id: out.requests.length });
    });

    page.on('response', async (res) => {
        try {
            const req = res.request();
            const idx = out.requests.findIndex((r) => r.url === req.url());
            const summary = { status: res.status(), url: res.url(), ok: res.ok() };
            if (idx >= 0) out.requests[idx] = { ...out.requests[idx], response: summary };
            else out.requests.push({ url: res.url(), response: summary });
        } catch (e) {
            out.errors.push('response-capture:' + String(e));
        }
    });

    try {
        const url = process.env.TARGET_URL || 'http://localhost:3000/dashboard';
        const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch((e) => {
            out.errors.push('goto-error:' + String(e));
            return null;
        });
        if (resp) {
            out.navigated = true;
            out.status = resp.status();
            out.title = await page.title().catch(() => null);
        }

        // Wait a little for client JS to hydrate and for potential network activity
        await page.waitForTimeout(1200);

        // Try to click a Refresh button if present
        try {
            const refresh = await page.$('button:has-text("Refresh")');
            if (refresh) {
                await refresh.click();
                out.actions.push('clicked-refresh');
                // wait for some network calls
                await page.waitForTimeout(1200);
            } else {
                out.actions.push('no-refresh-button-found');
            }
        } catch (e) {
            out.errors.push('refresh-click:' + String(e));
        }

        // Collect first meaningful DOM markers
        try {
            const h1 = await page.$('h1, h2');
            out.domHead = h1 ? (await h1.innerText()).slice(0, 300) : null;
        } catch (e) {
            out.errors.push('dom-head:' + String(e));
        }

        // Short snapshot of localStorage and cookies
        try {
            out.cookies = await context.cookies();
            out.localStorage = await page.evaluate(() => {
                const out = {};
                try {
                    for (let i = 0; i < localStorage.length; i++) {
                        const k = localStorage.key(i);
                        out[k] = localStorage.getItem(k);
                    }
                } catch (e) {
                    return { error: String(e) };
                }
                return out;
            });
        } catch (e) {
            out.errors.push('storage-capture:' + String(e));
        }

        // Trim arrays to reasonable size
        out.console = out.console.slice(0, 200);
        out.requests = out.requests.slice(0, 200);

        const json = JSON.stringify(out, null, 2);
        fs.writeFileSync('/tmp/runtime-smoke.json', json);
        console.log(json);
    } catch (e) {
        console.error('fatal:', e);
        process.exitCode = 2;
    } finally {
        try {
            await browser.close();
        } catch (e) {
            // ignore
        }
    }
})();
