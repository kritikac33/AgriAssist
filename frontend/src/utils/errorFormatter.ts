/**
 * Utility function to safely format API error responses into readable strings.
 * Handles FastAPI validation error objects and other error formats.
 */
export function formatError(error: any): string {
  // If error is already a string, return it
  if (typeof error === 'string') {
    return error;
  }

  // If error has a response with data
  if (error?.response?.data) {
    const detail = error.response.data.detail;

    // If detail is a string, return it
    if (typeof detail === 'string') {
      return detail;
    }

    // If detail is an array (FastAPI validation errors), format it with field names
    if (Array.isArray(detail)) {
      return detail
        .map((err: any) => {
          if (err?.loc && err?.msg) {
            // Extract field name from location array (skip 'body' prefix)
            const field = err.loc[err.loc.length - 1];
            return `${field}: ${err.msg}`;
          }
          if (err?.msg) {
            return err.msg;
          }
          return JSON.stringify(err);
        })
        .join(', ');
    }

    // If detail is an object, try to extract a message
    if (typeof detail === 'object' && detail !== null) {
      if (detail.message) return detail.message;
      if (detail.msg) return detail.msg;
      return JSON.stringify(detail);
    }
  }

  // If error has a message property
  if (error?.message) {
    return error.message;
  }

  // Fallback to stringifying the error
  return error?.toString() || 'An unknown error occurred';
}
