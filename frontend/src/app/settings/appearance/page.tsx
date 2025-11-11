/**
 * Appearance Settings Page
 * 
 * Allows users to customize the visual appearance:
 * - Theme (Light, Dark, System)
 * - UI Density (Comfortable, Compact)
 * - Language (future i18n)
 * - Font size (accessibility)
 */

'use client';

import { useState } from 'react';
import { Sun, Moon, Monitor, Save, Check } from 'lucide-react';
import { motion } from 'framer-motion';

import Button2 from '@/components/ui/Button2';
import Card2 from '@/components/ui/Card2';
import Select2 from '@/components/ui/Select2';
import { useDarkMode } from '@/hooks/useDarkMode';
import { cn } from '@/lib/utils';

type UIDensity = 'comfortable' | 'compact';
type FontSize = 'small' | 'medium' | 'large';

interface AppearanceSettings {
  density: UIDensity;
  language: string;
  fontSize: FontSize;
}

const languages = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Español (Coming Soon)', disabled: true },
  { value: 'fr', label: 'Français (Coming Soon)', disabled: true },
  { value: 'de', label: 'Deutsch (Coming Soon)', disabled: true },
  { value: 'zh', label: '中文 (Coming Soon)', disabled: true },
];

const fontSizes = [
  { value: 'small', label: 'Small', description: 'Compact text for more content' },
  { value: 'medium', label: 'Medium', description: 'Default comfortable reading' },
  { value: 'large', label: 'Large', description: 'Larger text for accessibility' },
];

