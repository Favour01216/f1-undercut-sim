/**
 * Error logging utilities for F1 Undercut Simulation frontend.
 *
 * This module provides utilities for logging API failures, frontend exceptions,
 * and other errors to both the console and Sentry (if configured).
 */

import * as Sentry from "@sentry/nextjs";

export interface ApiError {
  url: string;
  method: string;
  status?: number;
  statusText?: string;
  message?: string;
  requestId?: string;
}

export interface FrontendError {
  message: string;
  stack?: string;
  component?: string;
  props?: Record<string, unknown>;
  userAgent?: string;
}

/**
 * Log API failure with status code and path information.
 */
export function logApiFailure(error: ApiError): void {
  const logData = {
    type: "api_failure",
    url: error.url,
    method: error.method,
    status: error.status,
    statusText: error.statusText,
    message: error.message,
    requestId: error.requestId,
    timestamp: new Date().toISOString(),
  };

  // Log to console for development
  if (process.env.NODE_ENV === "development") {
    console.error("API Failure:", logData);
  }

  // Send to Sentry if enabled
  if (process.env.NEXT_PUBLIC_ENABLE_SENTRY === "true") {
    Sentry.addBreadcrumb({
      message: `API ${error.method} ${error.url} failed`,
      category: "api",
      level: "error",
      data: logData,
    });

    Sentry.captureException(
      new Error(
        `API ${error.method} ${error.url} failed: ${error.status} ${error.statusText}`
      ),
      {
        tags: {
          type: "api_failure",
          status: error.status,
          method: error.method,
        },
        extra: logData,
      }
    );
  }
}

/**
 * Log frontend exception with component context.
 */
export function logFrontendError(error: FrontendError): void {
  const logData = {
    type: "frontend_error",
    message: error.message,
    stack: error.stack,
    component: error.component,
    props: error.props,
    userAgent:
      error.userAgent ||
      (typeof navigator !== "undefined" ? navigator.userAgent : "unknown"),
    timestamp: new Date().toISOString(),
  };

  // Log to console for development
  if (process.env.NODE_ENV === "development") {
    console.error("Frontend Error:", logData);
  }

  // Send to Sentry if enabled
  if (process.env.NEXT_PUBLIC_ENABLE_SENTRY === "true") {
    Sentry.addBreadcrumb({
      message: error.message,
      category: "error",
      level: "error",
      data: {
        component: error.component,
        props: error.props,
      },
    });

    Sentry.captureException(new Error(error.message), {
      tags: {
        type: "frontend_error",
        component: error.component,
      },
      extra: logData,
    });
  }
}

/**
 * Enhanced fetch wrapper that automatically logs API failures.
 */
export async function fetchWithLogging(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const method = options.method || "GET";

  try {
    const response = await fetch(url, options);

    // Log API failures (4xx and 5xx responses)
    if (!response.ok) {
      const requestId = response.headers.get("X-Request-ID") || undefined;

      logApiFailure({
        url,
        method,
        status: response.status,
        statusText: response.statusText,
        requestId,
        message: `HTTP ${response.status}: ${response.statusText}`,
      });
    }

    return response;
  } catch (error) {
    // Log network errors and other fetch failures
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";

    logApiFailure({
      url,
      method,
      message: `Network error: ${errorMessage}`,
    });

    throw error;
  }
}

/**
 * React Error Boundary error logging function.
 */
export function logReactError(
  error: Error,
  errorInfo: { componentStack: string }
): void {
  logFrontendError({
    message: error.message,
    stack: error.stack,
    component: "ErrorBoundary",
    props: {
      componentStack: errorInfo.componentStack,
    },
  });
}

/**
 * Promise rejection handler for unhandled promises.
 */
export function logUnhandledRejection(event: PromiseRejectionEvent): void {
  const error = event.reason;
  const message = error instanceof Error ? error.message : String(error);

  logFrontendError({
    message: `Unhandled Promise Rejection: ${message}`,
    stack: error instanceof Error ? error.stack : undefined,
    component: "UnhandledPromise",
  });
}

/**
 * Window error handler for uncaught exceptions.
 */
export function logWindowError(
  message: string | Event,
  source?: string,
  lineno?: number,
  colno?: number,
  error?: Error
): void {
  const errorMessage = typeof message === "string" ? message : "Unknown error";

  logFrontendError({
    message: `Uncaught Exception: ${errorMessage}`,
    stack: error?.stack,
    component: "WindowError",
    props: {
      source,
      lineno,
      colno,
    },
  });
}

/**
 * Set up global error handlers for the application.
 * Call this once in your app initialization.
 */
export function setupGlobalErrorHandlers(): void {
  // Handle unhandled promise rejections
  if (typeof window !== "undefined") {
    window.addEventListener("unhandledrejection", logUnhandledRejection);
    window.addEventListener("error", (event) => {
      logWindowError(
        event.message,
        event.filename,
        event.lineno,
        event.colno,
        event.error
      );
    });
  }
}
