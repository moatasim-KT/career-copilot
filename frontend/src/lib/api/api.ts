/**
 * API Client for Career Copilot Backend
 * Extracted and adapted from Streamlit version
 */

import { z } from 'zod';

import { logger } from '../logger';

import { RecoveryManager, CacheFallbackRecovery, TokenRefreshRecovery, createDefaultRecoveryManager, type RecoveryContext, type TokenRefreshConfig } from './recovery';
import { UserProfileSchema } from './schemas';

// ============================================================================
// Error Classes
// ============================================================================

/**
 * Base API Error class
 */
export class APIError extends Error {
  constructor(
    public statusCode: number,
    message: string,
    public details?: any,
  ) {
    super(message);
    this.name = 'APIError';
    Object.setPrototypeOf(this, APIError.prototype);
  }
}

/**
 * Network connection error
 */
export class NetworkError extends APIError {
  constructor(message: string = 'Network connection failed') {
    super(0, message);
    this.name = 'NetworkError';
    Object.setPrototypeOf(this, NetworkError.prototype);
  }
}

/**
 * Authentication error (401)
 */
export class AuthenticationError extends APIError {
  constructor(message: string = 'Authentication required') {
    super(401, message);
    this.name = 'AuthenticationError';
    Object.setPrototypeOf(this, AuthenticationError.prototype);
  }
}

/**
 * Authorization error (403)
 */
export class AuthorizationError extends APIError {
  constructor(message: string = 'Permission denied') {
    super(403, message);
    this.name = 'AuthorizationError';
    Object.setPrototypeOf(this, AuthorizationError.prototype);
  }
}

/**
 * Not found error (404)
 */
export class NotFoundError extends APIError {
  constructor(message: string = 'Resource not found') {
    super(404, message);
    this.name = 'NotFoundError';
    Object.setPrototypeOf(this, NotFoundError.prototype);
  }
}

/**
 * Validation error (400, 422)
 */
