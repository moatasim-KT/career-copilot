import { useState, useEffect } from 'react'
import { api } from '@/utils/api'

interface UserProfile {
  first_name?: string
  last_name?: string
  phone?: string
  linkedin_url?: string
  portfolio_url?: string
  github_url?: string
  current_title?: string
  current_company?: string
  years_experience?: number
  education_level?: string
  skills: Array<{
    name: string
    level: string
    years_experience?: number
  }>
  location_preferences: Array<{
    city: string
    state?: string
    country: string
    is_remote: boolean
  }>
  career_preferences: {
    salary_min?: number
    salary_max?: number
    currency: string
    company_sizes: string[]
    industries: string[]
    job_types: string[]
    remote_preference: string
    travel_willingness: string
  }
  career_goals: {
    target_roles: string[]
    career_level: string
    time_horizon: string
    learning_goals: string[]
    certifications_desired: string[]
  }
  profile_completion: number
  last_updated?: string
  settings?: any
}

interface UserSettings {
  notifications?: {
    morning_briefing: boolean
    evening_summary: boolean
    job_recommendations: boolean
    application_reminders: boolean
    interview_reminders: boolean
    email_time: string
    timezone: string
  }
  ui_preferences?: {
    theme: string
    dashboard_layout: string
    items_per_page: number
    default_job_view: string
  }
  privacy_settings?: Record<string, any>
}

export function useProfile() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProfile = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/profile/profile')
      setProfile(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load profile')
    } finally {
      setLoading(false)
    }
  }

  const updateProfile = async (profileData: Partial<UserProfile>) => {
    try {
      setError(null)
      const response = await api.put('/profile/profile', profileData)
      setProfile(response.data)
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update profile')
      throw err
    }
  }

  const updateSettings = async (settingsData: UserSettings) => {
    try {
      setError(null)
      await api.put('/profile/settings', settingsData)
      // Refresh profile to get updated settings
      await fetchProfile()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update settings')
      throw err
    }
  }

  useEffect(() => {
    fetchProfile()
  }, [])

  return {
    profile,
    loading,
    error,
    updateProfile,
    updateSettings,
    refetch: fetchProfile
  }
}

export function useApplicationHistory() {
  const [history, setHistory] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHistory = async (params?: {
    page?: number
    per_page?: number
    status_filter?: string
    date_from?: string
    date_to?: string
  }) => {
    try {
      setLoading(true)
      setError(null)
      const queryParams = new URLSearchParams()
      
      if (params?.page) queryParams.append('page', params.page.toString())
      if (params?.per_page) queryParams.append('per_page', params.per_page.toString())
      if (params?.status_filter) queryParams.append('status_filter', params.status_filter)
      if (params?.date_from) queryParams.append('date_from', params.date_from)
      if (params?.date_to) queryParams.append('date_to', params.date_to)

      const response = await api.get(`/profile/application-history?${queryParams}`)
      setHistory(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load application history')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  return {
    history,
    loading,
    error,
    refetch: fetchHistory
  }
}

export function useProgressStats() {
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/profile/progress-stats')
      setStats(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load progress statistics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  return {
    stats,
    loading,
    error,
    refetch: fetchStats
  }
}

export function useDocumentSummary() {
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSummary = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/profile/documents')
      setSummary(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load document summary')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSummary()
  }, [])

  return {
    summary,
    loading,
    error,
    refetch: fetchSummary
  }
}

export function useDashboardStats() {
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/profile/dashboard-stats')
      setStats(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard statistics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  return {
    stats,
    loading,
    error,
    refetch: fetchStats
  }
}