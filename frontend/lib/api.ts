/**
 * F1 Undercut Simulator API Client
 * Production-grade typed API client with React Query integration
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ============================================================================
// Types
// ============================================================================

export interface SimulationRequest {
  gp: string;
  year: number;
  driver_a: string;
  driver_b: string;
  compound_a: string;
  lap_now: number;
  samples?: number;
}

export interface SimulationResponse {
  p_undercut: number;
  pitLoss_s: number;
  outLapDelta_s: number;
  assumptions: {
    current_gap_s: number;
    tire_age_driver_b: number;
    models_fitted: {
      deg_model: boolean;
      pit_model: boolean;
      outlap_model: boolean;
    };
    monte_carlo_samples: number;
    avg_degradation_penalty_s: number;
    pit_loss_range: [number, number];
    outlap_delta_range: [number, number];
    compound_used: string;
    success_margin_s: number;
    [key: string]: any;
  };
}

export interface BackendStatus {
  message: string;
  version: string;
  health: string;
  docs: string;
  simulate: string;
}

export interface SimulationSession {
  id: string;
  timestamp: Date;
  request: SimulationRequest;
  response: SimulationResponse;
}

export interface HeatmapDataPoint {
  gap: number;
  compound: string;
  probability: number;
}

// ============================================================================
// API Client
// ============================================================================

export class F1ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Check backend connectivity and status
   */
  async checkStatus(): Promise<BackendStatus> {
    const response = await fetch(`${this.baseUrl}/`);
    if (!response.ok) {
      throw new Error(`Backend status check failed: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Run a single undercut simulation
   */
  async simulate(request: SimulationRequest): Promise<SimulationResponse> {
    const response = await fetch(`${this.baseUrl}/simulate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Simulation failed: ${error}`);
    }

    return response.json();
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
    compounds: string[] = ["SOFT", "MEDIUM", "HARD"],
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
            results.push({
              gap,
              compound,
              probability: response.p_undercut,
            });
          })
          .catch((error) => {
            console.warn(
              `Heatmap simulation failed for gap=${gap}, compound=${compound}:`,
              error
            );
            // Add a default value for failed simulations
            results.push({
              gap,
              compound,
              probability: 0,
            });
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
 * Validate simulation request
 */
export const validateSimulationRequest = (
  request: Partial<SimulationRequest>
): string[] => {
  const errors: string[] = [];

  if (!request.gp) errors.push("Grand Prix is required");
  if (!request.year) errors.push("Year is required");
  if (!request.driver_a) errors.push("Driver A is required");
  if (!request.driver_b) errors.push("Driver B is required");
  if (!request.compound_a) errors.push("Compound is required");
  if (request.lap_now === undefined || request.lap_now < 1)
    errors.push("Current lap must be greater than 0");
  if (request.samples !== undefined && request.samples < 100)
    errors.push("Samples must be at least 100");

  return errors;
};