export class ValidationError extends APIError {
  constructor(message: string = 'Validation failed', details?: any) {
    super(400, message, details);
    this.name = 'ValidationError';
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

/**
 * Server error (500+)
 */
export class ServerError extends APIError {
  constructor(message: string = 'Server error occurred') {
    super(500, message);
    this.name = 'ServerError';
    Object.setPrototypeOf(this, ServerError.prototype);
  }
}

/**
 * Timeout error
 */
export class TimeoutError extends APIError {
  constructor(message: string = 'Request timeout') {
    super(408, message);
    this.name = 'TimeoutError';
    Object.setPrototypeOf(this, TimeoutError.prototype);
  }
}

// ============================================================================
// Interceptor Types
// ============================================================================

export interface RequestInterceptor {
  onRequest?: (config: RequestInit, url: string) => RequestInit | Promise<RequestInit>;
  onRequestError?: (error: Error) => void;
}

export interface ResponseInterceptor {
  onResponse?: (response: Response) => Response | Promise<Response>;
  onResponseError?: (error: Error) => void;
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Delay helper for retry logic
 */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Create a promise that rejects after a timeout
 */
function createTimeoutPromise(timeoutMs: number): Promise<never> {
  return new Promise((_, reject) => {
    setTimeout(() => reject(new TimeoutError(`Request timeout after ${timeoutMs}ms`)), timeoutMs);
  });
}

/**
 * Fetch with timeout support
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs: number,
): Promise<Response> {
  const fetchPromise = fetch(url, options);
  const timeoutPromise = createTimeoutPromise(timeoutMs);

  return Promise.race([fetchPromise, timeoutPromise]);
}

/**
 * Fetch with retry logic and exponential backoff
 */
async function fetchWithRetry(
  url: string,
  options: RequestInit,
  retries: number = 3,
  baseDelay: number = 1000,
  timeoutMs?: number,
): Promise<Response> {
  let lastError: Error | undefined;

  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const response = timeoutMs
        ? await fetchWithTimeout(url, options, timeoutMs)
        : await fetch(url, options);

      // If successful or client error (4xx), return immediately
      if (response.ok || (response.status >= 400 && response.status < 500)) {
        return response;
      }

      // Server error (5xx) - retry
      if (attempt < retries - 1) {
        const backoffDelay = baseDelay * Math.pow(2, attempt);
        await delay(backoffDelay);
        continue;
      }

      return response;
    } catch (error) {
      lastError = error as Error;

      // Don't retry timeout errors or abort errors
      if (error instanceof TimeoutError || (error as Error).name === 'AbortError') {
        throw error;
      }

      // Network error - retry
      if (attempt < retries - 1) {
        const backoffDelay = baseDelay * Math.pow(2, attempt);
        await delay(backoffDelay);
        continue;
      }
    }
  }

  // All retries failed
  throw new NetworkError(lastError?.message || 'Network request failed after retries');
}

// ============================================================================
// Type Definitions
// ============================================================================

export interface Job {
  id: number;
  company: string;
  title: string;
  location?: string;
  url?: string;
  salary_range?: string;
  job_type: string;
  description?: string;
  remote: boolean;
  tech_stack: string[];
  responsibilities?: string;
  source: string;
  match_score?: number;
  documents_required?: string[];
  created_at?: string;
}

export interface Application {
  id: number;
  job_id: number;
  job?: Job;
  status: 'interested' | 'applied' | 'interview' | 'offer' | 'rejected' | 'accepted' | 'declined';
  applied_date?: string;
  interview_date?: string;
  response_date?: string;
  notes?: string;
  interview_feedback?: {
    questions: string[];
    skill_areas: string[];
    notes: string;
  };
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  experience_level?: string;
  current_role?: string;
  target_roles?: string[];
  skills?: string[];
  location?: string;
  remote_preference?: boolean;
  prefer_remote_jobs?: boolean; // New field for job scraping preference
  salary_expectation?: string;
}

export interface AnalyticsSummary {
  total_jobs: number;
  total_applications: number;
  pending_applications: number;
  interviews_scheduled: number;
  offers_received: number;
  rejections_received: number;
  acceptance_rate: number;
  daily_applications_today: number;
  weekly_applications: number;
  monthly_applications: number;
  daily_application_goal: number;
  daily_goal_progress: number;
  top_skills_in_jobs: Array<{ skill: string; count: number }>;
  top_companies_applied: Array<{ company: string; count: number }>;
  application_status_breakdown: Record<string, number>;
  total_jobs_trend: { trend: 'up' | 'down' | 'neutral'; value: number; };
  total_applications_trend: { trend: 'up' | 'down' | 'neutral'; value: number; };
  interviews_scheduled_trend: { trend: 'up' | 'down' | 'neutral'; value: number; };
  offers_received_trend: { trend: 'up' | 'down' | 'neutral'; value: number; };
}

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
}

