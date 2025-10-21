import { useState } from 'react'
import { Card, CardHeader, CardContent, Button, Input } from '@/components/ui'
import { 
  BellIcon, 
  ComputerDesktopIcon, 
  ShieldCheckIcon,
  CheckIcon
} from '@heroicons/react/24/outline'

interface SettingsEditorProps {
  settings: any
  onSave: (settings: any) => void
}

export function SettingsEditor({ settings, onSave }: SettingsEditorProps) {
  const [formData, setFormData] = useState({
    notifications: {
      morning_briefing: settings?.notifications?.morning_briefing ?? true,
      evening_summary: settings?.notifications?.evening_summary ?? true,
      job_recommendations: settings?.notifications?.job_recommendations ?? true,
      application_reminders: settings?.notifications?.application_reminders ?? true,
      interview_reminders: settings?.notifications?.interview_reminders ?? true,
      email_time: settings?.notifications?.email_time ?? '08:00',
      timezone: settings?.notifications?.timezone ?? 'UTC'
    },
    ui_preferences: {
      theme: settings?.ui_preferences?.theme ?? 'light',
      dashboard_layout: settings?.ui_preferences?.dashboard_layout ?? 'default',
      items_per_page: settings?.ui_preferences?.items_per_page ?? 20,
      default_job_view: settings?.ui_preferences?.default_job_view ?? 'cards'
    },
    privacy_settings: {
      data_sharing: settings?.privacy_settings?.data_sharing ?? false,
      analytics_tracking: settings?.privacy_settings?.analytics_tracking ?? true,
      email_marketing: settings?.privacy_settings?.email_marketing ?? false,
      profile_visibility: settings?.privacy_settings?.profile_visibility ?? 'private'
    }
  })

  const [activeSection, setActiveSection] = useState<'notifications' | 'ui' | 'privacy'>('notifications')
  const [saving, setSaving] = useState(false)

  const handleInputChange = (section: string, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section as keyof typeof prev],
        [field]: value
      }
    }))
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      await onSave(formData)
    } finally {
      setSaving(false)
    }
  }

  const sections = [
    { id: 'notifications' as const, name: 'Notifications', icon: BellIcon },
    { id: 'ui' as const, name: 'Interface', icon: ComputerDesktopIcon },
    { id: 'privacy' as const, name: 'Privacy', icon: ShieldCheckIcon },
  ]

  return (
    <div className="space-y-6">
      {/* Section Navigation */}
      <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
        {sections.map((section) => {
          const Icon = section.icon
          return (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`
                flex items-center px-4 py-2 rounded-md font-medium text-sm transition-colors flex-1 justify-center
                ${activeSection === section.id
                  ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }
              `}
            >
              <Icon className="h-4 w-4 mr-2" />
              {section.name}
            </button>
          )
        })}
      </div>

      {/* Notifications Settings */}
      {activeSection === 'notifications' && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Notification Preferences
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Configure when and how you receive notifications
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Email Notifications */}
            <div>
              <h4 className="text-md font-medium text-gray-900 dark:text-white mb-4">
                Email Notifications
              </h4>
              <div className="space-y-4">
                <label className="flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      Morning Briefing
                    </span>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Daily email with job recommendations and career insights
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={formData.notifications.morning_briefing}
                    onChange={(e) => handleInputChange('notifications', 'morning_briefing', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </label>

                <label className="flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      Evening Summary
                    </span>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Daily progress summary and tomorrow's action items
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={formData.notifications.evening_summary}
                    onChange={(e) => handleInputChange('notifications', 'evening_summary', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </label>

                <label className="flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      Job Recommendations
                    </span>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Notifications when new matching jobs are found
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={formData.notifications.job_recommendations}
                    onChange={(e) => handleInputChange('notifications', 'job_recommendations', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </label>

                <label className="flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      Application Reminders
                    </span>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Reminders to follow up on applications
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={formData.notifications.application_reminders}
                    onChange={(e) => handleInputChange('notifications', 'application_reminders', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </label>

                <label className="flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      Interview Reminders
                    </span>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Reminders for upcoming interviews
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={formData.notifications.interview_reminders}
                    onChange={(e) => handleInputChange('notifications', 'interview_reminders', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </label>
              </div>
            </div>

            {/* Email Timing */}
            <div>
              <h4 className="text-md font-medium text-gray-900 dark:text-white mb-4">
                Email Timing
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Email Time"
                  type="time"
                  value={formData.notifications.email_time}
                  onChange={(e) => handleInputChange('notifications', 'email_time', e.target.value)}
                  help="Time to receive daily emails"
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Timezone
                  </label>
                  <select
                    className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    value={formData.notifications.timezone}
                    onChange={(e) => handleInputChange('notifications', 'timezone', e.target.value)}
                  >
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">Eastern Time</option>
                    <option value="America/Chicago">Central Time</option>
                    <option value="America/Denver">Mountain Time</option>
                    <option value="America/Los_Angeles">Pacific Time</option>
                    <option value="Europe/London">London</option>
                    <option value="Europe/Paris">Paris</option>
                    <option value="Asia/Tokyo">Tokyo</option>
                    <option value="Asia/Shanghai">Shanghai</option>
                  </select>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* UI Preferences */}
      {activeSection === 'ui' && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Interface Preferences
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Customize the look and feel of your dashboard
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Select
                label="Theme"
                value={formData.ui_preferences.theme}
                onChange={(e) => handleInputChange('ui_preferences', 'theme', e.target.value)}
                help="Choose your preferred color scheme"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="auto">Auto (System)</option>
              </Select>

              <Select
                label="Dashboard Layout"
                value={formData.ui_preferences.dashboard_layout}
                onChange={(e) => handleInputChange('ui_preferences', 'dashboard_layout', e.target.value)}
                help="Choose your dashboard layout style"
              >
                <option value="compact">Compact</option>
                <option value="default">Default</option>
                <option value="detailed">Detailed</option>
              </Select>

              <Select
                label="Items Per Page"
                value={formData.ui_preferences.items_per_page}
                onChange={(e) => handleInputChange('ui_preferences', 'items_per_page', parseInt(e.target.value))}
                help="Number of items to show per page"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </Select>

              <Select
                label="Default Job View"
                value={formData.ui_preferences.default_job_view}
                onChange={(e) => handleInputChange('ui_preferences', 'default_job_view', e.target.value)}
                help="Default view for job listings"
              >
                <option value="cards">Cards</option>
                <option value="list">List</option>
                <option value="table">Table</option>
              </Select>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Privacy Settings */}
      {activeSection === 'privacy' && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Privacy Settings
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Control your data privacy and sharing preferences
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <label className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    Data Sharing
                  </span>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Allow sharing anonymized data for service improvement
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={formData.privacy_settings.data_sharing}
                  onChange={(e) => handleInputChange('privacy_settings', 'data_sharing', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </label>

              <label className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    Analytics Tracking
                  </span>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Allow usage analytics to improve your experience
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={formData.privacy_settings.analytics_tracking}
                  onChange={(e) => handleInputChange('privacy_settings', 'analytics_tracking', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </label>

              <label className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    Email Marketing
                  </span>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Receive promotional emails and feature updates
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={formData.privacy_settings.email_marketing}
                  onChange={(e) => handleInputChange('privacy_settings', 'email_marketing', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </label>
            </div>

            <div>
              <Select
                label="Profile Visibility"
                value={formData.privacy_settings.profile_visibility}
                onChange={(e) => handleInputChange('privacy_settings', 'profile_visibility', e.target.value)}
                help="Control who can see your profile information"
              >
                <option value="private">Private</option>
                <option value="contacts">Contacts Only</option>
                <option value="public">Public</option>
              </Select>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Save Button */}
      <div className="flex justify-end">
        <Button 
          onClick={handleSave} 
          disabled={saving}
          variant="primary"
        >
          {saving ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Saving...
            </>
          ) : (
            <>
              <CheckIcon className="h-4 w-4 mr-2" />
              Save Settings
            </>
          )}
        </Button>
      </div>
    </div>
  )
}