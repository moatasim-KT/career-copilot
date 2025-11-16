/**
 * NotificationPreferences Component
 * Settings for notification preferences per category
 */

'use client';

import {
  Bell,
  Mail,
  Volume2,
  Smartphone,
  Moon,
  Save,
  RotateCcw,
  Send,
} from 'lucide-react';
import { useState } from 'react';

import Button2 from '@/components/ui/Button2';
import Card2 from '@/components/ui/Card2';
import { Checkbox } from '@/components/ui/Checkbox';
import Input2 from '@/components/ui/Input2';
import Select2 from '@/components/ui/Select2';
import { logger } from '@/lib/logger';
import { m } from '@/lib/motion';
import {
  getCategoryIcon,
  getCategoryLabel,
  categoryLabels,
} from '@/lib/notificationTemplates';
import {
  isPushNotificationSupported,
  getNotificationPermission,
  showTestNotification,
} from '@/lib/pushNotifications';
import { cn } from '@/lib/utils';
import type { NotificationCategory, NotificationPreference, NotificationSettings } from '@/types/notification';

// Default preferences
const defaultPreferences: NotificationPreference[] = (
  Object.keys(categoryLabels) as NotificationCategory[]
).map(category => ({
  category,
  enabled: true,
  emailEnabled: category === 'application' || category === 'job_alert',
  emailFrequency: 'immediate',
  pushEnabled: true,
  soundEnabled: category === 'application' || category === 'job_alert',
  vibrationEnabled: true,
}));

const defaultSettings: NotificationSettings = {
  userId: '1',
  preferences: defaultPreferences,
  doNotDisturb: {
    enabled: false,
    startTime: '22:00',
    endTime: '08:00',
    days: [0, 1, 2, 3, 4, 5, 6], // All days
  },
  globalMute: false,
};

interface CategoryPreferenceRowProps {
  preference: NotificationPreference;
  onChange: (preference: NotificationPreference) => void;
}

