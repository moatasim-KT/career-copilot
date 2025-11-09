 
export enum ErrorCode {
  NETWORK_ERROR = 'NETWORK_ERROR',
  AUTH_ERROR = 'AUTH_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  SERVER_ERROR = 'SERVER_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}
 

export interface AppError {
  code: ErrorCode;
  message: string;
  details?: unknown;
  statusCode?: number;
}

export const createError = (
  code: ErrorCode,
  message: string,
  details?: unknown,
  statusCode?: number,
): AppError => ({
  code,
  message,
  details,
  statusCode,
});

export const parseApiError = (error: unknown): AppError => {
  const err = error as {
    response?: { status: number; data?: { message?: string } };
    request?: unknown;
    message?: string;
  };

  if (err.response) {
    const status = err.response.status;
    if (status === 401 || status === 403) {
      return createError(ErrorCode.AUTH_ERROR, 'Authentication failed', error, status);
    }
    if (status === 404) {
      return createError(ErrorCode.NOT_FOUND, 'Resource not found', error, status);
    }
    if (status >= 500) {
      return createError(
        ErrorCode.SERVER_ERROR,
        'Server error occurred',
        error,
        status,
      );
    }
    return createError(
      ErrorCode.VALIDATION_ERROR,
      err.response.data?.message || 'Validation failed',
      error,
      status,
    );
  }
  if (err.request) {
    return createError(ErrorCode.NETWORK_ERROR, 'Network error occurred', error);
  }
  return createError(
    ErrorCode.UNKNOWN_ERROR,
    err.message || 'An unknown error occurred',
    error,
  );
};
