import axios, { AxiosError, AxiosInstance } from 'axios';
import {
  GeneratePodcastRequest,
  GeneratePodcastResponse,
  PodcastStatusResponse,
} from '../types/podcast';
import { AdminStats } from '../types/admin';
import { authService } from './auth';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token and logging
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token to every request
    const token = authService.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`[API] Response received:`, response.status);
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      console.error(
        `[API] Error ${error.response.status}:`,
        error.response.data
      );
    } else if (error.request) {
      // Request made but no response
      console.error('[API] No response received:', error.message);
    } else {
      // Error setting up request
      console.error('[API] Request setup error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Helper function to sleep
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Generic retry logic
async function withRetry<T>(
  fn: () => Promise<T>,
  retries: number = MAX_RETRIES,
  delay: number = RETRY_DELAY
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (retries <= 0) {
      throw error;
    }

    const axiosError = error as AxiosError;
    // Only retry on network errors or 5xx status codes
    if (
      !axiosError.response ||
      (axiosError.response.status >= 500 && axiosError.response.status < 600)
    ) {
      console.log(`[API] Retrying... (${MAX_RETRIES - retries + 1}/${MAX_RETRIES})`);
      await sleep(delay);
      return withRetry(fn, retries - 1, delay * 2); // Exponential backoff
    }

    throw error;
  }
}

// API Error class
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Parse error response
function parseError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>;

    if (axiosError.response) {
      const detail = axiosError.response.data?.detail ||
                     axiosError.response.data?.message ||
                     'An error occurred';
      return new ApiError(
        detail,
        axiosError.response.status,
        axiosError.response.data
      );
    }

    if (axiosError.request) {
      return new ApiError(
        'Network error: Unable to reach the server',
        undefined,
        axiosError.message
      );
    }
  }

  return new ApiError('An unexpected error occurred', undefined, error);
}

// ============================================================================
// Podcast API Endpoints
// ============================================================================

/**
 * Generate a new podcast based on interests and preferences
 */
export async function generatePodcast(
  request: GeneratePodcastRequest,
  mockAudio: boolean = false
): Promise<GeneratePodcastResponse> {
  try {
    const response = await withRetry(() =>
      apiClient.post<GeneratePodcastResponse>('/api/v1/podcasts/generate', {
        ...request,
        mock_audio: mockAudio,
      })
    );
    return response.data;
  } catch (error) {
    throw parseError(error);
  }
}

/**
 * Get the status of a podcast generation task
 */
export async function getPodcastStatus(
  podcastId: string
): Promise<PodcastStatusResponse> {
  try {
    const response = await apiClient.get<PodcastStatusResponse>(
      `/api/v1/podcasts/${podcastId}/status`
    );
    return response.data;
  } catch (error) {
    throw parseError(error);
  }
}

/**
 * Get list of user's podcasts
 */
export async function getPodcasts(
  page: number = 1,
  pageSize: number = 100
): Promise<{ podcasts: any[]; total: number }> {
  try {
    const response = await apiClient.get(`/api/v1/podcasts/`, {
      params: { page, page_size: pageSize },
    });
    return response.data;
  } catch (error) {
    throw parseError(error);
  }
}

/**
 * Get authenticated audio blob URL for playback
 */
export async function getAudioBlobUrl(podcastId: string): Promise<string> {
  const response = await apiClient.get(`/api/v1/podcasts/${podcastId}/audio`, {
    responseType: 'blob',
  });

  // Create a blob URL that can be used by audio elements
  return window.URL.createObjectURL(new Blob([response.data], { type: 'audio/mpeg' }));
}

/**
 * Download a podcast audio file
 */
export async function downloadPodcast(
  podcastId: string,
  filename?: string
): Promise<void> {
  try {
    const response = await apiClient.get(`/api/v1/podcasts/${podcastId}/audio`, {
      responseType: 'blob',
    });

    // Create a download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename || `podcast-${podcastId}.mp3`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    throw parseError(error);
  }
}

// ============================================================================
// Admin API Endpoints
// ============================================================================

/**
 * Get admin dashboard statistics
 */
export async function getAdminStats(
  days?: number
): Promise<AdminStats> {
  try {
    const params = days ? { days } : {};
    const response = await withRetry(() =>
      apiClient.get<AdminStats>('/api/v1/admin/stats', { params })
    );
    return response.data;
  } catch (error) {
    throw parseError(error);
  }
}

/**
 * Health check endpoint
 */
export async function checkHealth(): Promise<{ status: string }> {
  try {
    const response = await apiClient.get<{ status: string }>('/health');
    return response.data;
  } catch (error) {
    throw parseError(error);
  }
}

// ============================================================================
// User API Endpoints
// ============================================================================

/**
 * Get current user profile with preferences
 */
export async function getCurrentUser(): Promise<any> {
  try {
    const response = await apiClient.get('/api/v1/users/me');
    return response.data;
  } catch (error) {
    throw parseError(error);
  }
}

/**
 * Update user preferences
 */
export async function updateUserPreferences(data: {
  interests?: string[];
  duration_minutes?: number;
  language?: string;
}): Promise<any> {
  try {
    const response = await apiClient.put('/api/v1/users/me/preferences', data);
    return response.data;
  } catch (error) {
    throw parseError(error);
  }
}

/**
 * Update schedule settings
 */
export async function updateScheduleSettings(data: {
  enabled?: boolean;
  frequency?: string;
  time?: string;
  timezone?: string;
  days_of_week?: number[];
}): Promise<any> {
  try {
    const response = await apiClient.put('/api/v1/users/me/schedule', data);
    return response.data;
  } catch (error) {
    throw parseError(error);
  }
}

// ============================================================================
// Polling utilities
// ============================================================================

/**
 * Poll for podcast status until it's completed or failed
 * @param podcastId - The ID of the podcast to poll
 * @param onUpdate - Callback called on each status update
 * @param interval - Polling interval in milliseconds (default: 2000)
 * @param timeout - Maximum time to poll in milliseconds (default: 5 minutes)
 */
export async function pollPodcastStatus(
  podcastId: string,
  onUpdate: (status: PodcastStatusResponse) => void,
  interval: number = 2000,
  timeout: number = 300000
): Promise<PodcastStatusResponse> {
  const startTime = Date.now();

  while (true) {
    // Check timeout
    if (Date.now() - startTime > timeout) {
      throw new ApiError('Podcast generation timed out');
    }

    try {
      const status = await getPodcastStatus(podcastId);
      onUpdate(status);

      // Check if done
      if (status.status === 'completed' || status.status === 'failed') {
        return status;
      }

      // Wait before next poll
      await sleep(interval);
    } catch (error) {
      // Don't retry polling errors, just throw
      throw parseError(error);
    }
  }
}

export default apiClient;