function CategoryPreferenceRow({ preference, onChange }: CategoryPreferenceRowProps) {
  const CategoryIcon = getCategoryIcon(preference.category);
  const categoryLabel = getCategoryLabel(preference.category);

  return (
    <div className="p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg hover:border-neutral-300 dark:hover:border-neutral-600 transition-colors">
      {/* Category Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
            <CategoryIcon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
              {categoryLabel}
            </h3>
            <p className="text-xs text-neutral-600 dark:text-neutral-400">
              {preference.enabled ? 'Enabled' : 'Disabled'}
            </p>
          </div>
        </div>

        {/* Master Toggle */}
        <Checkbox
          checked={preference.enabled}
          onCheckedChange={(checked) =>
            onChange({ ...preference, enabled: checked as boolean })
          }
        />
      </div>

      {/* Detailed Settings */}
      {preference.enabled && (
        <m.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="space-y-3 pl-13"
        >
          {/* Push Notifications */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-neutral-500" />
              <span className="text-sm text-neutral-700 dark:text-neutral-300">
                Push notifications
              </span>
            </div>
            <Checkbox
              checked={preference.pushEnabled}
              onCheckedChange={(checked) =>
                onChange({ ...preference, pushEnabled: checked as boolean })
              }
            />
          </div>

          {/* Email Notifications */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-neutral-500" />
                <span className="text-sm text-neutral-700 dark:text-neutral-300">
                  Email notifications
                </span>
              </div>
              <Checkbox
                checked={preference.emailEnabled}
                onCheckedChange={(checked) =>
                  onChange({ ...preference, emailEnabled: checked as boolean })
                }
              />
            </div>

            {preference.emailEnabled && (
              <div className="pl-6">
                <Select2
                  value={preference.emailFrequency}
                  onChange={(e) =>
                    onChange({
                      ...preference,
                      emailFrequency: e.target.value as 'immediate' | 'daily' | 'weekly' | 'off',
                    })
                  }
                  className="text-sm"
                >
                  <option value="immediate">Immediate</option>
                  <option value="daily">Daily digest</option>
                  <option value="weekly">Weekly digest</option>
                  <option value="off">Off</option>
                </Select2>
              </div>
            )}
          </div>

          {/* Sound */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Volume2 className="w-4 h-4 text-neutral-500" />
              <span className="text-sm text-neutral-700 dark:text-neutral-300">
                Sound
              </span>
            </div>
            <Checkbox
              checked={preference.soundEnabled}
              onCheckedChange={(checked) =>
                onChange({ ...preference, soundEnabled: checked as boolean })
              }
            />
          </div>

          {/* Vibration */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Smartphone className="w-4 h-4 text-neutral-500" />
              <span className="text-sm text-neutral-700 dark:text-neutral-300">
                Vibration
              </span>
            </div>
            <Checkbox
              checked={preference.vibrationEnabled || false}
              onCheckedChange={(checked) =>
                onChange({ ...preference, vibrationEnabled: checked as boolean })
              }
            />
          </div>
        </m.div>
      )}
    </div>
  );
}

export default function NotificationPreferences() {
  const [settings, setSettings] = useState<NotificationSettings>(defaultSettings);
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isSendingTest, setIsSendingTest] = useState(false);

  const pushSupported = isPushNotificationSupported();
  const pushPermission = getNotificationPermission();

  const handlePreferenceChange = (updatedPreference: NotificationPreference) => {
    setSettings(prev => ({
      ...prev,
      preferences: prev.preferences.map(p =>
        p.category === updatedPreference.category ? updatedPreference : p,
      ),
    }));
    setHasChanges(true);
  };

  const handleDoNotDisturbToggle = (enabled: boolean) => {
    setSettings(prev => ({
      ...prev,
      doNotDisturb: prev.doNotDisturb
        ? { ...prev.doNotDisturb, enabled }
        : {
          enabled,
          startTime: '22:00',
          endTime: '08:00',
          days: [0, 1, 2, 3, 4, 5, 6],
        },
    }));
    setHasChanges(true);
  };

  const handleDoNotDisturbTimeChange = (field: 'startTime' | 'endTime', value: string) => {
    setSettings(prev => ({
      ...prev,
      doNotDisturb: prev.doNotDisturb
        ? { ...prev.doNotDisturb, [field]: value }
        : {
          enabled: true,
          startTime: field === 'startTime' ? value : '22:00',
          endTime: field === 'endTime' ? value : '08:00',
          days: [0, 1, 2, 3, 4, 5, 6],
        },
    }));
    setHasChanges(true);
  };

  const handleGlobalMuteToggle = (muted: boolean) => {
    setSettings(prev => ({ ...prev, globalMute: muted }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    setIsSaving(true);

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));

    // In production, save to backend:
    // await apiClient.updateNotificationSettings(settings);

    setIsSaving(false);
    setHasChanges(false);

    // Show success toast
    logger.info('Notification preferences saved:', settings);
  };

  const handleReset = () => {
    setSettings(defaultSettings);
    setHasChanges(true);
  };

  const handleSendTestNotification = async () => {
    setIsSendingTest(true);
    try {
      await showTestNotification();
      // Show success message
      logger.info('Test notification sent');
    } catch (error) {
      logger.error('Failed to send test notification:', error);
      // Show error message
    } finally {
      setIsSendingTest(false);
    }
  };

  const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
          Notification Preferences
        </h2>
        <p className="text-neutral-600 dark:text-neutral-400">
          Customize how and when you receive notifications
        </p>
      </div>

      {/* Push Notification Status */}
      {pushSupported && (
        <Card2 className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                <Bell className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                  Browser Push Notifications
                </h3>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  {pushPermission.granted
                    ? 'Enabled - You will receive push notifications'
                    : pushPermission.denied
                      ? 'Blocked - Please enable in browser settings'
                      : 'Not enabled - Click to enable push notifications'}
                </p>
              </div>
            </div>
          </div>

          {pushPermission.granted && (
            <div className="flex justify-end">
              <Button2
                size="sm"
                variant="outline"
                onClick={handleSendTestNotification}
                loading={isSendingTest}
                disabled={isSendingTest}
              >
                <Send className="w-4 h-4 mr-2" />
                Send test notification
              </Button2>
            </div>
          )}
        </Card2>
      )}

      {/* Global Mute */}
      <Card2 className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <Bell className={cn(
                'w-6 h-6',
                settings.globalMute
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-neutral-600 dark:text-neutral-400',
              )} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                Mute all notifications
              </h3>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Temporarily disable all notifications
              </p>
            </div>
          </div>
          <Checkbox
            checked={settings.globalMute}
            onCheckedChange={(checked) => handleGlobalMuteToggle(checked as boolean)}
          />
        </div>
      </Card2>

      {/* Do Not Disturb */}
      <Card2 className="p-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                <Moon className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                  Do Not Disturb
                </h3>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  Silence notifications during specific hours
                </p>
              </div>
            </div>
            <Checkbox
              checked={settings.doNotDisturb?.enabled || false}
              onCheckedChange={(checked) => handleDoNotDisturbToggle(checked as boolean)}
            />
          </div>

          {settings.doNotDisturb?.enabled && (
            <m.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-4 pl-15"
            >
              {/* Time Range */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                    Start time
                  </label>
                  <Input2
                    type="time"
                    value={settings.doNotDisturb.startTime}
                    onChange={(e) => handleDoNotDisturbTimeChange('startTime', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                    End time
                  </label>
                  <Input2
                    type="time"
                    value={settings.doNotDisturb.endTime}
                    onChange={(e) => handleDoNotDisturbTimeChange('endTime', e.target.value)}
                  />
                </div>
              </div>

              {/* Days */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                  Active days
                </label>
                <div className="flex gap-2">
                  {dayLabels.map((day, index) => {
                    const isActive = settings.doNotDisturb?.days.includes(index);
                    return (
                      <button
                        key={day}
                        onClick={() => {
                          const days = settings.doNotDisturb?.days || [];
                          const newDays = isActive
                            ? days.filter(d => d !== index)
                            : [...days, index].sort();
                          setSettings(prev => ({
                            ...prev,
                            doNotDisturb: prev.doNotDisturb
                              ? { ...prev.doNotDisturb, days: newDays }
                              : {
                                enabled: true,
                                startTime: '22:00',
                                endTime: '08:00',
                                days: newDays,
                              },
                          }));
                          setHasChanges(true);
                        }}
                        className={cn(
                          'w-10 h-10 rounded-full text-sm font-medium transition-colors',
                          isActive
                            ? 'bg-primary-600 dark:bg-primary-500 text-white'
                            : 'bg-neutral-200 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-300 dark:hover:bg-neutral-600',
                        )}
                      >
                        {day}
                      </button>
                    );
                  })}
                </div>
              </div>
            </m.div>
          )}
        </div>
      </Card2>

      {/* Category Preferences */}
      <div>
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
          Notification Categories
        </h3>
        <div className="space-y-3">
          {settings.preferences.map(preference => (
            <CategoryPreferenceRow
              key={preference.category}
              preference={preference}
              onChange={handlePreferenceChange}
            />
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-6 border-t border-neutral-200 dark:border-neutral-700">
        <Button2
          variant="outline"
          onClick={handleReset}
          disabled={isSaving}
        >
          <RotateCcw className="w-4 h-4 mr-2" />
          Reset to defaults
        </Button2>

        <Button2
          variant="primary"
          onClick={handleSave}
          disabled={!hasChanges || isSaving}
          loading={isSaving}
        >
          <Save className="w-4 h-4 mr-2" />
          {isSaving ? 'Saving...' : 'Save preferences'}
        </Button2>
      </div>
    </div>
  );
}
