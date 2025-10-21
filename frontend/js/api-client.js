/**
 * API Client for Career Co-Pilot Backend Communication
 * Handles all HTTP requests to the backend API with error handling and retry logic
 */

class APIClient {
    constructor(baseURL = '/api/v1') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
        this.retryAttempts = 3;
        this.retryDelay = 1000; // 1 second
        this.accessToken = null;
    }

    /**
     * Set authentication token
     */
    setAuthToken(token) {
        this.accessToken = token;
    }

    /**
     * Clear authentication token
     */
    clearAuthToken() {
        this.accessToken = null;
    }

    /**
     * Get authentication headers
     */
    getAuthHeaders() {
        const headers = { ...this.defaultHeaders };
        if (this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }
        return headers;
    }

    /**
     * Make HTTP request with retry logic and error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.getAuthHeaders(), ...options.headers },
            ...options
        };

        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                const response = await fetch(url, config);
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new APIError(
                        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
                        response.status,
                        errorData
                    );
                }

                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                }
                return await response.text();

            } catch (error) {
                if (attempt === this.retryAttempts || !this.shouldRetry(error)) {
                    throw error;
                }
                
                console.warn(`API request failed (attempt ${attempt}/${this.retryAttempts}):`, error.message);
                await this.delay(this.retryDelay * attempt);
            }
        }
    }

    /**
     * Determine if request should be retried
     */
    shouldRetry(error) {
        if (error instanceof APIError) {
            // Retry on server errors (5xx) and some client errors
            return error.status >= 500 || error.status === 429 || error.status === 408;
        }
        // Retry on network errors
        return error.name === 'TypeError' || error.name === 'NetworkError';
    }

    /**
     * Delay utility for retry logic
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Authentication API Methods

    /**
     * Exchange Firebase ID token for JWT access token
     */
    async exchangeFirebaseToken(firebaseToken) {
        return await this.request('/auth/token/exchange', {
            method: 'POST',
            body: JSON.stringify({ firebase_token: firebaseToken })
        });
    }

    /**
     * Get current user information
     */
    async getCurrentUser() {
        return await this.request('/auth/me');
    }

    /**
     * Update user profile
     */
    async updateUserProfile(profileData) {
        return await this.request('/auth/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    }

    /**
     * Logout user
     */
    async logout() {
        return await this.request('/auth/logout', {
            method: 'POST'
        });
    }

    /**
     * Validate authentication token
     */
    async validateToken() {
        return await this.request('/auth/validate');
    }

    // Job Application API Methods

    /**
     * Get all job applications with optional filters
     */
    async getJobs(filters = {}) {
        const params = new URLSearchParams();
        
        if (filters.status) params.append('status', filters.status);
        if (filters.company) params.append('company', filters.company);
        if (filters.skip) params.append('skip', filters.skip);
        if (filters.limit) params.append('limit', filters.limit);

        const queryString = params.toString();
        const endpoint = `/jobs/applications${queryString ? `?${queryString}` : ''}`;
        
        return await this.request(endpoint);
    }

    /**
     * Get single job application by ID
     */
    async getJob(jobId) {
        return await this.request(`/jobs/applications/${jobId}`);
    }

    /**
     * Create new job application
     */
    async createJob(jobData) {
        return await this.request('/jobs/applications', {
            method: 'POST',
            body: JSON.stringify(jobData)
        });
    }

    /**
     * Update existing job application
     */
    async updateJob(jobId, jobData) {
        return await this.request(`/jobs/applications/${jobId}`, {
            method: 'PUT',
            body: JSON.stringify(jobData)
        });
    }

    /**
     * Delete job application
     */
    async deleteJob(jobId) {
        return await this.request(`/jobs/applications/${jobId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Update job status only
     */
    async updateJobStatus(jobId, status) {
        return await this.updateJob(jobId, { status });
    }

    /**
     * Get application statistics
     */
    async getStatistics() {
        return await this.request('/jobs/statistics');
    }

    // Interview API Methods

    /**
     * Create interview for job application
     */
    async createInterview(applicationId, interviewData) {
        return await this.request(`/jobs/applications/${applicationId}/interviews`, {
            method: 'POST',
            body: JSON.stringify(interviewData)
        });
    }

    /**
     * Get interviews for job application
     */
    async getInterviews(applicationId) {
        return await this.request(`/jobs/applications/${applicationId}/interviews`);
    }

    // Contact API Methods

    /**
     * Create contact for job application
     */
    async createContact(applicationId, contactData) {
        return await this.request(`/jobs/applications/${applicationId}/contacts`, {
            method: 'POST',
            body: JSON.stringify(contactData)
        });
    }

    /**
     * Get contacts for job application
     */
    async getContacts(applicationId) {
        return await this.request(`/jobs/applications/${applicationId}/contacts`);
    }

    // Analytics API Methods (if available)

    /**
     * Get analytics dashboard data
     */
    async getAnalyticsDashboard(timePeriod = '30d') {
        try {
            return await this.request(`/analytics/dashboard?time_period=${timePeriod}`);
        } catch (error) {
            console.warn('Analytics not available:', error.message);
            return null;
        }
    }

    /**
     * Get skill gap analysis
     */
    async getSkillGapAnalysis() {
        try {
            return await this.request('/analytics/skill-gap');
        } catch (error) {
            console.warn('Skill gap analysis not available:', error.message);
            return null;
        }
    }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, status, data = {}) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
}

/**
 * Toast notification system for user feedback
 */
class ToastNotification {
    static show(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast-notification transform transition-all duration-300 ease-in-out translate-x-full opacity-0 max-w-sm w-full bg-white dark:bg-gray-800 shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden`;
        
        const typeClasses = {
            success: 'border-l-4 border-green-400',
            error: 'border-l-4 border-red-400',
            warning: 'border-l-4 border-yellow-400',
            info: 'border-l-4 border-blue-400'
        };

        const typeIcons = {
            success: `<svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>`,
            error: `<svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /></svg>`,
            warning: `<svg class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>`,
            info: `<svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" /></svg>`
        };

        toast.className += ` ${typeClasses[type] || typeClasses.info}`;
        
        toast.innerHTML = `
            <div class="p-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        ${typeIcons[type] || typeIcons.info}
                    </div>
                    <div class="ml-3 w-0 flex-1 pt-0.5">
                        <p class="text-sm font-medium text-gray-900 dark:text-white">
                            ${message}
                        </p>
                    </div>
                    <div class="ml-4 flex-shrink-0 flex">
                        <button class="toast-close bg-white dark:bg-gray-800 rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                            <span class="sr-only">Close</span>
                            <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;

        container.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
            toast.classList.add('translate-x-0', 'opacity-100');
        }, 100);

        // Setup close button
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.hide(toast);
        });

        // Auto-hide after duration
        if (duration > 0) {
            setTimeout(() => {
                this.hide(toast);
            }, duration);
        }

        return toast;
    }

    static hide(toast) {
        toast.classList.remove('translate-x-0', 'opacity-100');
        toast.classList.add('translate-x-full', 'opacity-0');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    static success(message, duration) {
        return this.show(message, 'success', duration);
    }

    static error(message, duration) {
        return this.show(message, 'error', duration);
    }

    static warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    static info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// Export for use in other modules
window.APIClient = APIClient;
window.APIError = APIError;
window.ToastNotification = ToastNotification;