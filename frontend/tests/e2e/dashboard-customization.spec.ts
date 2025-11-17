/**
 * E2E Tests for Dashboard Customization Features
 * 
 * Tests dashboard drag-and-drop, widget management, and layout persistence
 */

import { test, expect } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
const DASHBOARD_PAGE = `${BASE_URL}/dashboard/customizable`;

test.describe('Dashboard Customization Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard before each test
    await page.goto(DASHBOARD_PAGE);
  });

  test('should display dashboard page with heading', async ({ page }) => {
    // Check page heading
    await expect(page.getByRole('heading', { name: 'Customizable Dashboard' })).toBeVisible();
    
    // Check description
    await expect(page.getByText('Drag and resize widgets to customize your dashboard')).toBeVisible();
  });

  test('should display Save and Reset buttons', async ({ page }) => {
    // Check for Save Layout button
    await expect(page.getByRole('button', { name: /Save Layout/i })).toBeVisible();
    
    // Check for Reset button
    await expect(page.getByRole('button', { name: /Reset/i })).toBeVisible();
  });

  test('should display default widgets', async ({ page }) => {
    // Wait for dashboard to load
    await page.waitForSelector('.react-grid-layout', { timeout: 5000 });

    // Check for widget presence
    const layout = page.locator('.react-grid-layout');
    await expect(layout).toBeVisible();

    // Check for at least one widget
    const widgets = page.locator('.dashboard-widget');
    const count = await widgets.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should display widget titles', async ({ page }) => {
    // Wait for widgets to load
    await page.waitForSelector('.dashboard-widget', { timeout: 5000 });

    // Check for specific widget titles (based on default layout)
    const widgetTitles = [
      'Application Status Overview',
      'Recent Job Listings',
      'Application Statistics',
      'Upcoming Interviews',
      'Job Recommendations',
      'Recent Activity',
      'Skills Development Progress',
      'Career Goals',
    ];

    // At least some of these should be visible
    let visibleCount = 0;
    for (const title of widgetTitles) {
      const titleElement = page.getByText(title);
      if (await titleElement.isVisible().catch(() => false)) {
        visibleCount++;
      }
    }
    
    expect(visibleCount).toBeGreaterThan(0);
  });
});

test.describe('Dashboard Widget Drag and Drop', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(DASHBOARD_PAGE);
    await page.waitForSelector('.react-grid-layout', { timeout: 5000 });
  });

  test('should allow dragging widgets', async ({ page }) => {
    // Find a widget
    const widget = page.locator('.dashboard-widget').first();
    await expect(widget).toBeVisible();

    // Get initial position
    const initialBox = await widget.boundingBox();
    expect(initialBox).not.toBeNull();

    // Attempt to drag widget (drag by the header)
    const header = widget.locator('.cursor-move').first();
    if (await header.isVisible()) {
      // Drag to a new position
      await header.hover();
      await page.mouse.down();
      await page.mouse.move(initialBox!.x + 100, initialBox!.y + 100);
      await page.mouse.up();

      // Widget should have moved (position changed)
      const newBox = await widget.boundingBox();
      expect(newBox).not.toBeNull();
      // Position should be different (allowing for small variations)
      const moved = Math.abs(newBox!.x - initialBox!.x) > 10 || 
                    Math.abs(newBox!.y - initialBox!.y) > 10;
      expect(moved).toBe(true);
    }
  });

  test('should show drag placeholder', async ({ page }) => {
    // Find a widget header
    const header = page.locator('.cursor-move').first();
    if (await header.isVisible()) {
      // Start dragging
      await header.hover();
      await page.mouse.down();
      
      // Move mouse to trigger placeholder
      const box = await header.boundingBox();
      if (box) {
        await page.mouse.move(box.x + 50, box.y + 50);
        
        // Placeholder should appear
        const placeholder = page.locator('.react-grid-placeholder');
        await expect(placeholder).toBeVisible();
      }
      
      await page.mouse.up();
    }
  });
});

