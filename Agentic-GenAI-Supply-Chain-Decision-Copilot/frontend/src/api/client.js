import axios from 'axios';

// Get base URL from environment variable or default to relative /api/v1
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000, // 45s timeout for AI & simulation endpoints
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Response interceptor for graceful error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with a status code outside 2xx range
      const status = error.response.status;
      const data = error.response.data;

      if (status === 429) {
        return Promise.reject({
          status,
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Too many requests. Please wait a moment before trying again.',
        });
      }

      if (status === 400 && data?.detail) {
        return Promise.reject({
          status,
          code: 'BAD_REQUEST',
          message: typeof data.detail === 'string' ? data.detail : 'Invalid request parameters.',
        });
      }

      if (status === 500) {
        return Promise.reject({
          status,
          code: 'SERVER_ERROR',
          message: 'The supply chain service encountered an internal error. Please try again.',
        });
      }

      return Promise.reject({
        status,
        code: 'API_ERROR',
        message: data?.detail || data?.error?.message || 'An unexpected API error occurred.',
      });
    } else if (error.request) {
      // Network failure / server unreachable
      return Promise.reject({
        status: 0,
        code: 'NETWORK_ERROR',
        message: 'Unable to connect to the backend server. Please verify the FastAPI service is running.',
      });
    }

    return Promise.reject({
      status: 0,
      code: 'UNKNOWN_ERROR',
      message: error.message || 'An unexpected error occurred.',
    });
  }
);

export default apiClient;
