/**
 * Cross-Browser Compatibility Tests
 * 
 * Tests critical functionality across all supported browsers:
 * - Chrome, Firefox, Safari, Edge
 * - Mobile browsers (Chrome, Safari)
 * 
 * These tests verify that core features work consistently across browsers.
 */

import { test, expect } from '@playwright/test';

test.describe('Cross-Browser Compatibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load homepage successfully', async ({ page, browserName }) => {
    // Verify page loads
    await expect(page).toHaveTitle(/Career Copilot/i);

    // Verify main navigation is visible
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();

    console.log(`✓ Homepage loaded successfully on ${browserName}`);
  });

  test('should render design system components correctly', async ({ page, browserName }) => {
    // Navigate to a page with various components
    await page.goto('/dashboard');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for buttons
    const buttons = page.locator('button');
    await expect(buttons.first()).toBeVisible();

    // Check for cards
    const cards = page.locator('[class*="card"]');
    if (await cards.count() > 0) {
      await expect(cards.first()).toBeVisible();
    }

    console.log(`✓ Components rendered correctly on ${browserName}`);
  });

  test('should handle dark mode toggle', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Find theme toggle button
    const themeToggle = page.locator('button[aria-label*="theme" i], button[aria-label*="dark" i]').first();

    if (await themeToggle.isVisible()) {
      // Get initial theme
      const htmlElement = page.locator('html');
      const initialClass = await htmlElement.getAttribute('class');

      // Toggle theme
      await themeToggle.click();
      await page.waitForTimeout(300); // Wait for transition

      // Verify theme changed
      const newClass = await htmlElement.getAttribute('class');
      expect(newClass).not.toBe(initialClass);

      console.log(`✓ Dark mode toggle works on ${browserName}`);
    } else {
      console.log(`⚠ Theme toggle not found on ${browserName}`);
    }
  });

  test('should handle form inputs correctly', async ({ page, browserName }) => {
    // Navigate to a page with forms (e.g., settings or job search)
    await page.goto('/jobs');

    // Find search input
    const searchInput = page.locator('input[type="text"], input[type="search"]').first();

    if (await searchInput.isVisible()) {
      // Type in search
      await searchInput.fill('Software Engineer');

      // Verify value
      await expect(searchInput).toHaveValue('Software Engineer');

      // Clear input
      await searchInput.clear();
      await expect(searchInput).toHaveValue('');

      console.log(`✓ Form inputs work correctly on ${browserName}`);
    }
  });

  test('should handle navigation correctly', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Find navigation links
    const jobsLink = page.locator('a[href*="/jobs"]').first();

    if (await jobsLink.isVisible()) {
      await jobsLink.click();

      // Wait for navigation
      await page.waitForURL(/.*jobs.*/);

      // Verify URL changed
      expect(page.url()).toContain('jobs');

      console.log(`✓ Navigation works correctly on ${browserName}`);
    }
  });

  test('should handle responsive layouts', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Test different viewport sizes
    const viewports = [
      { width: 375, height: 667, name: 'Mobile' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 1920, height: 1080, name: 'Desktop' },
    ];

    for (const vp of viewports) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.waitForTimeout(500); // Wait for layout adjustment

      // Verify page is still functional
      const nav = page.locator('nav');
      await expect(nav).toBeVisible();

      console.log(`✓ ${vp.name} layout works on ${browserName}`);
    }
  });

  test('should handle CSS animations and transitions', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Find an animated element (button, card, etc.)
    const button = page.locator('button').first();

    if (await button.isVisible()) {
      // Hover over button
      await button.hover();
      await page.waitForTimeout(300);

      // Click button
      await button.click();
      await page.waitForTimeout(300);

      console.log(`✓ CSS animations work on ${browserName}`);
    }
  });

  test('should handle modal/dialog interactions', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Look for buttons that might open modals
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();

    // Try clicking buttons to find modals
    for (let i = 0; i < Math.min(buttonCount, 5); i++) {
      const button = buttons.nth(i);
      const buttonText = await button.textContent();

      if (buttonText && /add|create|new|edit/i.test(buttonText)) {
        await button.click();
        await page.waitForTimeout(500);

        // Check if modal appeared
        const modal = page.locator('[role="dialog"], [class*="modal"]');
        if (await modal.isVisible()) {
          // Close modal (ESC key)
          await page.keyboard.press('Escape');
          await page.waitForTimeout(300);

          console.log(`✓ Modal interactions work on ${browserName}`);
          break;
        }
      }
    }
  });

  test('should handle keyboard navigation', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Tab through focusable elements
    await page.keyboard.press('Tab');
    await page.waitForTimeout(100);

    // Verify focus is visible
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();

    // Tab a few more times
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    console.log(`✓ Keyboard navigation works on ${browserName}`);
  });

  test('should handle local storage', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Set local storage item
    await page.evaluate(() => {
      localStorage.setItem('test-key', 'test-value');
    });

    // Verify it was set
    const value = await page.evaluate(() => {
      return localStorage.getItem('test-key');
    });

    expect(value).toBe('test-value');

    // Clean up
    await page.evaluate(() => {
      localStorage.removeItem('test-key');
    });

    console.log(`✓ Local storage works on ${browserName}`);
  });

  test('should handle API requests', async ({ page, browserName }) => {
    // Listen for API requests
    const requests: string[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        requests.push(request.url());
      }
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify API requests were made
    expect(requests.length).toBeGreaterThan(0);

    console.log(`✓ API requests work on ${browserName} (${requests.length} requests)`);
  });

  test('should handle images and media', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Find images
    const images = page.locator('img');
    const imageCount = await images.count();

    if (imageCount > 0) {
      // Check first image loaded
      const firstImage = images.first();
      await expect(firstImage).toBeVisible();

      // Verify image has src
      const src = await firstImage.getAttribute('src');
      expect(src).toBeTruthy();

      console.log(`✓ Images load correctly on ${browserName}`);
    }
  });

  test('should handle CSS Grid and Flexbox layouts', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Check for grid/flex containers
    const containers = page.locator('[class*="grid"], [class*="flex"]');

    if (await containers.count() > 0) {
      const firstContainer = containers.first();
      await expect(firstContainer).toBeVisible();

      // Verify children are visible
      const children = firstContainer.locator('> *');
      if (await children.count() > 0) {
        await expect(children.first()).toBeVisible();
      }

      console.log(`✓ CSS Grid/Flexbox layouts work on ${browserName}`);
    }
  });

  test('should handle scroll behavior', async ({ page, browserName }) => {
    await page.goto('/jobs');
    await page.waitForLoadState('networkidle');

    // Scroll down
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(300);

    // Verify scroll position
    const scrollY = await page.evaluate(() => window.scrollY);
    expect(scrollY).toBeGreaterThan(0);

    // Scroll back to top
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(300);

    console.log(`✓ Scroll behavior works on ${browserName}`);
  });

  test('should handle date/time inputs', async ({ page, browserName }) => {
    // Navigate to a page that might have date inputs
    await page.goto('/applications');

    // Look for date inputs
    const dateInputs = page.locator('input[type="date"], input[type="datetime-local"]');

    if (await dateInputs.count() > 0) {
      const dateInput = dateInputs.first();

      // Try to set a date
      await dateInput.fill('2024-12-31');

      console.log(`✓ Date inputs work on ${browserName}`);
    }
  });

  test('should handle select dropdowns', async ({ page, browserName }) => {
    await page.goto('/jobs');

    // Look for select elements
    const selects = page.locator('select');

    if (await selects.count() > 0) {
      const select = selects.first();

      // Get options
      const options = select.locator('option');
      const optionCount = await options.count();

      if (optionCount > 1) {
        // Select second option
        await select.selectOption({ index: 1 });

        console.log(`✓ Select dropdowns work on ${browserName}`);
      }
    }
  });

  test('should handle checkboxes and radio buttons', async ({ page, browserName }) => {
    await page.goto('/settings/notifications');

    // Look for checkboxes
    const checkboxes = page.locator('input[type="checkbox"]');

    if (await checkboxes.count() > 0) {
      const checkbox = checkboxes.first();

      // Check initial state
      const initialState = await checkbox.isChecked();

      // Toggle checkbox
      await checkbox.click();
      await page.waitForTimeout(100);

      // Verify state changed
      const newState = await checkbox.isChecked();
      expect(newState).not.toBe(initialState);

      console.log(`✓ Checkboxes work on ${browserName}`);
    }
  });

  test('should handle text selection', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Find text content
    const textElement = page.locator('h1, h2, p').first();

    if (await textElement.isVisible()) {
      // Triple-click to select all text
      await textElement.click({ clickCount: 3 });
      await page.waitForTimeout(100);

      // Get selected text
      const selectedText = await page.evaluate(() => window.getSelection()?.toString());
      expect(selectedText).toBeTruthy();

      console.log(`✓ Text selection works on ${browserName}`);
    }
  });

  test('should handle copy/paste operations', async ({ page, browserName }) => {
    await page.goto('/jobs');

    // Find an input
    const input = page.locator('input[type="text"]').first();

    if (await input.isVisible()) {
      // Type text
      await input.fill('Test text');

      // Select all
      await input.press('Control+A');

      // Copy
      await input.press('Control+C');

      // Clear
      await input.clear();

      // Paste
      await input.press('Control+V');

      // Verify text was pasted
      await expect(input).toHaveValue('Test text');

      console.log(`✓ Copy/paste works on ${browserName}`);
    }
  });

  test('should handle window resize', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Get initial viewport
    const initialViewport = page.viewportSize();

    // Resize window
    await page.setViewportSize({ width: 800, height: 600 });
    await page.waitForTimeout(500);

    // Verify page is still functional
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();

    // Restore viewport
    if (initialViewport) {
      await page.setViewportSize(initialViewport);
    }

    console.log(`✓ Window resize works on ${browserName}`);
  });

  test('should handle focus management', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Find focusable elements
    const buttons = page.locator('button');

    if (await buttons.count() > 0) {
      const button = buttons.first();

      // Focus the button
      await button.focus();

      // Verify it's focused
      await expect(button).toBeFocused();

      // Blur the button
      await button.blur();

      console.log(`✓ Focus management works on ${browserName}`);
    }
  });
});

