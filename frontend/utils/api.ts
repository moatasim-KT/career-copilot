import { ApiResponse, PaginatedResponse } from '@/types'
import { offlineStorage, offlineUtils } from './offline-storage'

class ApiClient {
  private baseURL: string
  private isOnline: boolean = true

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    this.setupNetworkMonitoring()
  }

  private setupNetworkMonitoring(): void {
    if (typeof window !== 'undefined') {
      this.isOnline = navigator.onLine
      
      offlineUtils.registerNetworkListeners(
        () => {
          this.isOnline = true
          this.syncPendingActions()
        },
        () => {
          this.isOnline = false
        }
      )
    }
  }

  private getCacheKey(endpoint: string, options?: RequestInit): string {
    const method = options?.method || 'GET'
    const body = options?.body || ''
    return `${method}:${endpoint}:${body}`
  }

  private async syncPendingActions(): Promise<void> {
    try {
      const pendingActions = await offlineStorage.getPendingActions()
      
      for (const action of pendingActions) {
        try {
          switch (action.type) {
            case 'job-application':
              await this.createJob(action.data)
              break
            case 'profile-update':
              await this.updateProfile(action.data)
              break
            case 'job-status-update':
              await this.updateJob(action.data.jobId, action.data)
              break
            default:
              console.warn('Unknown action type:', action.type)
          }
          
          await offlineStorage.removePendingAction(action.id)
        } catch (error) {
          console.error('Failed to sync action:', action.id, error)
        }
      }
    } catch (error) {
      console.error('Failed to sync pending actions:', error)
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}/api/v1${endpoint}`
    const cacheKey = this.getCacheKey(endpoint, options)
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    // Add auth token if available
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      }
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || `HTTP error! status: ${response.status}`)
      }

      // Cache successful GET responses
      if (options.method === 'GET' || !options.method) {
        await offlineStorage.cacheData(cacheKey, data, 60) // Cache for 1 hour
      }

      return {
        success: true,
        data,
      }
    } catch (error) {
      console.error('API request failed:', error)
      
      // If offline and it's a GET request, try cache
      if (!this.isOnline && (options.method === 'GET' || !options.method)) {
        const cachedData = await offlineStorage.getCachedData(cacheKey)
        if (cachedData) {
          return {
            success: true,
            data: {
              ...cachedData,
              offline: true,
              cached_at: new Date().toISOString(),
              message: 'This data was loaded from cache while offline'
            },
          }
        }
      }

      // If offline and it's a write operation, store for later sync
      if (!this.isOnline && (options.method === 'POST' || options.method === 'PUT' || options.method === 'PATCH')) {
        const actionType = this.getActionTypeFromEndpoint(endpoint, options.method)
        if (actionType) {
          const actionData = options.body ? JSON.parse(options.body as string) : {}
          await offlineStorage.storePendingAction(actionType, actionData)
          
          return {
            success: true,
            data: {
              success: true,
              offline: true,
              message: 'Action stored for sync when online',
              pending: true
            } as T,
          }
        }
      }

      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      }
    }
  }

  private getActionTypeFromEndpoint(endpoint: string, method?: string): string | null {
    if (endpoint.includes('/jobs') && method === 'POST') return 'job-application'
    if (endpoint.includes('/jobs') && (method === 'PUT' || method === 'PATCH')) return 'job-status-update'
    if (endpoint.includes('/profile') && (method === 'PUT' || method === 'PATCH')) return 'profile-update'
    return null
  }

  // Auth endpoints
  async login(email: string, password: string) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async register(email: string, password: string) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async logout() {
    return this.request('/auth/logout', {
      method: 'POST',
    })
  }

  // Job endpoints
  async getJobs(params?: {
    page?: number
    pageSize?: number
    search?: string
    status?: string
  }) {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.append('page', params.page.toString())
    if (params?.pageSize) searchParams.append('page_size', params.pageSize.toString())
    if (params?.search) searchParams.append('search', params.search)
    if (params?.status) searchParams.append('status', params.status)

    const query = searchParams.toString()
    return this.request<PaginatedResponse<any>>(`/jobs${query ? `?${query}` : ''}`)
  }

  async getJob(id: number) {
    return this.request(`/jobs/${id}`)
  }

  async createJob(jobData: any) {
    return this.request('/jobs', {
      method: 'POST',
      body: JSON.stringify(jobData),
    })
  }

  async updateJob(id: number, jobData: any) {
    return this.request(`/jobs/${id}`, {
      method: 'PUT',
      body: JSON.stringify(jobData),
    })
  }

  async deleteJob(id: number) {
    return this.request(`/jobs/${id}`, {
      method: 'DELETE',
    })
  }

  // User endpoints
  async getProfile() {
    return this.request('/users/profile')
  }

  async updateProfile(profileData: any) {
    return this.request('/users/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    })
  }

  // Analytics endpoints
  async getAnalytics() {
    return this.request('/analytics')
  }

  async getSkillGapAnalysis() {
    return this.request('/analytics/skill-gap')
  }

  // Health check
  async healthCheck() {
    return this.request('/')
  }

  // Offline-specific methods
  async getOfflineJobs() {
    return offlineStorage.getOfflineJobs()
  }

  async getOfflineProfile() {
    return offlineStorage.getUserProfile()
  }

  isOffline(): boolean {
    return !this.isOnline
  }

  async getPendingActionsCount(): Promise<number> {
    const actions = await offlineStorage.getPendingActions()
    return actions.length
  }

  async clearOfflineData(): Promise<void> {
    return offlineStorage.clearAllData()
  }

  async getStorageStats() {
    return offlineStorage.getStorageStats()
  }

  // Data export methods
  async exportUserData(format: 'json' | 'csv' = 'json') {
    return this.request(`/export/user-data?format=${format}`)
  }

  async exportJobsCSV() {
    const response = await fetch(`${this.baseURL}/api/v1/export/jobs/csv`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
      },
    })
    
    if (!response.ok) {
      throw new Error('Failed to export jobs')
    }
    
    return response.blob()
  }

  async importUserData(data: any) {
    return this.request('/export/import', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Enhanced offline and export methods
  async getOfflineCapabilities() {
    return this.request('/offline/capabilities')
  }

  async getDegradationStatus() {
    return this.request('/offline/degradation-status')
  }

  async enableCompleteOfflineMode() {
    return this.request('/offline/complete-offline', {
      method: 'POST',
    })
  }

  async exportOfflinePackage() {
    return this.request('/export/offline-package')
  }

  async exportWithOfflineSupport(includeOfflineData: boolean = true) {
    return this.request(`/export/with-offline-support?include_offline_data=${includeOfflineData}`)
  }

  async prepareOfflineData() {
    return this.request('/offline/prepare', {
      method: 'POST',
    })
  }

  async getOfflineStatus() {
    return this.request('/offline/status')
  }

  // Saved searches endpoints
  async getSavedSearches() {
    return this.request('/saved-searches')
  }

  async saveSearch(searchData: any) {
    return this.request('/saved-searches', {
      method: 'POST',
      body: JSON.stringify(searchData),
    })
  }

  async updateSearchLastUsed(searchId: string) {
    return this.request(`/saved-searches/${searchId}/last-used`, {
      method: 'PATCH',
    })
  }

  async deleteSavedSearch(searchId: string) {
    return this.request(`/saved-searches/${searchId}`, {
      method: 'DELETE',
    })
  }

  async toggleDefaultSearch(searchId: string) {
    return this.request(`/saved-searches/${searchId}/toggle-default`, {
      method: 'PATCH',
    })
  }

  // Dashboard layout endpoints
  async getDashboardLayouts() {
    return this.request('/dashboard/layouts')
  }

  async saveDashboardLayout(layoutData: any) {
    return this.request('/dashboard/layouts', {
      method: 'POST',
      body: JSON.stringify(layoutData),
    })
  }

  async updateDashboardLayout(layoutId: string, layoutData: any) {
    return this.request(`/dashboard/layouts/${layoutId}`, {
      method: 'PUT',
      body: JSON.stringify(layoutData),
    })
  }

  async deleteDashboardLayout(layoutId: string) {
    return this.request(`/dashboard/layouts/${layoutId}`, {
      method: 'DELETE',
    })
  }

  async setDefaultDashboardLayout(layoutId: string) {
    return this.request(`/dashboard/layouts/${layoutId}/set-default`, {
      method: 'PATCH',
    })
  }

  // Graceful degradation helpers
  async withFallback<T>(
    primaryAction: () => Promise<T>,
    fallbackAction: () => Promise<T>,
    fallbackMessage?: string
  ): Promise<T & { fallback?: boolean; message?: string }> {
    try {
      const result = await primaryAction()
      return result
    } catch (error) {
      console.warn('Primary action failed, using fallback:', error)
      const fallbackResult = await fallbackAction()
      return {
        ...fallbackResult,
        fallback: true,
        message: fallbackMessage || 'Using cached data due to connectivity issues'
      }
    }
  }
}

export const apiClient = new ApiClient()
export default apiClient