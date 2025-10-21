import { Layout } from '@/components/Layout'
import { AccessibilitySettings } from '@/components/AccessibilitySettings'

export default function AccessibilityPage() {
  return (
    <Layout title="Accessibility Settings - Career Co-Pilot">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Accessibility Settings
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Customize your experience to meet your accessibility needs and preferences.
          </p>
        </div>
        
        <AccessibilitySettings />
      </div>
    </Layout>
  )
}