export default function AppearanceSettingsPage() {
  const { theme, setTheme, isDark } = useDarkMode();
  const [settings, setSettings] = useState<AppearanceSettings>({
    density: 'comfortable',
    language: 'en',
    fontSize: 'medium',
  });
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const handleSettingChange = (field: keyof AppearanceSettings, value: any) => {
    setSettings(prev => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    setIsSaving(true);

    try {
      // Save settings to backend
      // await apiClient.user.updateSettings({ appearance: settings });

      // Apply font size
      document.documentElement.style.fontSize = 
        settings.fontSize === 'small' ? '14px' :
        settings.fontSize === 'large' ? '18px' : '16px';

      // Apply density
      document.documentElement.setAttribute('data-density', settings.density);

      setHasChanges(false);
      
      // Show success message
      console.log('Appearance settings saved:', settings);
    } catch (error) {
      console.error('Failed to save appearance settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
          Appearance Settings
        </h2>
        <p className="text-neutral-600 dark:text-neutral-400">
          Customize how Career Copilot looks and feels
        </p>
      </div>

      {/* Theme Selection */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Theme
        </h3>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Choose your preferred color scheme
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Light Theme */}
          <button
            onClick={() => setTheme('light')}
            className={cn(
              'relative p-4 rounded-lg border-2 transition-all hover:border-primary-300 dark:hover:border-primary-600',
              theme === 'light'
                ? 'border-primary-600 dark:border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-neutral-200 dark:border-neutral-700'
            )}
          >
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center">
                <Sun className="w-6 h-6 text-white" />
              </div>
              <div className="text-center">
                <div className="font-medium text-neutral-900 dark:text-neutral-100">
                  Light
                </div>
                <div className="text-xs text-neutral-600 dark:text-neutral-400">
                  Bright and clear
                </div>
              </div>
            </div>
            {theme === 'light' && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute top-2 right-2 w-6 h-6 rounded-full bg-primary-600 dark:bg-primary-500 flex items-center justify-center"
              >
                <Check className="w-4 h-4 text-white" />
              </motion.div>
            )}
          </button>

          {/* Dark Theme */}
          <button
            onClick={() => setTheme('dark')}
            className={cn(
              'relative p-4 rounded-lg border-2 transition-all hover:border-primary-300 dark:hover:border-primary-600',
              theme === 'dark'
                ? 'border-primary-600 dark:border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-neutral-200 dark:border-neutral-700'
            )}
          >
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center">
                <Moon className="w-6 h-6 text-white" />
              </div>
              <div className="text-center">
                <div className="font-medium text-neutral-900 dark:text-neutral-100">
                  Dark
                </div>
                <div className="text-xs text-neutral-600 dark:text-neutral-400">
                  Easy on the eyes
                </div>
              </div>
            </div>
            {theme === 'dark' && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute top-2 right-2 w-6 h-6 rounded-full bg-primary-600 dark:bg-primary-500 flex items-center justify-center"
              >
                <Check className="w-4 h-4 text-white" />
              </motion.div>
            )}
          </button>

          {/* System Theme */}
          <button
            onClick={() => setTheme('system')}
            className={cn(
              'relative p-4 rounded-lg border-2 transition-all hover:border-primary-300 dark:hover:border-primary-600',
              theme === 'system'
                ? 'border-primary-600 dark:border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-neutral-200 dark:border-neutral-700'
            )}
          >
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                <Monitor className="w-6 h-6 text-white" />
              </div>
              <div className="text-center">
                <div className="font-medium text-neutral-900 dark:text-neutral-100">
                  System
                </div>
                <div className="text-xs text-neutral-600 dark:text-neutral-400">
                  Match your OS
                </div>
              </div>
            </div>
            {theme === 'system' && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute top-2 right-2 w-6 h-6 rounded-full bg-primary-600 dark:bg-primary-500 flex items-center justify-center"
              >
                <Check className="w-4 h-4 text-white" />
              </motion.div>
            )}
          </button>
        </div>
      </div>

      {/* UI Density */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          UI Density
        </h3>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Adjust spacing and component sizes
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Comfortable */}
          <button
            onClick={() => handleSettingChange('density', 'comfortable')}
            className={cn(
              'relative p-4 rounded-lg border-2 transition-all text-left hover:border-primary-300 dark:hover:border-primary-600',
              settings.density === 'comfortable'
                ? 'border-primary-600 dark:border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-neutral-200 dark:border-neutral-700'
            )}
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                  Comfortable
                </div>
                <div className="text-sm text-neutral-600 dark:text-neutral-400">
                  More spacing, easier to scan
                </div>
              </div>
              {settings.density === 'comfortable' && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-6 h-6 rounded-full bg-primary-600 dark:bg-primary-500 flex items-center justify-center flex-shrink-0"
                >
                  <Check className="w-4 h-4 text-white" />
                </motion.div>
              )}
            </div>
            {/* Preview */}
            <div className="mt-4 space-y-2">
              <div className="h-8 bg-neutral-200 dark:bg-neutral-700 rounded" />
              <div className="h-8 bg-neutral-200 dark:bg-neutral-700 rounded" />
            </div>
          </button>

          {/* Compact */}
          <button
            onClick={() => handleSettingChange('density', 'compact')}
            className={cn(
              'relative p-4 rounded-lg border-2 transition-all text-left hover:border-primary-300 dark:hover:border-primary-600',
              settings.density === 'compact'
                ? 'border-primary-600 dark:border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-neutral-200 dark:border-neutral-700'
            )}
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                  Compact
                </div>
                <div className="text-sm text-neutral-600 dark:text-neutral-400">
                  Less spacing, more content
                </div>
              </div>
              {settings.density === 'compact' && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-6 h-6 rounded-full bg-primary-600 dark:bg-primary-500 flex items-center justify-center flex-shrink-0"
                >
                  <Check className="w-4 h-4 text-white" />
                </motion.div>
              )}
            </div>
            {/* Preview */}
            <div className="mt-4 space-y-1">
              <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded" />
              <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded" />
              <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded" />
            </div>
          </button>
        </div>
      </div>

      {/* Font Size */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Font Size
        </h3>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Adjust text size for better readability
        </p>

        <div className="space-y-3">
          {fontSizes.map(size => (
            <button
              key={size.value}
              onClick={() => handleSettingChange('fontSize', size.value)}
              className={cn(
                'w-full p-4 rounded-lg border-2 transition-all text-left hover:border-primary-300 dark:hover:border-primary-600',
                settings.fontSize === size.value
                  ? 'border-primary-600 dark:border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-neutral-200 dark:border-neutral-700'
              )}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className={cn(
                    'font-medium text-neutral-900 dark:text-neutral-100 mb-1',
                    size.value === 'small' && 'text-sm',
                    size.value === 'medium' && 'text-base',
                    size.value === 'large' && 'text-lg'
                  )}>
                    {size.label}
                  </div>
                  <div className="text-sm text-neutral-600 dark:text-neutral-400">
                    {size.description}
                  </div>
                </div>
                {settings.fontSize === size.value && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-6 h-6 rounded-full bg-primary-600 dark:bg-primary-500 flex items-center justify-center flex-shrink-0"
                  >
                    <Check className="w-4 h-4 text-white" />
                  </motion.div>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Language */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Language
        </h3>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Choose your preferred language
        </p>

        <Select2
          value={settings.language}
          onChange={(e) => handleSettingChange('language', e.target.value)}
        >
          {languages.map(lang => (
            <option key={lang.value} value={lang.value} disabled={lang.disabled}>
              {lang.label}
            </option>
          ))}
        </Select2>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-6 border-t border-neutral-200 dark:border-neutral-700">
        <Button2
          variant="outline"
          onClick={() => {
            setSettings({
              density: 'comfortable',
              language: 'en',
              fontSize: 'medium',
            });
            setHasChanges(false);
          }}
          disabled={!hasChanges || isSaving}
        >
          Reset
        </Button2>

        <Button2
          variant="primary"
          onClick={handleSave}
          disabled={!hasChanges || isSaving}
          loading={isSaving}
        >
          <Save className="w-4 h-4 mr-2" />
          {isSaving ? 'Saving...' : 'Save Changes'}
        </Button2>
      </div>
    </div>
  );
}
