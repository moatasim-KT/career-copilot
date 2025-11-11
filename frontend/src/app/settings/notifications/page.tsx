/**
 * Notifications Settings Page
 * 
 * Integrates the NotificationPreferences component from task 8.4
 * Allows users to configure:
 * - Toggle per category
 * - Email notifications (Immediate, Daily digest, Off)
 * - Push notifications toggle
 * - Sound/vibration settings
 * - Do Not Disturb schedule
 */

'use client';

import NotificationPreferences from '@/components/settings/NotificationPreferences';

export default function NotificationsSettingsPage() {
  return <NotificationPreferences />;
}
