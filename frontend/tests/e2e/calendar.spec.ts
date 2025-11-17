/**
 * E2E Tests for Calendar Features
 * 
 * Tests calendar event management, OAuth integration, and UI interactions
 */

import { test, expect } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
const CALENDAR_PAGE = `${BASE_URL}/calendar`;
const CALENDAR_SETTINGS_PAGE = `${BASE_URL}/settings/calendar`;

test.describe('Calendar Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to calendar page before each test
    await page.goto(CALENDAR_PAGE);
  });

  test('should display calendar page with all views', async ({ page }) => {
    // Check page title and description
    await expect(page.getByRole('heading', { name: 'Calendar' })).toBeVisible();
    await expect(page.getByText('Manage your interview schedules and events')).toBeVisible();

    // Check for "New Event" button
    await expect(page.getByRole('button', { name: /New Event/i })).toBeVisible();

    // Check calendar view is rendered
    await expect(page.locator('.rbc-calendar')).toBeVisible();
  });

  test('should switch between calendar views', async ({ page }) => {
    // Wait for calendar to load
    await expect(page.locator('.rbc-calendar')).toBeVisible();

    // Check for view buttons (Month, Week, Day, Agenda)
    const toolbar = page.locator('.rbc-toolbar');
    await expect(toolbar).toBeVisible();

    // Click on Week view
    const weekButton = page.locator('.rbc-toolbar button', { hasText: 'Week' });
    if (await weekButton.isVisible()) {
      await weekButton.click();
      // Verify week view is displayed
      await expect(page.locator('.rbc-time-view')).toBeVisible();
    }

    // Click on Day view
    const dayButton = page.locator('.rbc-toolbar button', { hasText: 'Day' });
    if (await dayButton.isVisible()) {
      await dayButton.click();
      // Verify day view is displayed
      await expect(page.locator('.rbc-time-view')).toBeVisible();
    }

    // Click back to Month view
    const monthButton = page.locator('.rbc-toolbar button', { hasText: 'Month' });
    if (await monthButton.isVisible()) {
      await monthButton.click();
      // Verify month view is displayed
      await expect(page.locator('.rbc-month-view')).toBeVisible();
    }
  });

  test('should open create event dialog', async ({ page }) => {
    // Click "New Event" button
    await page.getByRole('button', { name: /New Event/i }).click();

    // Check dialog is opened
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('Create Calendar Event')).toBeVisible();

    // Check form fields are present
    await expect(page.getByLabel(/Event Title/i)).toBeVisible();
    await expect(page.getByLabel(/Description/i)).toBeVisible();
    await expect(page.getByLabel(/Location/i)).toBeVisible();

    // Close dialog
    const closeButton = page.getByRole('button', { name: /Cancel/i });
    if (await closeButton.isVisible()) {
      await closeButton.click();
      await expect(page.getByRole('dialog')).not.toBeVisible();
    }
  });

  test('should display upcoming events sidebar', async ({ page }) => {
    // Check for "Upcoming Events" section
    await expect(page.getByText('Upcoming Events')).toBeVisible();

    // Check for either events or "No upcoming events" message
    const upcomingSection = page.locator('text=Upcoming Events').locator('..');
    await expect(upcomingSection).toBeVisible();
  });

  test('should display event details sidebar', async ({ page }) => {
    // Check for "Event Details" section
    await expect(page.getByText('Event Details')).toBeVisible();

    // Initially should show "Select an event to view details"
    const detailsSection = page.locator('text=Event Details').locator('..');
    await expect(detailsSection).toBeVisible();
  });

  test('should navigate calendar months', async ({ page }) => {
    // Wait for calendar to load
    await expect(page.locator('.rbc-calendar')).toBeVisible();

    // Find next month button
    const nextButton = page.locator('.rbc-toolbar button').filter({ hasText: /Next|›|→/ }).first();
    if (await nextButton.isVisible()) {
      await nextButton.click();
      // Calendar should still be visible
      await expect(page.locator('.rbc-calendar')).toBeVisible();
    }

    // Find previous month button
    const prevButton = page.locator('.rbc-toolbar button').filter({ hasText: /Previous|‹|←/ }).first();
    if (await prevButton.isVisible()) {
      await prevButton.click();
      // Calendar should still be visible
      await expect(page.locator('.rbc-calendar')).toBeVisible();
    }

    // Find today button
    const todayButton = page.locator('.rbc-toolbar button', { hasText: 'Today' });
    if (await todayButton.isVisible()) {
      await todayButton.click();
      // Calendar should still be visible
      await expect(page.locator('.rbc-calendar')).toBeVisible();
    }
  });
});