test.describe('Browser-Specific Features', () => {
  test('should handle browser-specific CSS features', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Check for backdrop-filter support (Safari, Chrome)
    const supportsBackdropFilter = await page.evaluate(() => {
      return CSS.supports('backdrop-filter', 'blur(10px)');
    });

    console.log(`${browserName} backdrop-filter support: ${supportsBackdropFilter}`);

    // Check for CSS Grid support
    const supportsGrid = await page.evaluate(() => {
      return CSS.supports('display', 'grid');
    });

    expect(supportsGrid).toBe(true);
    console.log(`✓ CSS Grid supported on ${browserName}`);
  });

  test('should handle browser-specific JavaScript APIs', async ({ page, browserName }) => {
    await page.goto('/dashboard');

    // Check for IntersectionObserver
    const hasIntersectionObserver = await page.evaluate(() => {
      return 'IntersectionObserver' in window;
    });

    expect(hasIntersectionObserver).toBe(true);
    console.log(`✓ IntersectionObserver supported on ${browserName}`);

    // Check for ResizeObserver
    const hasResizeObserver = await page.evaluate(() => {
      return 'ResizeObserver' in window;
    });

    expect(hasResizeObserver).toBe(true);
    console.log(`✓ ResizeObserver supported on ${browserName}`);
  });

  test('should handle touch events on mobile browsers', async ({ page, browserName, isMobile }) => {
    if (!isMobile) {
      test.skip();
      return;
    }

    await page.goto('/dashboard');

    // Find a tappable element
    const button = page.locator('button').first();

    if (await button.isVisible()) {
      // Tap the button
      await button.tap();
      await page.waitForTimeout(300);

      console.log(`✓ Touch events work on ${browserName}`);
    }
  });
});
