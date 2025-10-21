import { useState } from 'react'
import { Button, Input, Badge } from '@/components/ui'
import { PlusIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface ProfileEditorProps {
  profile: any
  onSave: (profile: any) => void
  onCancel: () => void
}

export function ProfileEditor({ profile, onSave, onCancel }: ProfileEditorProps) {
  const [formData, setFormData] = useState({
    first_name: profile?.first_name || '',
    last_name: profile?.last_name || '',
    phone: profile?.phone || '',
    linkedin_url: profile?.linkedin_url || '',
    portfolio_url: profile?.portfolio_url || '',
    github_url: profile?.github_url || '',
    current_title: profile?.current_title || '',
    current_company: profile?.current_company || '',
    years_experience: profile?.years_experience || '',
    education_level: profile?.education_level || '',
    skills: profile?.skills || [],
    location_preferences: profile?.location_preferences || [],
    career_preferences: {
      salary_min: profile?.career_preferences?.salary_min || '',
      salary_max: profile?.career_preferences?.salary_max || '',
      currency: profile?.career_preferences?.currency || 'USD',
      company_sizes: profile?.career_preferences?.company_sizes || [],
      industries: profile?.career_preferences?.industries || [],
      job_types: profile?.career_preferences?.job_types || [],
      remote_preference: profile?.career_preferences?.remote_preference || 'hybrid',
      travel_willingness: profile?.career_preferences?.travel_willingness || 'minimal'
    },
    career_goals: {
      target_roles: profile?.career_goals?.target_roles || [],
      career_level: profile?.career_goals?.career_level || 'mid',
      time_horizon: profile?.career_goals?.time_horizon || '1_year',
      learning_goals: profile?.career_goals?.learning_goals || [],
      certifications_desired: profile?.career_goals?.certifications_desired || []
    }
  })

  const [newSkill, setNewSkill] = useState({ name: '', level: 'intermediate', years_experience: '' })
  const [newLocation, setNewLocation] = useState({ city: '', state: '', country: '', is_remote: false })
  const [newTargetRole, setNewTargetRole] = useState('')
  const [newLearningGoal, setNewLearningGoal] = useState('')

  const handleInputChange = (field: string, value: any) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.')
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent as keyof typeof prev],
          [child]: value
        }
      }))
    } else {
      setFormData(prev => ({ ...prev, [field]: value }))
    }
  }

  const addSkill = () => {
    if (newSkill.name.trim()) {
      const skill = {
        name: newSkill.name.trim(),
        level: newSkill.level,
        years_experience: newSkill.years_experience ? parseInt(newSkill.years_experience) : undefined
      }
      setFormData(prev => ({
        ...prev,
        skills: [...prev.skills, skill]
      }))
      setNewSkill({ name: '', level: 'intermediate', years_experience: '' })
    }
  }

  const removeSkill = (index: number) => {
    setFormData(prev => ({
      ...prev,
      skills: prev.skills.filter((_: any, i: number) => i !== index)
    }))
  }

  const addLocation = () => {
    if (newLocation.city.trim() && newLocation.country.trim()) {
      setFormData(prev => ({
        ...prev,
        location_preferences: [...prev.location_preferences, { ...newLocation }]
      }))
      setNewLocation({ city: '', state: '', country: '', is_remote: false })
    }
  }

  const removeLocation = (index: number) => {
    setFormData(prev => ({
      ...prev,
      location_preferences: prev.location_preferences.filter((_: any, i: number) => i !== index)
    }))
  }

  const addTargetRole = () => {
    if (newTargetRole.trim()) {
      setFormData(prev => ({
        ...prev,
        career_goals: {
          ...prev.career_goals,
          target_roles: [...prev.career_goals.target_roles, newTargetRole.trim()]
        }
      }))
      setNewTargetRole('')
    }
  }

  const removeTargetRole = (index: number) => {
    setFormData(prev => ({
      ...prev,
      career_goals: {
        ...prev.career_goals,
        target_roles: prev.career_goals.target_roles.filter((_: any, i: number) => i !== index)
      }
    }))
  }

  const addLearningGoal = () => {
    if (newLearningGoal.trim()) {
      setFormData(prev => ({
        ...prev,
        career_goals: {
          ...prev.career_goals,
          learning_goals: [...prev.career_goals.learning_goals, newLearningGoal.trim()]
        }
      }))
      setNewLearningGoal('')
    }
  }

  const removeLearningGoal = (index: number) => {
    setFormData(prev => ({
      ...prev,
      career_goals: {
        ...prev.career_goals,
        learning_goals: prev.career_goals.learning_goals.filter((_: any, i: number) => i !== index)
      }
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Personal Information */}
      <div>
        <h4 className="text-md font-medium text-gray-900 dark:text-white mb-4">
          Personal Information
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="First Name"
            value={formData.first_name}
            onChange={(e) => handleInputChange('first_name', e.target.value)}
            placeholder="Enter your first name"
          />
          <Input
            label="Last Name"
            value={formData.last_name}
            onChange={(e) => handleInputChange('last_name', e.target.value)}
            placeholder="Enter your last name"
          />
          <Input
            label="Phone"
            value={formData.phone}
            onChange={(e) => handleInputChange('phone', e.target.value)}
            placeholder="Enter your phone number"
          />
          <Input
            label="LinkedIn URL"
            value={formData.linkedin_url}
            onChange={(e) => handleInputChange('linkedin_url', e.target.value)}
            placeholder="https://linkedin.com/in/yourprofile"
          />
          <Input
            label="Portfolio URL"
            value={formData.portfolio_url}
            onChange={(e) => handleInputChange('portfolio_url', e.target.value)}
            placeholder="https://yourportfolio.com"
          />
          <Input
            label="GitHub URL"
            value={formData.github_url}
            onChange={(e) => handleInputChange('github_url', e.target.value)}
            placeholder="https://github.com/yourusername"
          />
        </div>
      </div>

      {/* Professional Information */}
      <div>
        <h4 className="text-md font-medium text-gray-900 dark:text-white mb-4">
          Professional Information
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Current Title"
            value={formData.current_title}
            onChange={(e) => handleInputChange('current_title', e.target.value)}
            placeholder="e.g., Senior Software Engineer"
          />
          <Input
            label="Current Company"
            value={formData.current_company}
            onChange={(e) => handleInputChange('current_company', e.target.value)}
            placeholder="e.g., TechCorp Inc."
          />
          <Input
            label="Years of Experience"
            type="number"
            value={formData.years_experience}
            onChange={(e) => handleInputChange('years_experience', parseInt(e.target.value) || '')}
            placeholder="e.g., 5"
            min="0"
            max="50"
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Education Level
            </label>
            <select
              className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={formData.education_level}
              onChange={(e) => handleInputChange('education_level', e.target.value)}
            >
              <option value="">Select education level</option>
              <option value="high_school">High School</option>
              <option value="associate">Associate Degree</option>
              <option value="bachelor">Bachelor's Degree</option>
              <option value="master">Master's Degree</option>
              <option value="phd">PhD</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>
      </div>

      {/* Skills */}
      <div>
        <h4 className="text-md font-medium text-gray-900 dark:text-white mb-4">
          Skills
        </h4>
        
        {/* Existing Skills */}
        {formData.skills.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-2">
              {formData.skills.map((skill: any, index: number) => (
                <Badge key={index} variant="secondary" className="flex items-center space-x-2">
                  <span>{skill.name} ({skill.level})</span>
                  <button
                    type="button"
                    onClick={() => removeSkill(index)}
                    className="ml-2 text-red-500 hover:text-red-700"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Add New Skill */}
        <div className="flex space-x-2">
          <Input
            placeholder="Skill name"
            value={newSkill.name}
            onChange={(e) => setNewSkill(prev => ({ ...prev, name: e.target.value }))}
            className="flex-1"
          />
          <select
            className="w-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={newSkill.level}
            onChange={(e) => setNewSkill(prev => ({ ...prev, level: e.target.value }))}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
            <option value="expert">Expert</option>
          </select>
          <Input
            type="number"
            placeholder="Years"
            value={newSkill.years_experience}
            onChange={(e) => setNewSkill(prev => ({ ...prev, years_experience: e.target.value }))}
            className="w-20"
            min="0"
            max="50"
          />
          <Button type="button" onClick={addSkill} variant="secondary">
            <PlusIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Location Preferences */}
      <div>
        <h4 className="text-md font-medium text-gray-900 dark:text-white mb-4">
          Location Preferences
        </h4>
        
        {/* Existing Locations */}
        {formData.location_preferences.length > 0 && (
          <div className="mb-4 space-y-2">
            {formData.location_preferences.map((location: any, index: number) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Badge variant={location.is_remote ? "success" : "info"}>
                    {location.is_remote ? 'Remote' : 'On-site'}
                  </Badge>
                  <span className="text-sm">
                    {location.city}, {location.country}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => removeLocation(index)}
                  className="text-red-500 hover:text-red-700"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Add New Location */}
        <div className="flex space-x-2">
          <Input
            placeholder="City"
            value={newLocation.city}
            onChange={(e) => setNewLocation(prev => ({ ...prev, city: e.target.value }))}
            className="flex-1"
          />
          <Input
            placeholder="State (optional)"
            value={newLocation.state}
            onChange={(e) => setNewLocation(prev => ({ ...prev, state: e.target.value }))}
            className="flex-1"
          />
          <Input
            placeholder="Country"
            value={newLocation.country}
            onChange={(e) => setNewLocation(prev => ({ ...prev, country: e.target.value }))}
            className="flex-1"
          />
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={newLocation.is_remote}
              onChange={(e) => setNewLocation(prev => ({ ...prev, is_remote: e.target.checked }))}
              className="rounded"
            />
            <span className="text-sm">Remote</span>
          </label>
          <Button type="button" onClick={addLocation} variant="secondary">
            <PlusIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Career Goals */}
      <div>
        <h4 className="text-md font-medium text-gray-900 dark:text-white mb-4">
          Career Goals
        </h4>
        
        <div className="space-y-4">
          {/* Target Roles */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Target Roles
            </label>
            {formData.career_goals.target_roles.length > 0 && (
              <div className="mb-2 flex flex-wrap gap-2">
                {formData.career_goals.target_roles.map((role: string, index: number) => (
                  <Badge key={index} variant="info" className="flex items-center space-x-2">
                    <span>{role}</span>
                    <button
                      type="button"
                      onClick={() => removeTargetRole(index)}
                      className="ml-2 text-red-500 hover:text-red-700"
                    >
                      <XMarkIcon className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
            <div className="flex space-x-2">
              <Input
                placeholder="e.g., Senior Developer, Tech Lead"
                value={newTargetRole}
                onChange={(e) => setNewTargetRole(e.target.value)}
                className="flex-1"
              />
              <Button type="button" onClick={addTargetRole} variant="secondary">
                <PlusIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Career Level and Time Horizon */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Career Level
              </label>
              <select
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={formData.career_goals.career_level}
                onChange={(e) => handleInputChange('career_goals.career_level', e.target.value)}
              >
                <option value="entry">Entry Level</option>
                <option value="junior">Junior</option>
                <option value="mid">Mid Level</option>
                <option value="senior">Senior</option>
                <option value="lead">Lead</option>
                <option value="principal">Principal</option>
                <option value="executive">Executive</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Time Horizon
              </label>
              <select
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={formData.career_goals.time_horizon}
                onChange={(e) => handleInputChange('career_goals.time_horizon', e.target.value)}
              >
                <option value="6_months">6 Months</option>
                <option value="1_year">1 Year</option>
                <option value="2_years">2 Years</option>
                <option value="5_years">5 Years</option>
                <option value="long_term">Long Term</option>
              </select>
            </div>
          </div>

          {/* Learning Goals */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Learning Goals
            </label>
            {formData.career_goals.learning_goals.length > 0 && (
              <div className="mb-2 flex flex-wrap gap-2">
                {formData.career_goals.learning_goals.map((goal: string, index: number) => (
                  <Badge key={index} variant="warning" className="flex items-center space-x-2">
                    <span>{goal}</span>
                    <button
                      type="button"
                      onClick={() => removeLearningGoal(index)}
                      className="ml-2 text-red-500 hover:text-red-700"
                    >
                      <XMarkIcon className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
            <div className="flex space-x-2">
              <Input
                placeholder="e.g., Learn React, AWS Certification"
                value={newLearningGoal}
                onChange={(e) => setNewLearningGoal(e.target.value)}
                className="flex-1"
              />
              <Button type="button" onClick={addLearningGoal} variant="secondary">
                <PlusIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200 dark:border-gray-700">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" variant="primary">
          Save Profile
        </Button>
      </div>
    </form>
  )
}