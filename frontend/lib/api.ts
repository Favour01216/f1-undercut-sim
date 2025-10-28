/**
 * F1 Undercut Simulator API Client
 * Production-grade typed API client with Zod validation and React Query integration
 */

import { z } from "zod";

// API URL configuration for different environments
function getApiBaseUrl(): string {
  // Client-side: use the public API URL or default to localhost
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_CLIENT_API_URL || "http://localhost:8000";
  }

  // Server-side: use internal Docker network or fallback to public URL
  return (
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_CLIENT_API_URL ||
    "http://localhost:8000"
  );
}

export const API_BASE_URL = getApiBaseUrl();

// ============================================================================
// Zod Schemas for Runtime Validation
// ============================================================================

// Grand Prix choices based on backend validation
const GP_CHOICES = [
  "bahrain",
  "imola",
  "monza",
  "monaco",
  "spain",
  "canada",
  "austria",
  "silverstone",
  "hungary",
  "belgium",
  "netherlands",
  "italy",
  "singapore",
  "japan",
  "qatar",
  "usa",
  "mexico",
  "brazil",
  "abu_dhabi",
  "australia",
  "china",
  "azerbaijan",
  "miami",
  "france",
  "portugal",
  "russia",
  "turkey",
  "saudi_arabia",
  "las_vegas",
] as const;

// Compound choices
const COMPOUND_CHOICES = ["SOFT", "MEDIUM", "HARD"] as const;

// Request validation schema
export const SimulationRequestSchema = z.object({
  gp: z.enum(GP_CHOICES),
  year: z.coerce.number().int().min(2020).max(2024),
  driver_a: z.string().min(1).max(50),
  driver_b: z.string().min(1).max(50),
  compound_a: z.enum(COMPOUND_CHOICES),
  lap_now: z.coerce.number().int().min(1).max(100),
  samples: z.coerce.number().int().min(1).max(10000).optional().default(1000),
  H: z.coerce.number().int().min(1).max(5).optional().default(2),
  p_pit_next: z.coerce.number().min(0).max(1).optional().default(1.0),
});

// Models fitted sub-schema
const ModelsFittedSchema = z.object({
  degradation_model: z.boolean(),
  pit_model: z.boolean(),
  outlap_model: z.boolean(),
});

// Assumptions schema with flexible additional properties
const AssumptionsSchema = z
  .object({
    current_gap_s: z.number(),
    tire_age_driver_b: z.number(),
    models_fitted: ModelsFittedSchema,
    monte_carlo_samples: z.coerce.number().int(),
    avg_degradation_penalty_s: z.number().optional(),
    pit_loss_range: z.tuple([z.number(), z.number()]).optional(),
    outlap_delta_range: z.tuple([z.number(), z.number()]).optional(),
    compound_used: z.string().optional(),
    success_margin_s: z.number().optional(),
    gap_s: z.number().optional(),
    tyre_age_b: z.number().optional(),
    degradation_model: z.string().optional(),
    pit_model: z.string().optional(),
    outlap_model: z.string().optional(),
  })
  .catchall(z.any()); // Allow additional properties

// Main response validation schema (SimOut equivalent)
export const SimulationResponseSchema = z.object({
  p_undercut: z.number().min(0).max(1),
  pitLoss_s: z.number(),
  outLapDelta_s: z.number(),
  avgMargin_s: z.number().optional(),
  expected_margin_s: z.number().optional(),
  ci_low_s: z.number().optional(),
  ci_high_s: z.number().optional(),
  H_used: z.number().int().optional(),
  assumptions: AssumptionsSchema,
});

// Backend status validation schema
export const BackendStatusSchema = z.object({
  message: z.string(),
  version: z.string(),
  health: z.string().optional(),
  docs: z.string(),
  simulate: z.string(),
});

// Heatmap data point schema
export const HeatmapDataPointSchema = z.object({
  gap: z.number(),
  compound: z.enum(COMPOUND_CHOICES),
  probability: z.number().min(0).max(1),
});

// ============================================================================
// TypeScript Types (derived from Zod schemas)
// ============================================================================

export type SimulationRequest = z.infer<typeof SimulationRequestSchema>;
export type SimulationResponse = z.infer<typeof SimulationResponseSchema>;
export type BackendStatus = z.infer<typeof BackendStatusSchema>;
export type HeatmapDataPoint = z.infer<typeof HeatmapDataPointSchema>;

// Legacy interface for backward compatibility
export interface SimulationSession {
  id: string;
  timestamp: Date;
  request: SimulationRequest;
  response: SimulationResponse;
}

// ============================================================================
// Custom Error Types
// ============================================================================

