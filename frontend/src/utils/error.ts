import { AxiosError } from 'axios';
import type { HTTPValidationError } from '../types';

export function formatApiError(error: unknown): string {
  // Network errors
  if (error instanceof AxiosError && !error.response) {
    return 'Cannot reach the server. Please check your internet connection.';
  }

  // Axios errors with response
  if (error instanceof AxiosError && error.response) {
    const data = error.response.data;

    // FastAPI 422 validation errors
    if (error.response.status === 422 && data && typeof data === 'object' && 'detail' in data) {
      const validationError = data as HTTPValidationError;
      if (Array.isArray(validationError.detail)) {
        // Format validation errors like "crop_id: field required"
        return validationError.detail
          .map((err) => {
            const field = err.loc && err.loc.length > 0 ? err.loc[err.loc.length - 1] : 'field';
            return `${field}: ${err.msg}`;
          })
          .join(', ');
      }
    }

    // Simple string error messages
    if (data && typeof data === 'object' && 'detail' in data && typeof data.detail === 'string') {
      return data.detail;
    }

    // Generic HTTP error with status
    return `Server error: ${error.response.status}`;
  }

  // Generic error
  if (error instanceof Error) {
    return error.message;
  }

  // Unknown error shape
  return 'An unexpected error occurred. Please try again.';
}