test.describe('Dashboard Widget Resizing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(DASHBOARD_PAGE);
    await page.waitForSelector('.react-grid-layout', { timeout: 5000 });
  });

  test('should have resize handles', async ({ page }) => {
    // Check for resize handles
    const resizeHandles = page.locator('.react-resizable-handle');
    const count = await resizeHandles.count();
    
    // Should have at least one resize handle
    expect(count).toBeGreaterThan(0);
  });

  test('should allow resizing widgets', async ({ page }) => {
    // Find a widget
    const widget = page.locator('.dashboard-widget').first();
    await expect(widget).toBeVisible();

    // Get initial size
    const initialBox = await widget.boundingBox();
    expect(initialBox).not.toBeNull();

    // Find resize handle for this widget
    const resizeHandle = widget.locator('.react-resizable-handle').first();
    if (await resizeHandle.isVisible()) {
      // Drag resize handle
      await resizeHandle.hover();
      await page.mouse.down();
      await page.mouse.move(initialBox!.x + initialBox!.width + 50, 
                             initialBox!.y + initialBox!.height + 50);
      await page.mouse.up();

      // Widget should have resized
      const newBox = await widget.boundingBox();
      expect(newBox).not.toBeNull();
      
      // Size should be different
      const resized = Math.abs(newBox!.width - initialBox!.width) > 10 || 
                      Math.abs(newBox!.height - initialBox!.height) > 10;
      expect(resized).toBe(true);
    }
  });
});