export class ApiValidationError extends Error {
  constructor(
    message: string,
    public readonly validationError: z.ZodError,
    public readonly rawResponse?: any
  ) {
    super(message);
    this.name = "ApiValidationError";
  }

  /**
   * Get user-friendly error message for display in UI
   */
  getUserFriendlyMessage(): string {
    const issues = this.validationError.issues;
    if (issues.length === 0) return "Invalid response from server";

    const firstIssue = issues[0];
    const path = firstIssue.path.join(".");

    switch (firstIssue.code) {
      case "invalid_type":
        return `Invalid data type for ${path}: expected ${firstIssue.expected}, got ${firstIssue.received}`;
      case "too_small":
        return `Value for ${path} is too small: minimum is ${firstIssue.minimum}`;
      case "too_big":
        return `Value for ${path} is too large: maximum is ${firstIssue.maximum}`;
      case "invalid_enum_value":
        return `Invalid value for ${path}: must be one of ${firstIssue.options?.join(
          ", "
        )}`;
      default:
        return `Invalid value for ${path}: ${firstIssue.message}`;
    }
  }
}

export class ApiNetworkError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly statusText?: string
  ) {
    super(message);
    this.name = "ApiNetworkError";
  }

  getUserFriendlyMessage(): string {
    if (this.status) {
      switch (this.status) {
        case 400:
          return "Invalid request parameters. Please check your inputs.";
        case 404:
          return "API endpoint not found. Please contact support.";
        case 500:
          return "Server error. Please try again later.";
        case 503:
          return "Service unavailable. Please try again in a few minutes.";
        default:
          return `Server error (${this.status}). Please try again later.`;
      }
    }
    return "Network error. Please check your connection and try again.";
  }
}

// ============================================================================
// API Client with Zod Validation
// ============================================================================

export class F1ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Parse and validate API response using Zod schema
   */
  private parseResponse<T>(
    schema: z.ZodSchema<T>,
    data: unknown,
    endpoint: string
  ): T {
    try {
      return schema.parse(data);
    } catch (error) {
      if (error instanceof z.ZodError) {
        const message = `Invalid response from ${endpoint}`;
        throw new ApiValidationError(message, error, data);
      }
      throw error;
    }
  }

  /**
   * Perform validated fetch request
   */
  private async fetchWithValidation<T>(
    url: string,
    schema: z.ZodSchema<T>,
    options?: RequestInit
  ): Promise<T> {
    let response: Response;

    try {
      response = await fetch(url, options);
    } catch (error) {
      throw new ApiNetworkError(
        `Network error when connecting to ${url}: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    }

    if (!response.ok) {
      let errorMessage: string;
      try {
        const errorText = await response.text();
        errorMessage = errorText || response.statusText;
      } catch {
        errorMessage = response.statusText;
      }

      throw new ApiNetworkError(
        `API request failed: ${errorMessage}`,
        response.status,
        response.statusText
      );
    }

    let data: unknown;
    try {
      data = await response.json();
    } catch (error) {
      throw new ApiNetworkError(
        `Invalid JSON response from ${url}: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    }

    return this.parseResponse(schema, data, url);
  }

  /**
   * Check backend connectivity and status
   */
  async checkStatus(): Promise<BackendStatus> {
    return this.fetchWithValidation(`${this.baseUrl}/`, BackendStatusSchema);
  }

  /**
   * Run a single undercut simulation with validated input/output
   */
  async simulate(request: SimulationRequest): Promise<SimulationResponse> {
    // Validate request before sending
    const validatedRequest = SimulationRequestSchema.parse(request);

    return this.fetchWithValidation(
      `${this.baseUrl}/simulate`,
      SimulationResponseSchema,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(validatedRequest),
      }
    );
  }

  /**
   * Generate heatmap data by running simulations across gap and compound combinations
   */
  async generateHeatmapData(
    baseRequest: Omit<SimulationRequest, "samples">,
    gapRange: { min: number; max: number; step: number } = {
      min: 0,
      max: 30,
      step: 2,
    },
    compounds: (typeof COMPOUND_CHOICES)[number][] = ["SOFT", "MEDIUM", "HARD"],
    samples: number = 500
  ): Promise<HeatmapDataPoint[]> {
    const results: HeatmapDataPoint[] = [];
    const promises: Promise<void>[] = [];

    // Generate all gap values
    const gaps: number[] = [];
    for (let gap = gapRange.min; gap <= gapRange.max; gap += gapRange.step) {
      gaps.push(gap);
    }

    // Create simulation promises for all combinations
    for (const compound of compounds) {
      for (const gap of gaps) {
        const request: SimulationRequest = {
          ...baseRequest,
          compound_a: compound,
          samples,
        };

        const promise = this.simulate(request)
          .then((response) => {
            const dataPoint: HeatmapDataPoint = {
              gap,
              compound,
              probability: response.p_undercut,
            };

            // Validate the data point
            const validatedPoint = HeatmapDataPointSchema.parse(dataPoint);
            results.push(validatedPoint);
          })
          .catch((error) => {
            console.warn(
              `Heatmap simulation failed for gap=${gap}, compound=${compound}:`,
              error
            );
            // Add a default value for failed simulations
            const fallbackPoint: HeatmapDataPoint = {
              gap,
              compound,
              probability: 0,
            };
            results.push(fallbackPoint);
          });

        promises.push(promise);
      }
    }

    // Wait for all simulations to complete
    await Promise.all(promises);

    // Sort results by gap then compound for consistent ordering
    return results.sort((a, b) => {
      if (a.gap !== b.gap) return a.gap - b.gap;
      return a.compound.localeCompare(b.compound);
    });
  }
}