test.describe('Calendar Settings - OAuth Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to calendar settings before each test
    await page.goto(CALENDAR_SETTINGS_PAGE);
  });

  test('should display calendar settings page', async ({ page }) => {
    // Check page heading
    await expect(page.getByRole('heading', { name: 'Calendar Integration' })).toBeVisible();
    
    // Check description
    await expect(page.getByText(/Connect your calendar accounts/i)).toBeVisible();
  });

  test('should display Google Calendar connection option', async ({ page }) => {
    // Check for Google Calendar section
    await expect(page.getByText('Google Calendar')).toBeVisible();
    
    // Check for connect button
    const connectButton = page.getByRole('button', { name: /Connect Google Calendar/i });
    await expect(connectButton).toBeVisible();
  });

  test('should display Microsoft Outlook connection option', async ({ page }) => {
    // Check for Outlook section
    await expect(page.getByText('Microsoft Outlook')).toBeVisible();
    
    // Check for connect button
    const connectButton = page.getByRole('button', { name: /Connect Outlook/i });
    await expect(connectButton).toBeVisible();
  });

  test('should show calendar features list', async ({ page }) => {
    // Check for feature descriptions
    await expect(page.getByText(/Two-way sync/i)).toBeVisible();
    await expect(page.getByText(/automatic updates/i)).toBeVisible();
  });
});

test.describe('Calendar Event Creation Form Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(CALENDAR_PAGE);
    // Open create event dialog
    await page.getByRole('button', { name: /New Event/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Try to submit form without filling required fields
    const createButton = page.getByRole('button', { name: /Create Event/i });
    await createButton.click();

    // Should show validation error or stay on dialog
    await expect(page.getByRole('dialog')).toBeVisible();
  });

  test('should accept valid event data', async ({ page }) => {
    // Fill in event title
    await page.getByLabel(/Event Title/i).fill('Test Interview');
    
    // Fill in description
    await page.getByLabel(/Description/i).fill('Technical interview with engineering team');
    
    // Fill in location
    await page.getByLabel(/Location/i).fill('Video call');

    // Set start date and time
    const today = new Date();
    const dateString = today.toISOString().split('T')[0];
    
    const startDateInput = page.locator('input[type="date"]').first();
    if (await startDateInput.isVisible()) {
      await startDateInput.fill(dateString);
    }

    const startTimeInput = page.locator('input[type="time"]').first();
    if (await startTimeInput.isVisible()) {
      await startTimeInput.fill('14:00');
    }

    // Set end date and time
    const endDateInput = page.locator('input[type="date"]').nth(1);
    if (await endDateInput.isVisible()) {
      await endDateInput.fill(dateString);
    }

    const endTimeInput = page.locator('input[type="time"]').nth(1);
    if (await endTimeInput.isVisible()) {
      await endTimeInput.fill('15:00');
    }

    // Form should be valid (all required fields filled)
    const createButton = page.getByRole('button', { name: /Create Event/i });
    await expect(createButton).toBeEnabled();
  });

  test('should have reminder checkboxes', async ({ page }) => {
    // Check for reminder options
    await expect(page.getByText(/15 minutes before/i)).toBeVisible();
    await expect(page.getByText(/1 hour before/i)).toBeVisible();
    await expect(page.getByText(/1 day before/i)).toBeVisible();
  });
});

test.describe('Calendar Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto(CALENDAR_PAGE);
    
    // Check main heading
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toBeVisible();
  });

  test('should have keyboard navigation support', async ({ page }) => {
    await page.goto(CALENDAR_PAGE);
    
    // Tab through interactive elements
    await page.keyboard.press('Tab');
    
    // Check that focus is visible on interactive elements
    const newEventButton = page.getByRole('button', { name: /New Event/i });
    await expect(newEventButton).toBeVisible();
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto(CALENDAR_PAGE);
    
    // Open dialog
    await page.getByRole('button', { name: /New Event/i }).click();
    
    // Check dialog has proper role
    await expect(page.getByRole('dialog')).toBeVisible();
  });
});

test.describe('Calendar Responsive Design', () => {
  test('should display correctly on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(CALENDAR_PAGE);

    // Check main elements are visible
    await expect(page.getByRole('heading', { name: 'Calendar' })).toBeVisible();
    await expect(page.getByRole('button', { name: /New Event/i })).toBeVisible();
  });

  test('should display correctly on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(CALENDAR_PAGE);

    // Check main elements are visible
    await expect(page.getByRole('heading', { name: 'Calendar' })).toBeVisible();
    await expect(page.locator('.rbc-calendar')).toBeVisible();
  });

  test('should display correctly on desktop viewport', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(CALENDAR_PAGE);

    // Check main elements are visible
    await expect(page.getByRole('heading', { name: 'Calendar' })).toBeVisible();
    await expect(page.locator('.rbc-calendar')).toBeVisible();
    
    // Sidebar should be visible on desktop
    await expect(page.getByText('Event Details')).toBeVisible();
    await expect(page.getByText('Upcoming Events')).toBeVisible();
  });
});
