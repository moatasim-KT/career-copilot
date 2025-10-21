import { useState, useEffect } from 'react'
import { Layout } from '@/components/Layout'
import { Card, CardHeader, CardContent, Button, Badge } from '@/components/ui'
import { 
  UserIcon, 
  CogIcon, 
  DocumentTextIcon,
  ChartBarIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import { useProfile } from '@/hooks/useProfile'
import { ProfileEditor } from '@/components/ProfileEditor'
import { SettingsEditor } from '@/components/SettingsEditor'
import { ApplicationHistory } from '@/components/ApplicationHistory'
import { DocumentManager } from '@/components/DocumentManager'

type TabType = 'profile' | 'settings' | 'history' | 'documents'

export default function Profile() {
  const [activeTab, setActiveTab] = useState<TabType>('profile')
  const [isEditing, setIsEditing] = useState(false)
  const { profile, loading, error, updateProfile, updateSettings } = useProfile()

  const tabs = [
    { id: 'profile' as TabType, name: 'Profile', icon: UserIcon },
    { id: 'settings' as TabType, name: 'Settings', icon: CogIcon },
    { id: 'history' as TabType, name: 'Application History', icon: ChartBarIcon },
    { id: 'documents' as TabType, name: 'Documents', icon: DocumentTextIcon },
  ]

  if (loading) {
    return (
      <Layout title="Profile - Career Co-Pilot">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout title="Profile - Career Co-Pilot">
        <div className="text-center py-12">
          <p className="text-red-600 dark:text-red-400">Error loading profile: {error}</p>
        </div>
      </Layout>
    )
  }

  return (
    <Layout title="Profile - Career Co-Pilot">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Profile Management
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Manage your profile, settings, and career data
            </p>
          </div>
          
          {/* Profile Completion Badge */}
          {profile && (
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm text-gray-600 dark:text-gray-400">Profile Completion</p>
                <div className="flex items-center space-x-2">
                  <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${profile.profile_completion}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {profile.profile_completion}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id)
                    setIsEditing(false)
                  }}
                  className={`
                    flex items-center py-2 px-1 border-b-2 font-medium text-sm transition-colors
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                    }
                  `}
                >
                  <Icon className="h-5 w-5 mr-2" />
                  {tab.name}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === 'profile' && (
            <div className="space-y-6">
              {/* Profile Header */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Personal Information
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Update your personal and professional details
                    </p>
                  </div>
                  <Button
                    variant={isEditing ? "secondary" : "primary"}
                    onClick={() => setIsEditing(!isEditing)}
                  >
                    {isEditing ? (
                      <>
                        <XMarkIcon className="h-4 w-4 mr-2" />
                        Cancel
                      </>
                    ) : (
                      <>
                        <PencilIcon className="h-4 w-4 mr-2" />
                        Edit Profile
                      </>
                    )}
                  </Button>
                </CardHeader>
                <CardContent>
                  {isEditing ? (
                    <ProfileEditor
                      profile={profile}
                      onSave={(updatedProfile) => {
                        updateProfile(updatedProfile)
                        setIsEditing(false)
                      }}
                      onCancel={() => setIsEditing(false)}
                    />
                  ) : (
                    <ProfileDisplay profile={profile} />
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'settings' && (
            <SettingsEditor
              settings={profile?.settings}
              onSave={updateSettings}
            />
          )}

          {activeTab === 'history' && (
            <ApplicationHistory />
          )}

          {activeTab === 'documents' && (
            <DocumentManager />
          )}
        </div>
      </div>
    </Layout>
  )
}

// Profile Display Component
function ProfileDisplay({ profile }: { profile: any }) {
  if (!profile) return null

  return (
    <div className="space-y-6">
      {/* Personal Information */}
      <div>
        <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">
          Personal Details
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              First Name
            </label>
            <p className="mt-1 text-sm text-gray-900 dark:text-white">
              {profile.first_name || 'Not provided'}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Last Name
            </label>
            <p className="mt-1 text-sm text-gray-900 dark:text-white">
              {profile.last_name || 'Not provided'}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Phone
            </label>
            <p className="mt-1 text-sm text-gray-900 dark:text-white">
              {profile.phone || 'Not provided'}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              LinkedIn URL
            </label>
            <p className="mt-1 text-sm text-gray-900 dark:text-white">
              {profile.linkedin_url ? (
                <a 
                  href={profile.linkedin_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400"
                >
                  {profile.linkedin_url}
                </a>
              ) : (
                'Not provided'
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Professional Information */}
      <div>
        <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">
          Professional Details
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Current Title
            </label>
            <p className="mt-1 text-sm text-gray-900 dark:text-white">
              {profile.current_title || 'Not provided'}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Current Company
            </label>
            <p className="mt-1 text-sm text-gray-900 dark:text-white">
              {profile.current_company || 'Not provided'}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Years of Experience
            </label>
            <p className="mt-1 text-sm text-gray-900 dark:text-white">
              {profile.years_experience ? `${profile.years_experience} years` : 'Not provided'}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Education Level
            </label>
            <p className="mt-1 text-sm text-gray-900 dark:text-white">
              {profile.education_level || 'Not provided'}
            </p>
          </div>
        </div>
      </div>

      {/* Skills */}
      <div>
        <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">
          Skills
        </h4>
        {profile.skills && profile.skills.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {profile.skills.map((skill: any, index: number) => (
              <Badge key={index} variant="secondary">
                {skill.name} ({skill.level})
              </Badge>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            No skills added yet
          </p>
        )}
      </div>

      {/* Location Preferences */}
      <div>
        <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">
          Location Preferences
        </h4>
        {profile.location_preferences && profile.location_preferences.length > 0 ? (
          <div className="space-y-2">
            {profile.location_preferences.map((location: any, index: number) => (
              <div key={index} className="flex items-center space-x-2">
                <Badge variant={location.is_remote ? "success" : "info"}>
                  {location.is_remote ? 'Remote' : 'On-site'}
                </Badge>
                <span className="text-sm text-gray-900 dark:text-white">
                  {location.city}, {location.country}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            No location preferences set
          </p>
        )}
      </div>
    </div>
  )
}