// Singleton instance
export const apiClient = new F1ApiClient();

// ============================================================================
// React Query Keys
// ============================================================================

export const queryKeys = {
  status: ["backend", "status"] as const,
  simulation: (request: SimulationRequest) => ["simulation", request] as const,
  heatmap: (baseRequest: Omit<SimulationRequest, "samples">) =>
    ["heatmap", baseRequest] as const,
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Generate a unique session ID
 */
export const generateSessionId = (): string => {
  return `sim_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Format probability as percentage
 */
export const formatProbability = (probability: number | undefined): string => {
  if (probability === undefined || probability === null || isNaN(probability)) {
    return "N/A";
  }
  return `${(probability * 100).toFixed(1)}%`;
};

/**
 * Format time in seconds
 */
export const formatSeconds = (seconds: number | undefined): string => {
  if (seconds === undefined || seconds === null || isNaN(seconds)) {
    return "N/A";
  }
  return `${seconds.toFixed(2)}s`;
};

/**
 * Determine success likelihood based on probability threshold
 */
export const getSuccessLikelihood = (
  probability: number | undefined,
  threshold: number = 0.5
): {
  label: string;
  variant: "success" | "danger" | "warning";
} => {
  if (probability === undefined || probability === null || isNaN(probability)) {
    return { label: "Unknown", variant: "warning" };
  }

  if (probability >= threshold + 0.2) {
    return { label: "High Success", variant: "success" };
  } else if (probability >= threshold) {
    return { label: "Likely Success", variant: "success" };
  } else if (probability >= threshold - 0.2) {
    return { label: "Uncertain", variant: "warning" };
  } else {
    return { label: "Likely Fail", variant: "danger" };
  }
};

/**
 * Validate simulation request using Zod schema
 */
export const validateSimulationRequest = (
  request: Partial<SimulationRequest>
): { isValid: boolean; errors: string[]; data?: SimulationRequest } => {
  try {
    const validatedData = SimulationRequestSchema.parse(request);
    return { isValid: true, errors: [], data: validatedData };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors = error.issues.map((issue) => {
        const path = issue.path.join(".");
        switch (issue.code) {
          case "invalid_type":
            return `${path}: expected ${issue.expected}, got ${issue.received}`;
          case "too_small":
            if (issue.type === "string") {
              return `${path}: must be at least ${issue.minimum} characters`;
            }
            return `${path}: must be at least ${issue.minimum}`;
          case "too_big":
            if (issue.type === "string") {
              return `${path}: must be at most ${issue.maximum} characters`;
            }
            return `${path}: must be at most ${issue.maximum}`;
          case "invalid_enum_value":
            return `${path}: must be one of ${issue.options?.join(", ")}`;
          default:
            return `${path}: ${issue.message}`;
        }
      });
      return { isValid: false, errors };
    }
    return { isValid: false, errors: ["Unknown validation error"] };
  }
};

/**
 * Handle API errors gracefully with user-friendly messages
 */
export const handleApiError = (
  error: unknown
): {
  message: string;
  isUserFriendly: boolean;
  originalError: unknown;
} => {
  if (error instanceof ApiValidationError) {
    return {
      message: error.getUserFriendlyMessage(),
      isUserFriendly: true,
      originalError: error,
    };
  }

  if (error instanceof ApiNetworkError) {
    return {
      message: error.getUserFriendlyMessage(),
      isUserFriendly: true,
      originalError: error,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      isUserFriendly: false,
      originalError: error,
    };
  }

  return {
    message: "An unexpected error occurred. Please try again.",
    isUserFriendly: true,
    originalError: error,
  };
};