export class APIClient {
  private baseUrl: string;
  private token: string | null = null;
  private activeRequests: Map<string, AbortController> = new Map();
  private pendingRequests: Map<string, Promise<any>> = new Map();
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];
  private defaultTimeout: number = 30000; // 30 seconds default timeout
  private recoveryManager: RecoveryManager;
  private cacheFallbackStrategy: CacheFallbackRecovery | null = null;
  private tokenRefreshStrategy: TokenRefreshRecovery | null = null;

  constructor(
    baseUrl: string = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8002',
    // recoveryManager?: RecoveryManager // Removed as we'll create it internally
  ) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    // Initialize with default recovery manager
    this.recoveryManager = createDefaultRecoveryManager();

    // Extract cache fallback strategy if present
    this.cacheFallbackStrategy = this.recoveryManager['strategies']?.find(
      s => s.name === 'CacheFallbackRecovery',
    ) as CacheFallbackRecovery || null;

    // Extract token refresh strategy if present
    this.tokenRefreshStrategy = this.recoveryManager['strategies']?.find(
      s => s.name === 'TokenRefreshRecovery',
    ) as TokenRefreshRecovery || null;
  }

  /**
   * Set the function to refresh the authentication token.
   * This should be provided by the authentication context.
   */
  setRefreshTokenFn(refreshTokenFn: () => Promise<string | null>) {
    if (this.tokenRefreshStrategy) {
      this.tokenRefreshStrategy.reset(); // Reset attempts on new function set
      // Remove existing token refresh strategy if any
      this.recoveryManager.removeStrategy('TokenRefreshRecovery');
    }

    const tokenRefreshConfig: TokenRefreshConfig = {
      refreshTokenFn,
      onTokenRefreshed: (newToken) => {
        this.setToken(newToken);
        logger.info('Token refreshed and set in API client.');
      },
      onRefreshFailed: (error) => {
        logger.error('Token refresh failed:', error);
        // TODO: Potentially trigger a global logout or re-authentication flow
      },
      maxRefreshAttempts: 2, // Allow up to 2 refresh attempts
    };

    this.tokenRefreshStrategy = new TokenRefreshRecovery(tokenRefreshConfig);
    this.recoveryManager.addStrategy(this.tokenRefreshStrategy);
  }

  /**
   * Set default timeout for all requests
   */
  setTimeout(timeoutMs: number) {
    this.defaultTimeout = timeoutMs;
  }

  /**
   * Set recovery manager
   */
  setRecoveryManager(manager: RecoveryManager) {
    this.recoveryManager = manager;
    // Update cache fallback reference
    this.cacheFallbackStrategy = this.recoveryManager['strategies']?.find(
      s => s.name === 'CacheFallbackRecovery',
    ) as CacheFallbackRecovery || null;
  }

  /**
   * Get recovery manager
   */
  getRecoveryManager(): RecoveryManager {
    return this.recoveryManager;
  }

  /**
   * Add a request interceptor
   */
  addRequestInterceptor(interceptor: RequestInterceptor) {
    this.requestInterceptors.push(interceptor);
    return () => {
      const index = this.requestInterceptors.indexOf(interceptor);
      if (index > -1) {
        this.requestInterceptors.splice(index, 1);
      }
    };
  }

  /**
   * Add a response interceptor
   */
  addResponseInterceptor(interceptor: ResponseInterceptor) {
    this.responseInterceptors.push(interceptor);
    return () => {
      const index = this.responseInterceptors.indexOf(interceptor);
      if (index > -1) {
        this.responseInterceptors.splice(index, 1);
      }
    };
  }

  /**
   * Apply request interceptors
   */
  private async applyRequestInterceptors(config: RequestInit, url: string): Promise<RequestInit> {
    let modifiedConfig = config;
    logger.debug(`[API] Requesting: ${url}`, { config });
    for (const interceptor of this.requestInterceptors) {
      if (interceptor.onRequest) {
        try {
          modifiedConfig = await interceptor.onRequest(modifiedConfig, url);
        } catch (error) {
          logger.error(`[API] Request Interceptor Error for ${url}:`, error);
          if (interceptor.onRequestError) {
            interceptor.onRequestError(error as Error);
          }
        }
      }
    }
    return modifiedConfig;
  }

  /**
   * Apply response interceptors
   */
  private async applyResponseInterceptors(response: Response): Promise<Response> {
    let modifiedResponse = response;
    logger.debug(`[API] Response received for: ${response.url}`, { response });
    for (const interceptor of this.responseInterceptors) {
      if (interceptor.onResponse) {
        try {
          modifiedResponse = await interceptor.onResponse(modifiedResponse);
        } catch (error) {
          logger.error(`[API] Response Interceptor Error for ${response.url}:`, error);
          if (interceptor.onResponseError) {
            interceptor.onResponseError(error as Error);
          }
        }
      }
    }
    return modifiedResponse;
  }

  setToken(token: string) {
    this.token = token;
  }

  clearToken() {
    this.token = null;
  }

  /**
   * Cancel all active requests
   */
  cancelAllRequests() {
    this.activeRequests.forEach(controller => controller.abort());
    this.activeRequests.clear();
    this.pendingRequests.clear();
  }

  /**
   * Cancel a specific request by ID
   */
  cancelRequest(requestId: string) {
    const controller = this.activeRequests.get(requestId);
    if (controller) {
      controller.abort();
      this.activeRequests.delete(requestId);
      this.pendingRequests.delete(requestId);
    }
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Authentication disabled - no token required
    // All requests automatically use the Moatasim user

    return headers;
  }

  /**
   * Enhanced response handler with proper error types and runtime validation
   */
  private async handleResponse<T>(response: Response, schema?: z.ZodType<T>): Promise<ApiResponse<T>> {
    try {
      if (response.ok) {
        const data = await response.json();
        if (schema) {
          try {
            const validatedData = schema.parse(data);
            return { data: validatedData };
          } catch (error) {
            logger.error('API Response Validation Error:', error);
            if (error instanceof z.ZodError) {
              throw new ValidationError('API response failed schema validation', error.issues);
            }
            throw new ValidationError('API response failed schema validation', []);
          }
        }
        return { data };
      }

      // Handle specific error codes
      const errorText = await response.text();
      let errorMessage = `HTTP ${response.status}: ${errorText}`;

      switch (response.status) {
        case 401:
          throw new AuthenticationError(errorText || 'Authentication required');
        case 403:
          throw new AuthorizationError(errorText || 'Permission denied');
        case 404:
          throw new NotFoundError(errorText || 'Resource not found');
        case 400:
        case 422:
          throw new ValidationError(errorText || 'Validation failed', []);
        case 500:
        case 502:
        case 503:
        case 504:
          throw new ServerError(errorText || 'Server error occurred');
        default:
          throw new APIError(response.status, errorMessage);
      }
    } catch (error) {
      if (error instanceof APIError) {
        return { error: error.message };
      }
      return { error: `Response error: ${error}` };
    }
  }

  /**
   * Make a request with retry, cancellation, deduplication, interceptors, and recovery
   */
  private async makeRequest<T>(
    requestId: string,
    url: string,
    options: RequestInit = {},
    enableRetry: boolean = true,
    timeoutMs?: number,
    responseSchema?: z.ZodType<T>,
  ): Promise<ApiResponse<T>> {
    // Deduplication: Return existing promise if request is pending
    const pendingRequest = this.pendingRequests.get(requestId);
    if (pendingRequest) {
      return pendingRequest;
    }

    // Create abort controller for cancellation
    const controller = new AbortController();
    this.activeRequests.set(requestId, controller);

    const requestPromise = (async () => {
      try {
        // Apply request interceptors
        let requestOptions = await this.applyRequestInterceptors({
          ...options,
          signal: controller.signal,
        }, url);

        const timeout = timeoutMs || this.defaultTimeout;

        const response = enableRetry
          ? await fetchWithRetry(url, requestOptions, 3, 1000, timeout)
          : timeout
            ? await fetchWithTimeout(url, requestOptions, timeout)
            : await fetch(url, requestOptions);

        // Apply response interceptors
        const interceptedResponse = await this.applyResponseInterceptors(response);

        const result = await this.handleResponse<T>(interceptedResponse, responseSchema);

        // Cache successful responses for fallback
        if (result.data && this.cacheFallbackStrategy) {
          await this.cacheFallbackStrategy.cacheResponse(url, requestOptions, result.data);
        }

        return result;
      } catch (error) {
        // Check if request was cancelled
        if (error instanceof Error && error.name === 'AbortError') {
          return { error: 'Request cancelled' };
        }

        // Attempt recovery for errors
        const recoveryContext: RecoveryContext = {
          url,
          options,
          requestId,
          retryCount: 0,
        };

        const recoveredData = await this.recoveryManager.recover<T>(
          error as Error,
          recoveryContext,
        );

        if (recoveredData !== null) {
          return { data: recoveredData };
        }

        // No recovery possible, return error
        if (error instanceof TimeoutError) {
          return { error: error.message };
        }
        if (error instanceof NetworkError) {
          return { error: error.message };
        }
        if (error instanceof APIError) {
          return { error: error.message };
        }
        return { error: `Request error: ${error}` };
      } finally {
        this.activeRequests.delete(requestId);
        this.pendingRequests.delete(requestId);
      }
    })();

    this.pendingRequests.set(requestId, requestPromise);
    return requestPromise;
  }

  // Authentication
  async login(username: string, password: string): Promise<ApiResponse<{ access_token: string; user: UserProfile }>> {
    return this.makeRequest(
      'login',
      `${this.baseUrl}/api/v1/auth/login`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      },
      false, // Don't retry login attempts
      undefined,
      z.object({ access_token: z.string(), user: UserProfileSchema }),
    );
  }

  async register(username: string, email: string, password: string): Promise<ApiResponse<UserProfile>> {
    return this.makeRequest(
      'register',
      `${this.baseUrl}/api/v1/auth/register`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
      },
      false, // Don't retry registration
      undefined,
      UserProfileSchema,
    );
  }

  // Jobs
  async getJobs(skip: number = 0, limit: number = 100): Promise<ApiResponse<Job[]>> {
    return this.makeRequest(
      `getJobs-${skip}-${limit}`,
      `${this.baseUrl}/api/v1/jobs?skip=${skip}&limit=${limit}`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  async searchJobs(query: string, limit: number = 10): Promise<ApiResponse<Job[]>> {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    params.append('limit', limit.toString());

    return this.makeRequest(
      `searchJobs-${query}-${limit}`,
      `${this.baseUrl}/api/v1/jobs/search?${params.toString()}`,
      {
        headers: this.getHeaders(),
      },
      true, // Enable retry
      5000, // 5 second timeout for search
    );
  }

  async createJob(jobData: Partial<Job>): Promise<ApiResponse<Job>> {
    return this.makeRequest(
      'createJob',
      `${this.baseUrl}/api/v1/jobs`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(jobData),
      },
      false, // Don't retry creates to avoid duplicates
    );
  }

  async updateJob(jobId: number, jobData: Partial<Job>): Promise<ApiResponse<Job>> {
    return this.makeRequest(
      `updateJob-${jobId}`,
      `${this.baseUrl}/api/v1/jobs/${jobId}`,
      {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify(jobData),
      },
    );
  }

  async deleteJob(jobId: number): Promise<ApiResponse<void>> {
    return this.makeRequest(
      `deleteJob-${jobId}`,
      `${this.baseUrl}/api/v1/jobs/${jobId}`,
      {
        method: 'DELETE',
        headers: this.getHeaders(),
      },
      false, // Don't retry deletes
    );
  }

  // Applications
  async getApplications(skip: number = 0, limit: number = 100): Promise<ApiResponse<Application[]>> {
    return this.makeRequest(
      `getApplications-${skip}-${limit}`,
      `${this.baseUrl}/api/v1/applications?skip=${skip}&limit=${limit}`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  async searchApplications(query: string, limit: number = 10): Promise<ApiResponse<Application[]>> {
    // Applications endpoint doesn't have a dedicated search, but we can filter by fetching all
    // and filtering client-side, or use the status filter if query matches a status
    const params = new URLSearchParams();
    params.append('limit', limit.toString());

    // Check if query matches a status
    const statuses = ['interested', 'applied', 'interview', 'offer', 'rejected', 'accepted', 'declined'];
    const matchedStatus = statuses.find(s => s.toLowerCase().includes(query.toLowerCase()));
    if (matchedStatus) {
      params.append('status', matchedStatus);
    }

    return this.makeRequest(
      `searchApplications-${query}-${limit}`,
      `${this.baseUrl}/api/v1/applications?${params.toString()}`,
      {
        headers: this.getHeaders(),
      },
      true, // Enable retry
      5000, // 5 second timeout for search
    );
  }

  async createApplication(applicationData: Partial<Application>): Promise<ApiResponse<Application>> {
    return this.makeRequest(
      'createApplication',
      `${this.baseUrl}/api/v1/applications`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(applicationData),
      },
      false, // Don't retry creates to avoid duplicates
    );
  }

  async updateApplication(applicationId: number, applicationData: Partial<Application>): Promise<ApiResponse<Application>> {
    return this.makeRequest(
      `updateApplication-${applicationId}`,
      `${this.baseUrl}/api/v1/applications/${applicationId}`,
      {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify(applicationData),
      },
    );
  }

  async deleteApplication(applicationId: number): Promise<ApiResponse<void>> {
    return this.makeRequest(
      `deleteApplication-${applicationId}`,
      `${this.baseUrl}/api/v1/applications/${applicationId}`,
      {
        method: 'DELETE',
        headers: this.getHeaders(),
      },
      false, // Don't retry deletes
    );
  }

  // Analytics
  async getAnalyticsSummary(): Promise<ApiResponse<AnalyticsSummary>> {
    return this.makeRequest(
      'getAnalyticsSummary',
      `${this.baseUrl}/api/v1/analytics/summary`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  async getComprehensiveAnalytics(days: number = 90): Promise<ApiResponse<any>> {
    return this.makeRequest(
      `getComprehensiveAnalytics-${days}`,
      `${this.baseUrl}/api/v1/analytics/comprehensive-dashboard?days=${days}`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  // User Profile
  async getUserProfile(): Promise<ApiResponse<UserProfile>> {
    return this.makeRequest(
      'getUserProfile',
      `${this.baseUrl}/api/v1/profile`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  async updateUserProfile(profileData: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> {
    return this.makeRequest(
      'updateUserProfile',
      `${this.baseUrl}/api/v1/profile`,
      {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify(profileData),
      },
    );
  }

  // Recommendations
  async getRecommendations(skip: number = 0, limit: number = 10): Promise<ApiResponse<Job[]>> {
    return this.makeRequest(
      `getRecommendations-${skip}-${limit}`,
      `${this.baseUrl}/api/v1/recommendations?skip=${skip}&limit=${limit}`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  // Skill Gap Analysis
  async getSkillGapAnalysis(): Promise<ApiResponse<{
    user_skills: string[];
    missing_skills: string[];
    top_market_skills: string[];
    skill_coverage_percentage: number;
    recommendations: string[];
  }>> {
    return this.makeRequest(
      'getSkillGapAnalysis',
      `${this.baseUrl}/api/v1/skill-gap`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  // Content Generation
  async generateContent(contentType: string, data: any): Promise<ApiResponse<{ generated_content: string }>> {
    return this.makeRequest(
      `generateContent-${contentType}`,
      `${this.baseUrl}/api/v1/content/generate`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ content_type: contentType, ...data }),
      },
      false, // Don't retry content generation
    );
  }

  // Resume Upload and Parsing
  async uploadResume(file: File): Promise<ApiResponse<{ upload_id: string; parsing_status: string }>> {
    const formData = new FormData();
    formData.append('file', file);

    const headers: Record<string, string> = {};
    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    return this.makeRequest(
      'uploadResume',
      `${this.baseUrl}/api/v1/resume/upload`,
      {
        method: 'POST',
        headers,
        body: formData,
      },
      false, // Don't retry file uploads
    );
  }

  async getResumeParsingStatus(uploadId: string): Promise<ApiResponse<{
    parsing_status: string;
    extracted_data?: any;
    suggestions?: any;
  }>> {
    return this.makeRequest(
      `getResumeParsingStatus-${uploadId}`,
      `${this.baseUrl}/api/v1/resume/${uploadId}/status`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  async parseJobDescription(data: { job_url?: string; description_text?: string }): Promise<ApiResponse<{
    extracted_tech_stack: string[];
    requirements: string[];
    parsed_data: any;
  }>> {
    return this.makeRequest(
      'parseJobDescription',
      `${this.baseUrl}/api/v1/jobs/parse-description`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(data),
      },
    );
  }

  // Content Generation
  async generateCoverLetter(data: {
    job_id: number;
    tone?: 'professional' | 'casual' | 'enthusiastic';
    custom_prompt?: string;
  }): Promise<ApiResponse<{ generated_content: string; content_id: string }>> {
    return this.makeRequest(
      `generateCoverLetter-${data.job_id}`,
      `${this.baseUrl}/api/v1/content/cover-letter`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(data),
      },
      false, // Don't retry content generation
    );
  }

  async generateResumeTailoring(data: {
    job_id: number;
    resume_sections?: any;
  }): Promise<ApiResponse<{ tailored_sections: any; suggestions: string[] }>> {
    return this.makeRequest(
      `generateResumeTailoring-${data.job_id}`,
      `${this.baseUrl}/api/v1/content/resume-tailor`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(data),
      },
      false, // Don't retry content generation
    );
  }

  async getGeneratedContent(contentId: string): Promise<ApiResponse<{
    content_type: string;
    generated_content: string;
    user_modifications?: string;
    created_at: string;
  }>> {
    return this.makeRequest(
      `getGeneratedContent-${contentId}`,
      `${this.baseUrl}/api/v1/content/${contentId}`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  async updateGeneratedContent(contentId: string, modifications: string): Promise<ApiResponse<any>> {
    return this.makeRequest(
      `updateGeneratedContent-${contentId}`,
      `${this.baseUrl}/api/v1/content/${contentId}`,
      {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify({ user_modifications: modifications }),
      },
    );
  }

  // Interview Practice
  async startInterviewSession(data: {
    job_id?: number;
    session_type: 'general' | 'job_specific' | 'behavioral' | 'technical';
  }): Promise<ApiResponse<{ session_id: string; first_question: string }>> {
    return this.makeRequest(
      'startInterviewSession',
      `${this.baseUrl}/api/v1/interview/start-session`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(data),
      },
      false, // Don't retry session creation
    );
  }

  async submitInterviewAnswer(sessionId: string, data: {
    answer_text: string;
    question_id: string;
  }): Promise<ApiResponse<{ feedback: any; next_question?: string }>> {
    return this.makeRequest(
      `submitInterviewAnswer-${sessionId}`,
      `${this.baseUrl}/api/v1/interview/${sessionId}/answer`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(data),
      },
      false, // Don't retry answers
    );
  }

  async getInterviewSessionSummary(sessionId: string): Promise<ApiResponse<{
    overall_score: number;
    detailed_feedback: any[];
    improvement_areas: string[];
  }>> {
    return this.makeRequest(
      `getInterviewSessionSummary-${sessionId}`,
      `${this.baseUrl}/api/v1/interview/${sessionId}/summary`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  // Feedback
  async submitFeedback(data: {
    feedback_type: 'recommendation' | 'skill_gap' | 'content_generation' | 'interview_practice';
    target_id: number | string;
    rating: number;
    comments?: string;
  }): Promise<ApiResponse<{ feedback_id: string }>> {
    return this.makeRequest(
      'submitFeedback',
      `${this.baseUrl}/api/v1/feedback`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(data),
      },
      false, // Don't retry feedback submissions
    );
  }

  async getFeedbackSummary(): Promise<ApiResponse<{
    feedback_history: any[];
    impact_on_recommendations: any;
  }>> {
    return this.makeRequest(
      'getFeedbackSummary',
      `${this.baseUrl}/api/v1/feedback/summary`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  // Health Check
  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.makeRequest(
      'healthCheck',
      `${this.baseUrl}/api/v1/health`,
      {},
      false, // Don't retry health checks
    );
  }

  // Notifications
  async getNotifications(skip: number = 0, limit: number = 50): Promise<ApiResponse<any[]>> {
    return this.makeRequest(
      `getNotifications-${skip}-${limit}`,
      `${this.baseUrl}/api/v1/notifications?skip=${skip}&limit=${limit}`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  async markNotificationAsRead(notificationId: string): Promise<ApiResponse<void>> {
    return this.makeRequest(
      `markNotificationAsRead-${notificationId}`,
      `${this.baseUrl}/api/v1/notifications/${notificationId}/read`,
      {
        method: 'PUT',
        headers: this.getHeaders(),
      },
    );
  }

  async markNotificationAsUnread(notificationId: string): Promise<ApiResponse<void>> {
    return this.makeRequest(
      `markNotificationAsUnread-${notificationId}`,
      `${this.baseUrl}/api/v1/notifications/${notificationId}/unread`,
      {
        method: 'PUT',
        headers: this.getHeaders(),
      },
    );
  }

  async markAllNotificationsAsRead(): Promise<ApiResponse<void>> {
    return this.makeRequest(
      'markAllNotificationsAsRead',
      `${this.baseUrl}/api/v1/notifications/read-all`,
      {
        method: 'PUT',
        headers: this.getHeaders(),
      },
    );
  }

  async deleteNotification(notificationId: string): Promise<ApiResponse<void>> {
    return this.makeRequest(
      `deleteNotification-${notificationId}`,
      `${this.baseUrl}/api/v1/notifications/${notificationId}`,
      {
        method: 'DELETE',
        headers: this.getHeaders(),
      },
      false, // Don't retry deletes
    );
  }

  async deleteNotifications(notificationIds: string[]): Promise<ApiResponse<void>> {
    return this.makeRequest(
      'deleteNotifications',
      `${this.baseUrl}/api/v1/notifications/bulk-delete`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ notification_ids: notificationIds }),
      },
      false, // Don't retry deletes
    );
  }

  async getNotificationPreferences(): Promise<ApiResponse<any>> {
    return this.makeRequest(
      'getNotificationPreferences',
      `${this.baseUrl}/api/v1/notifications/preferences`,
      {
        headers: this.getHeaders(),
      },
    );
  }

  async updateNotificationPreferences(preferences: any): Promise<ApiResponse<any>> {
    return this.makeRequest(
      'updateNotificationPreferences',
      `${this.baseUrl}/api/v1/notifications/preferences`,
      {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify(preferences),
      },
    );
  }

  async subscribeToPushNotifications(subscription: any): Promise<ApiResponse<void>> {
    return this.makeRequest(
      'subscribeToPushNotifications',
      `${this.baseUrl}/api/v1/notifications/push/subscribe`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(subscription),
      },
      false, // Don't retry subscriptions
    );
  }

  async unsubscribeFromPushNotifications(): Promise<ApiResponse<void>> {
    return this.makeRequest(
      'unsubscribeFromPushNotifications',
      `${this.baseUrl}/api/v1/notifications/push/unsubscribe`,
      {
        method: 'POST',
        headers: this.getHeaders(),
      },
      false, // Don't retry unsubscriptions
    );
  }

  // Generic HTTP methods for custom endpoints
  async get<T = any>(endpoint: string, config?: RequestInit): Promise<ApiResponse<T>> {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    return this.makeRequest(
      `get-${endpoint}`,
      url,
      {
        method: 'GET',
        headers: this.getHeaders(),
        ...config,
      },
    );
  }

  async post<T = any>(endpoint: string, data?: any, config?: RequestInit): Promise<ApiResponse<T>> {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    return this.makeRequest(
      `post-${endpoint}`,
      url,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
        ...config,
      },
      false, // Don't auto-retry POST requests
    );
  }

  async put<T = any>(endpoint: string, data?: any, config?: RequestInit): Promise<ApiResponse<T>> {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    return this.makeRequest(
      `put-${endpoint}`,
      url,
      {
        method: 'PUT',
        headers: this.getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
        ...config,
      },
    );
  }

  async delete<T = any>(endpoint: string, config?: RequestInit): Promise<ApiResponse<T>> {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    return this.makeRequest(
      `delete-${endpoint}`,
      url,
      {
        method: 'DELETE',
        headers: this.getHeaders(),
        ...config,
      },
      false, // Don't auto-retry DELETE requests
    );
  }

  async patch<T = any>(endpoint: string, data?: any, config?: RequestInit): Promise<ApiResponse<T>> {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    return this.makeRequest(
      `patch-${endpoint}`,
      url,
      {
        method: 'PATCH',
        headers: this.getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
        ...config,
      },
    );
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default APIClient;