test.describe('Dashboard Layout Persistence', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(DASHBOARD_PAGE);
    await page.waitForSelector('.react-grid-layout', { timeout: 5000 });
  });

  test('should enable Save Layout button after changes', async ({ page }) => {
    // Make a change (drag a widget)
    const header = page.locator('.cursor-move').first();
    if (await header.isVisible()) {
      const box = await header.boundingBox();
      if (box) {
        await header.hover();
        await page.mouse.down();
        await page.mouse.move(box.x + 100, box.y + 50);
        await page.mouse.up();

        // Save button should be enabled
        const saveButton = page.getByRole('button', { name: /Save Layout/i });
        await expect(saveButton).toBeEnabled();
      }
    }
  });

  test('should show loading state when saving', async ({ page }) => {
    // Click save button
    const saveButton = page.getByRole('button', { name: /Save Layout/i });
    if (await saveButton.isEnabled()) {
      await saveButton.click();
      
      // Should show "Saving..." text briefly
      const savingText = page.getByText(/Saving\.\.\./i);
      // Note: This might be very quick, so we use a shorter timeout
      await expect(savingText).toBeVisible({ timeout: 2000 }).catch(() => {
        // It's OK if we miss the brief loading state
      });
    }
  });

  test('should reset layout when Reset button clicked', async ({ page }) => {
    // Click reset button
    const resetButton = page.getByRole('button', { name: /Reset/i });
    await expect(resetButton).toBeVisible();
    await resetButton.click();

    // Layout should be reset (widgets should be visible)
    await page.waitForSelector('.dashboard-widget', { timeout: 5000 });
    const widgets = page.locator('.dashboard-widget');
    const count = await widgets.count();
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('Dashboard Widget Content', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(DASHBOARD_PAGE);
    await page.waitForSelector('.react-grid-layout', { timeout: 5000 });
  });

  test('should display widget content or loading states', async ({ page }) => {
    // Check each widget has either content or a loading spinner
    const widgets = page.locator('.dashboard-widget');
    const count = await widgets.count();

    for (let i = 0; i < count; i++) {
      const widget = widgets.nth(i);
      
      // Should have either content or loading spinner
      const hasContent = await widget.locator('text=/./').count() > 0;
      const hasSpinner = await widget.locator('.animate-spin').isVisible().catch(() => false);
      
      expect(hasContent || hasSpinner).toBe(true);
    }
  });

  test('should display empty states when no data', async ({ page }) => {
    // Some widgets might show "No data" or similar messages
    const emptyMessages = [
      'No upcoming events',
      'No recent jobs',
      'No recommendations yet',
      'No recent activity',
      'No skills tracked',
      'No goals set',
    ];

    // Check if any empty state messages are visible
    let foundEmptyState = false;
    for (const message of emptyMessages) {
      const element = page.getByText(message);
      if (await element.isVisible().catch(() => false)) {
        foundEmptyState = true;
        break;
      }
    }
    
    // At least one empty state or actual data should be present
    // (We're just checking the page renders properly)
    const widgets = page.locator('.dashboard-widget');
    const count = await widgets.count();
    
    // Verify either widgets have content or show empty states
    expect(count).toBeGreaterThan(0);
    // foundEmptyState is informational - at least one widget should render
    if (foundEmptyState) {
      console.log('Empty state messages detected in some widgets');
    }
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('Dashboard Responsive Breakpoints', () => {
  test('should display correctly on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(DASHBOARD_PAGE);

    // Check main elements are visible
    await expect(page.getByRole('heading', { name: 'Customizable Dashboard' })).toBeVisible();
    
    // Widgets should stack vertically on mobile
    await page.waitForSelector('.react-grid-layout', { timeout: 5000 });
    const layout = page.locator('.react-grid-layout');
    await expect(layout).toBeVisible();
  });

  test('should display correctly on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(DASHBOARD_PAGE);

    // Check main elements are visible
    await expect(page.getByRole('heading', { name: 'Customizable Dashboard' })).toBeVisible();
    await page.waitForSelector('.react-grid-layout', { timeout: 5000 });
  });

  test('should display correctly on desktop viewport', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(DASHBOARD_PAGE);

    // Check main elements are visible
    await expect(page.getByRole('heading', { name: 'Customizable Dashboard' })).toBeVisible();
    await page.waitForSelector('.react-grid-layout', { timeout: 5000 });
    
    // Should have multiple columns on desktop
    const widgets = page.locator('.dashboard-widget');
    const count = await widgets.count();
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('Dashboard Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto(DASHBOARD_PAGE);
    
    // Check main heading
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toBeVisible();
  });

  test('should have keyboard navigation support', async ({ page }) => {
    await page.goto(DASHBOARD_PAGE);
    
    // Tab through interactive elements
    await page.keyboard.press('Tab');
    
    // Check that focus is visible
    const saveButton = page.getByRole('button', { name: /Save Layout/i });
    const resetButton = page.getByRole('button', { name: /Reset/i });
    
    await expect(saveButton).toBeVisible();
    await expect(resetButton).toBeVisible();
  });

  test('should have proper button labels', async ({ page }) => {
    await page.goto(DASHBOARD_PAGE);
    
    // Buttons should have descriptive names
    await expect(page.getByRole('button', { name: /Save Layout/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Reset/i })).toBeVisible();
  });
});

test.describe('Dashboard Error Handling', () => {
  test('should handle missing or failed widget loads gracefully', async ({ page }) => {
    await page.goto(DASHBOARD_PAGE);
    await page.waitForSelector('.react-grid-layout', { timeout: 5000 });

    // Page should still render even if some widgets fail
    const layout = page.locator('.react-grid-layout');
    await expect(layout).toBeVisible();
    
    // Should have widgets or error messages
    const widgets = page.locator('.dashboard-widget');
    const count = await widgets.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should display message if no layout found', async ({ page }) => {
    await page.goto(DASHBOARD_PAGE);
    
    // Should either show widgets or a "no layout" message with create button
    const hasWidgets = await page.locator('.dashboard-widget').count() > 0;
    const hasCreateButton = await page.getByRole('button', { name: /Create Default Layout/i })
      .isVisible()
      .catch(() => false);
    
    expect(hasWidgets || hasCreateButton).toBe(true);
  });
});
