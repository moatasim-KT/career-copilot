export interface Job {
  id: number
  user_id: number
  title: string
  company: string
  location?: string
  salary_min?: number
  salary_max?: number
  currency: string
  requirements?: Record<string, any>
  description?: string
  application_url?: string
  status: 'not_applied' | 'applied' | 'phone_screen' | 'interview_scheduled' | 'interviewed' | 'offer_received' | 'rejected' | 'withdrawn' | 'archived'
  source: 'manual' | 'scraped' | 'api' | 'rss' | 'referral'
  date_posted?: string
  date_added: string
  date_applied?: string
  recommendation_score?: number
  tags: string[]
  notes?: string
  created_at: string
  updated_at: string
}

export interface User {
  id: number
  email: string
  profile: UserProfile
  settings: UserSettings
  createdAt: string
  updatedAt: string
}

export interface UserProfile {
  skills: string[]
  experienceLevel: 'entry' | 'mid' | 'senior' | 'lead'
  locations: string[]
  preferences: {
    salaryMin?: number
    companySize?: string[]
    industries?: string[]
    remotePreference?: 'onsite' | 'hybrid' | 'remote' | 'any'
  }
}

export interface UserSettings {
  theme: 'light' | 'dark' | 'system'
  notifications: {
    email: boolean
    browser: boolean
    dailyBriefing: boolean
    jobAlerts: boolean
  }
  privacy: {
    profileVisibility: 'public' | 'private'
    dataSharing: boolean
  }
}

export interface Analytics {
  totalJobs: number
  totalApplications: number
  interviewCount: number
  successRate: number
  applicationsByStatus: Record<string, number>
  applicationsByMonth: Array<{
    month: string
    count: number
  }>
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}