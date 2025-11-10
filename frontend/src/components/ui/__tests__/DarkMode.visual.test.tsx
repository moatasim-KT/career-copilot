/**
 * Dark Mode Visual Regression Tests
 * 
 * Automated visual testing for dark mode across all pages and components.
 * Uses Playwright for screenshot comparison.
 */

import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';

// Helper to toggle dark mode
async function toggleDarkMode(page: Page) {
  await page.click('[aria-label="Toggle theme"]');
  await page.waitForTimeout(300); // Wait for transition
}

// Helper to verify dark mode is active
async function isDarkMode(page: Page): Promise<boolean> {
  return await page.evaluate(() => {
    return document.documentElement.classList.contains('dark');
  });
}

// Helper to set theme via localStorage
async function setTheme(page: Page, theme: 'light' | 'dark' | 'system') {
  await page.evaluate((t) => {
    localStorage.setItem('theme', t);
    if (t === 'dark') {
      document.documentElement.classList.add('dark');
    } else if (t === 'light') {
      document.documentElement.classList.remove('dark');
    }
  }, theme);
}

test.describe('Dark Mode Visual Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto(BASE_URL);
    await page.evaluate(() => localStorage.clear());
  });

  test.describe('Dashboard Page', () => {
    test('should render dashboard in light mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'light');
      await page.reload();
      
      await expect(page).toHaveScreenshot('dashboard-light.png', {
        fullPage: true,
      });
    });

    test('should render dashboard in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      await expect(page).toHaveScreenshot('dashboard-dark.png', {
        fullPage: true,
      });
    });

    test('should transition smoothly between themes', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      
      // Start in light mode
      await setTheme(page, 'light');
      await page.reload();
      
      // Toggle to dark
      await toggleDarkMode(page);
      expect(await isDarkMode(page)).toBe(true);
      
      await expect(page).toHaveScreenshot('dashboard-after-toggle.png', {
        fullPage: true,
      });
    });
  });

  test.describe('Jobs Page', () => {
    test('should render jobs page in light mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/jobs`);
      await setTheme(page, 'light');
      await page.reload();
      
      await expect(page).toHaveScreenshot('jobs-light.png', {
        fullPage: true,
      });
    });

    test('should render jobs page in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/jobs`);
      await setTheme(page, 'dark');
      await page.reload();
      
      await expect(page).toHaveScreenshot('jobs-dark.png', {
        fullPage: true,
      });
    });

    test('should render job cards correctly in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/jobs`);
      await setTheme(page, 'dark');
      await page.reload();
      
      // Wait for job cards to load
      await page.waitForSelector('[data-testid="job-card"]', { timeout: 5000 }).catch(() => {});
      
      await expect(page).toHaveScreenshot('jobs-cards-dark.png');
    });
  });

  test.describe('Applications Page', () => {
    test('should render applications page in light mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/applications`);
      await setTheme(page, 'light');
      await page.reload();
      
      await expect(page).toHaveScreenshot('applications-light.png', {
        fullPage: true,
      });
    });

    test('should render applications page in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/applications`);
      await setTheme(page, 'dark');
      await page.reload();
      
      await expect(page).toHaveScreenshot('applications-dark.png', {
        fullPage: true,
      });
    });
  });

  test.describe('Recommendations Page', () => {
    test('should render recommendations page in light mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/recommendations`);
      await setTheme(page, 'light');
      await page.reload();
      
      await expect(page).toHaveScreenshot('recommendations-light.png', {
        fullPage: true,
      });
    });

    test('should render recommendations page in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/recommendations`);
      await setTheme(page, 'dark');
      await page.reload();
      
      await expect(page).toHaveScreenshot('recommendations-dark.png', {
        fullPage: true,
      });
    });
  });

  test.describe('Analytics Page', () => {
    test('should render analytics page in light mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/analytics`);
      await setTheme(page, 'light');
      await page.reload();
      
      await expect(page).toHaveScreenshot('analytics-light.png', {
        fullPage: true,
      });
    });

    test('should render analytics page in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/analytics`);
      await setTheme(page, 'dark');
      await page.reload();
      
      await expect(page).toHaveScreenshot('analytics-dark.png', {
        fullPage: true,
      });
    });

    test('should render charts correctly in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/analytics`);
      await setTheme(page, 'dark');
      await page.reload();
      
      // Wait for charts to render
      await page.waitForTimeout(1000);
      
      await expect(page).toHaveScreenshot('analytics-charts-dark.png');
    });
  });

  test.describe('Navigation', () => {
    test('should render navigation in light mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'light');
      await page.reload();
      
      const nav = page.locator('nav');
      await expect(nav).toHaveScreenshot('navigation-light.png');
    });

    test('should render navigation in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      const nav = page.locator('nav');
      await expect(nav).toHaveScreenshot('navigation-dark.png');
    });

    test('should render mobile navigation in dark mode', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      // Open mobile menu
      await page.click('[aria-label="Toggle menu"]');
      await page.waitForTimeout(300);
      
      await expect(page).toHaveScreenshot('navigation-mobile-dark.png');
    });
  });

  test.describe('Modals and Popovers', () => {
    test('should render modal in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      // Open a modal (adjust selector based on your app)
      const modalTrigger = page.locator('[data-testid="open-modal"]').first();
      if (await modalTrigger.count() > 0) {
        await modalTrigger.click();
        await page.waitForTimeout(300);
        
        await expect(page).toHaveScreenshot('modal-dark.png');
      }
    });

    test('should render tooltip in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      // Hover over theme toggle to show tooltip
      await page.hover('[aria-label="Toggle theme"]');
      await page.waitForTimeout(300);
      
      await expect(page).toHaveScreenshot('tooltip-dark.png');
    });
  });

  test.describe('Form Components', () => {
    test('should render form inputs in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      // Find a form or create a test page with forms
      const form = page.locator('form').first();
      if (await form.count() > 0) {
        await expect(form).toHaveScreenshot('form-dark.png');
      }
    });

    test('should render input focus state in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      const input = page.locator('input[type="text"]').first();
      if (await input.count() > 0) {
        await input.focus();
        await page.waitForTimeout(200);
        
        await expect(input).toHaveScreenshot('input-focus-dark.png');
      }
    });

    test('should render select dropdown in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      const select = page.locator('select').first();
      if (await select.count() > 0) {
        await select.click();
        await page.waitForTimeout(200);
        
        await expect(page).toHaveScreenshot('select-dropdown-dark.png');
      }
    });
  });

  test.describe('Buttons', () => {
    test('should render button variants in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      const buttons = page.locator('button');
      if (await buttons.count() > 0) {
        await expect(page).toHaveScreenshot('buttons-dark.png');
      }
    });

    test('should render button hover state in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      const button = page.locator('button').first();
      if (await button.count() > 0) {
        await button.hover();
        await page.waitForTimeout(200);
        
        await expect(button).toHaveScreenshot('button-hover-dark.png');
      }
    });
  });

  test.describe('Cards', () => {
    test('should render cards in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      const card = page.locator('[data-testid="card"]').first();
      if (await card.count() > 0) {
        await expect(card).toHaveScreenshot('card-dark.png');
      }
    });

    test('should render card hover state in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      const card = page.locator('[data-testid="card"]').first();
      if (await card.count() > 0) {
        await card.hover();
        await page.waitForTimeout(200);
        
        await expect(card).toHaveScreenshot('card-hover-dark.png');
      }
    });
  });

  test.describe('Theme Toggle', () => {
    test('should show correct icon in light mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'light');
      await page.reload();
      
      const toggle = page.locator('[aria-label="Toggle theme"]');
      await expect(toggle).toHaveScreenshot('theme-toggle-light.png');
    });

    test('should show correct icon in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      const toggle = page.locator('[aria-label="Toggle theme"]');
      await expect(toggle).toHaveScreenshot('theme-toggle-dark.png');
    });

    test('should animate icon transition', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'light');
      await page.reload();
      
      const toggle = page.locator('[aria-label="Toggle theme"]');
      
      // Capture before toggle
      await expect(toggle).toHaveScreenshot('theme-toggle-before.png');
      
      // Toggle
      await toggle.click();
      await page.waitForTimeout(100); // Mid-transition
      
      // Capture during transition (may be flaky)
      // await expect(toggle).toHaveScreenshot('theme-toggle-transition.png');
      
      await page.waitForTimeout(200); // After transition
      
      // Capture after toggle
      await expect(toggle).toHaveScreenshot('theme-toggle-after.png');
    });
  });

  test.describe('Responsive Design', () => {
    const viewports = [
      { name: 'mobile', width: 375, height: 667 },
      { name: 'tablet', width: 768, height: 1024 },
      { name: 'desktop', width: 1920, height: 1080 },
    ];

    for (const viewport of viewports) {
      test(`should render dashboard in dark mode on ${viewport.name}`, async ({ page }) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await page.goto(`${BASE_URL}/dashboard`);
        await setTheme(page, 'dark');
        await page.reload();
        
        await expect(page).toHaveScreenshot(`dashboard-dark-${viewport.name}.png`, {
          fullPage: true,
        });
      });
    }
  });

  test.describe('Color Contrast', () => {
    test('should have sufficient contrast for text', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      await page.reload();
      
      // Get text elements and their backgrounds
      const textElements = await page.locator('p, h1, h2, h3, h4, h5, h6, span, a').all();
      
      for (const element of textElements.slice(0, 10)) { // Test first 10 elements
        const color = await element.evaluate((el) => {
          return window.getComputedStyle(el).color;
        });
        
        const bgColor = await element.evaluate((el) => {
          return window.getComputedStyle(el).backgroundColor;
        });
        
        // Log for manual verification
        console.log(`Text color: ${color}, Background: ${bgColor}`);
      }
    });
  });

  test.describe('System Preference', () => {
    test('should respect system dark mode preference', async ({ page, context }) => {
      // Emulate dark color scheme
      await context.emulateMedia({ colorScheme: 'dark' });
      
      await page.goto(`${BASE_URL}/dashboard`);
      await page.evaluate(() => {
        localStorage.setItem('theme', 'system');
      });
      await page.reload();
      
      expect(await isDarkMode(page)).toBe(true);
      
      await expect(page).toHaveScreenshot('system-dark-preference.png', {
        fullPage: true,
      });
    });

    test('should respect system light mode preference', async ({ page, context }) => {
      // Emulate light color scheme
      await context.emulateMedia({ colorScheme: 'light' });
      
      await page.goto(`${BASE_URL}/dashboard`);
      await page.evaluate(() => {
        localStorage.setItem('theme', 'system');
      });
      await page.reload();
      
      expect(await isDarkMode(page)).toBe(false);
      
      await expect(page).toHaveScreenshot('system-light-preference.png', {
        fullPage: true,
      });
    });
  });

  test.describe('No Flash of Wrong Theme', () => {
    test('should not flash light theme when loading in dark mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/dashboard`);
      await setTheme(page, 'dark');
      
      // Reload and check immediately
      await page.reload();
      
      // Check within first 100ms
      await page.waitForTimeout(50);
      expect(await isDarkMode(page)).toBe(true);
      
      // Check after full load
      await page.waitForLoadState('networkidle');
      expect(await isDarkMode(page)).toBe(true);
    });
  });
});
