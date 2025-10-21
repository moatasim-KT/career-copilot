import { useState } from 'react'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import { 
  EyeIcon,
  SpeakerWaveIcon,
  AdjustmentsHorizontalIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'
import { useAccessibility } from '@/contexts/AccessibilityContext'
import { A11yTesting } from '@/utils/accessibility'

interface AccessibilitySettingsProps {
  onClose?: () => void
}

export function AccessibilitySettings({ onClose }: AccessibilitySettingsProps) {
  const { settings, updateSetting, resetToDefaults, announceToScreenReader } = useAccessibility()
  const [testResults, setTestResults] = useState<{ category: string; issues: string[] }[]>([])
  const [showTestResults, setShowTestResults] = useState(false)

  const handleSettingChange = (key: keyof typeof settings, value: boolean) => {
    updateSetting(key, value)
    announceToScreenReader(`${key.replace(/([A-Z])/g, ' $1').toLowerCase()} ${value ? 'enabled' : 'disabled'}`)
  }

  const runAccessibilityTests = () => {
    const results = A11yTesting.runAllChecks()
    setTestResults(results)
    setShowTestResults(true)
    
    const totalIssues = results.reduce((sum, category) => sum + category.issues.length, 0)
    announceToScreenReader(`Accessibility test completed. Found ${totalIssues} issues across ${results.length} categories.`)
  }

  const settingSections = [
    {
      title: 'Visual Preferences',
      icon: EyeIcon,
      settings: [
        {
          key: 'highContrast' as const,
          label: 'High Contrast Mode',
          description: 'Increases color contrast for better visibility',
          systemDetected: settings.prefersHighContrast
        },
        {
          key: 'largeText' as const,
          label: 'Large Text',
          description: 'Increases font size throughout the application',
          systemDetected: false
        },
        {
          key: 'reducedMotion' as const,
          label: 'Reduce Motion',
          description: 'Minimizes animations and transitions',
          systemDetected: settings.prefersReducedMotion
        }
      ]
    },
    {
      title: 'Screen Reader Support',
      icon: SpeakerWaveIcon,
      settings: [
        {
          key: 'screenReaderOptimized' as const,
          label: 'Screen Reader Optimized',
          description: 'Optimizes interface for screen reader users',
          systemDetected: false
        }
      ]
    },
    {
      title: 'Keyboard Navigation',
      icon: AdjustmentsHorizontalIcon,
      settings: [
        {
          key: 'keyboardNavigation' as const,
          label: 'Enhanced Keyboard Navigation',
          description: 'Enables advanced keyboard shortcuts and navigation',
          systemDetected: false
        },
        {
          key: 'showFocusRings' as const,
          label: 'Show Focus Indicators',
          description: 'Shows visual focus indicators for keyboard navigation',
          systemDetected: false
        },
        {
          key: 'skipLinks' as const,
          label: 'Skip Links',
          description: 'Enables skip navigation links',
          systemDetected: false
        }
      ]
    }
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-3">
            <AdjustmentsHorizontalIcon className="h-6 w-6 text-blue-600" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Accessibility Settings
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Customize the interface to meet your accessibility needs
              </p>
            </div>
          </div>
          {onClose && (
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
          )}
        </CardHeader>

        <CardContent className="space-y-8">
          {/* System Detection Notice */}
          {(settings.prefersReducedMotion || settings.prefersHighContrast) && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <InformationCircleIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="font-medium text-blue-900 dark:text-blue-100">
                    System Preferences Detected
                  </h3>
                  <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                    We've detected accessibility preferences in your system settings and automatically enabled relevant options.
                  </p>
                  <ul className="text-sm text-blue-700 dark:text-blue-300 mt-2 list-disc list-inside">
                    {settings.prefersReducedMotion && <li>Reduced motion preference detected</li>}
                    {settings.prefersHighContrast && <li>High contrast preference detected</li>}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Settings Sections */}
          {settingSections.map((section) => (
            <div key={section.title} className="space-y-4">
              <div className="flex items-center gap-2">
                <section.icon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  {section.title}
                </h3>
              </div>

              <div className="grid gap-4">
                {section.settings.map((setting) => (
                  <div
                    key={setting.key}
                    className="flex items-start justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <label
                          htmlFor={setting.key}
                          className="text-sm font-medium text-gray-900 dark:text-white cursor-pointer"
                        >
                          {setting.label}
                        </label>
                        {setting.systemDetected && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                            System
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {setting.description}
                      </p>
                    </div>
                    <div className="ml-4">
                      <button
                        id={setting.key}
                        type="button"
                        role="switch"
                        aria-checked={settings[setting.key]}
                        onClick={() => handleSettingChange(setting.key, !settings[setting.key])}
                        className={`
                          relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent 
                          transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                          ${settings[setting.key] 
                            ? 'bg-blue-600' 
                            : 'bg-gray-200 dark:bg-gray-700'
                          }
                        `}
                      >
                        <span className="sr-only">
                          {settings[setting.key] ? 'Disable' : 'Enable'} {setting.label}
                        </span>
                        <span
                          className={`
                            pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 
                            transition duration-200 ease-in-out
                            ${settings[setting.key] ? 'translate-x-5' : 'translate-x-0'}
                          `}
                        />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Accessibility Testing */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Accessibility Testing
            </h3>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Run automated accessibility tests to identify potential issues on the current page.
              </p>
              <Button onClick={runAccessibilityTests} variant="secondary">
                Run Accessibility Tests
              </Button>
            </div>

            {/* Test Results */}
            {showTestResults && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                  Test Results
                </h4>
                {testResults.length === 0 ? (
                  <p className="text-sm text-green-600 dark:text-green-400">
                    No accessibility issues found!
                  </p>
                ) : (
                  <div className="space-y-3">
                    {testResults.map((category) => (
                      <div key={category.category}>
                        <h5 className="font-medium text-gray-800 dark:text-gray-200">
                          {category.category} ({category.issues.length} issues)
                        </h5>
                        {category.issues.length > 0 && (
                          <ul className="text-sm text-gray-600 dark:text-gray-400 list-disc list-inside ml-4 space-y-1">
                            {category.issues.map((issue, index) => (
                              <li key={index}>{issue}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Reset Settings */}
          <div className="pt-6 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                  Reset Settings
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Reset all accessibility settings to their default values
                </p>
              </div>
              <Button
                variant="secondary"
                onClick={() => {
                  resetToDefaults()
                  announceToScreenReader('Accessibility settings reset to defaults')
                }}
              >
                Reset to Defaults
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}