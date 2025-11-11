/**
 * Privacy Settings Page
 * 
 * Allows users to control privacy settings:
 * - Profile visibility (future multi-user)
 * - Search indexing opt-out
 * - Data sharing preferences
 * - Cookie preferences
 */

'use client';

import { useState } from 'react';
import { Shield, Eye, Search, Share2, Cookie, Save } from 'lucide-react';

import Button2 from '@/components/ui/Button2';
import Card2 from '@/components/ui/Card2';
import { Checkbox } from '@/components/ui/Checkbox';
import Select2 from '@/components/ui/Select2';
import { cn } from '@/lib/utils';

interface PrivacySettings {
  profileVisibility: 'public' | 'private' | 'connections';
  searchIndexing: boolean;
  dataSharing: {
    analytics: boolean;
    recommendations: boolean;
    thirdParty: boolean;
  };
  cookies: {
    essential: boolean;
    functional: boolean;
    analytics: boolean;
    marketing: boolean;
  };
}

export default function PrivacySettingsPage() {
  const [settings, setSettings] = useState<PrivacySettings>({
    profileVisibility: 'private',
    searchIndexing: false,
    dataSharing: {
      analytics: true,
      recommendations: true,
      thirdParty: false,
    },
    cookies: {
      essential: true,
      functional: true,
      analytics: true,
      marketing: false,
    },
  });

  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const handleVisibilityChange = (visibility: 'public' | 'private' | 'connections') => {
    setSettings(prev => ({ ...prev, profileVisibility: visibility }));
    setHasChanges(true);
  };

  const handleSearchIndexingToggle = (enabled: boolean) => {
    setSettings(prev => ({ ...prev, searchIndexing: enabled }));
    setHasChanges(true);
  };

  const handleDataSharingToggle = (key: keyof PrivacySettings['dataSharing'], enabled: boolean) => {
    setSettings(prev => ({
      ...prev,
      dataSharing: { ...prev.dataSharing, [key]: enabled },
    }));
    setHasChanges(true);
  };

  const handleCookieToggle = (key: keyof PrivacySettings['cookies'], enabled: boolean) => {
    setSettings(prev => ({
      ...prev,
      cookies: { ...prev.cookies, [key]: enabled },
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    setIsSaving(true);

    try {
      // Save settings to backend
      // await apiClient.user.updateSettings({ privacy: settings });

      setHasChanges(false);
      
      // Show success message
      console.log('Privacy settings saved:', settings);
    } catch (error) {
      console.error('Failed to save privacy settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
          Privacy Settings
        </h2>
        <p className="text-neutral-600 dark:text-neutral-400">
          Control how your information is shared and used
        </p>
      </div>

      {/* Profile Visibility */}
      <Card2 className="p-6">
        <div className="flex items-start gap-4 mb-4">
          <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
            <Eye className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
              Profile Visibility
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
              Control who can see your profile (available in future multi-user version)
            </p>

            <Select2
              value={settings.profileVisibility}
              onChange={(e) => handleVisibilityChange(e.target.value as any)}
              className="max-w-xs"
            >
              <option value="public">Public - Anyone can view</option>
              <option value="connections">Connections Only</option>
              <option value="private">Private - Only me</option>
            </Select2>
          </div>
        </div>
      </Card2>

      {/* Search Indexing */}
      <Card2 className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4 flex-1">
            <div className="w-12 h-12 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
              <Search className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                Search Engine Indexing
              </h3>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Allow search engines to index your public profile
              </p>
            </div>
          </div>
          <Checkbox
            checked={settings.searchIndexing}
            onCheckedChange={(checked) => handleSearchIndexingToggle(checked as boolean)}
          />
        </div>
      </Card2>

      {/* Data Sharing */}
      <Card2 className="p-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
            <Share2 className="w-6 h-6 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
              Data Sharing Preferences
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Control how your data is used to improve your experience
            </p>
          </div>
        </div>

        <div className="space-y-4 pl-16">
          {/* Analytics */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                Usage Analytics
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Help us improve by sharing anonymous usage data
              </div>
            </div>
            <Checkbox
              checked={settings.dataSharing.analytics}
              onCheckedChange={(checked) => handleDataSharingToggle('analytics', checked as boolean)}
            />
          </div>

          {/* Recommendations */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                Personalized Recommendations
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Use your activity to provide better job recommendations
              </div>
            </div>
            <Checkbox
              checked={settings.dataSharing.recommendations}
              onCheckedChange={(checked) => handleDataSharingToggle('recommendations', checked as boolean)}
            />
          </div>

          {/* Third Party */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                Third-Party Services
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Share data with trusted partners for enhanced features
              </div>
            </div>
            <Checkbox
              checked={settings.dataSharing.thirdParty}
              onCheckedChange={(checked) => handleDataSharingToggle('thirdParty', checked as boolean)}
            />
          </div>
        </div>
      </Card2>

      {/* Cookie Preferences */}
      <Card2 className="p-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center flex-shrink-0">
            <Cookie className="w-6 h-6 text-orange-600 dark:text-orange-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
              Cookie Preferences
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Manage how we use cookies on your device
            </p>
          </div>
        </div>

        <div className="space-y-4 pl-16">
          {/* Essential */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                Essential Cookies
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Required for the website to function properly
              </div>
            </div>
            <Checkbox
              checked={settings.cookies.essential}
              disabled
              onCheckedChange={(checked) => handleCookieToggle('essential', checked as boolean)}
            />
          </div>

          {/* Functional */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                Functional Cookies
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Remember your preferences and settings
              </div>
            </div>
            <Checkbox
              checked={settings.cookies.functional}
              onCheckedChange={(checked) => handleCookieToggle('functional', checked as boolean)}
            />
          </div>

          {/* Analytics */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                Analytics Cookies
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Help us understand how you use the website
              </div>
            </div>
            <Checkbox
              checked={settings.cookies.analytics}
              onCheckedChange={(checked) => handleCookieToggle('analytics', checked as boolean)}
            />
          </div>

          {/* Marketing */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                Marketing Cookies
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Used to deliver relevant advertisements
              </div>
            </div>
            <Checkbox
              checked={settings.cookies.marketing}
              onCheckedChange={(checked) => handleCookieToggle('marketing', checked as boolean)}
            />
          </div>
        </div>
      </Card2>

      {/* Privacy Notice */}
      <Card2 className="p-6 bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-neutral-700 dark:text-neutral-300">
            <p className="font-medium mb-1">Your Privacy Matters</p>
            <p>
              We take your privacy seriously. Read our{' '}
              <a href="/privacy-policy" className="text-primary-600 dark:text-primary-400 hover:underline">
                Privacy Policy
              </a>{' '}
              to learn more about how we collect, use, and protect your data.
            </p>
          </div>
        </div>
      </Card2>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-6 border-t border-neutral-200 dark:border-neutral-700">
        <Button2
          variant="outline"
          onClick={() => {
            setSettings({
              profileVisibility: 'private',
              searchIndexing: false,
              dataSharing: {
                analytics: true,
                recommendations: true,
                thirdParty: false,
              },
              cookies: {
                essential: true,
                functional: true,
                analytics: true,
                marketing: false,
              },
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
