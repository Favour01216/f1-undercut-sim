/**
 * React Query hooks for F1 Undercut Simulator API
 *
 * This module provides optimized hooks with caching, error handling,
 * and performance optimizations for the simulation API.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  apiClient,
  queryKeys,
  type SimulationRequest,
  type SimulationResponse,
  type BackendStatus,
  type HeatmapDataPoint,
} from "@/lib/api";
import { logApiFailure } from "@/lib/error-logging";

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Hook to check backend status with caching
 */
export function useBackendStatus() {
  return useQuery({
    queryKey: queryKeys.status,
    queryFn: () => apiClient.checkStatus(),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 2 * 60 * 1000, // 2 minutes
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    meta: {
      errorMessage: "Failed to check backend status",
    },
  });
}

/**
 * Hook for single simulation with optimized caching
 */
export function useSimulation(
  request: SimulationRequest | null,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: request
      ? queryKeys.simulation(request)
      : ["simulation", "disabled"],
    queryFn: () => {
      if (!request) throw new Error("No simulation request provided");
      return apiClient.simulate(request);
    },
    enabled: enabled && request !== null,
    staleTime: 10 * 60 * 1000, // 10 minutes - simulations are deterministic
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
    meta: {
      errorMessage: "Simulation failed",
    },
  });
}

/**
 * Hook for heatmap data generation with memoization
 */
export function useHeatmapData(
  baseRequest: Omit<SimulationRequest, "samples"> | null,
  options: {
    gapRange?: { min: number; max: number; step: number };
    compounds?: ("SOFT" | "MEDIUM" | "HARD")[];
    samples?: number;
    enabled?: boolean;
  } = {}
) {
  const {
    gapRange = { min: 0, max: 30, step: 2 },
    compounds = ["SOFT", "MEDIUM", "HARD"] as const,
    samples = 500,
    enabled = true,
  } = options;

  return useQuery({
    queryKey: ["heatmap", baseRequest, gapRange, compounds, samples],
    queryFn: () => {
      if (!baseRequest) throw new Error("No base request provided");
      return apiClient.generateHeatmapData(
        baseRequest,
        gapRange,
        compounds,
        samples
      );
    },
    enabled: enabled && baseRequest !== null,
    staleTime: 15 * 60 * 1000, // 15 minutes - heatmaps are expensive
    gcTime: 60 * 60 * 1000, // 1 hour
    retry: 1, // Fewer retries for expensive operations
    retryDelay: 5000,
    meta: {
      errorMessage: "Failed to generate heatmap data",
    },
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Hook for running simulations with optimistic updates
 */
export function useSimulateMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SimulationRequest) => apiClient.simulate(request),
    onSuccess: (data, variables) => {
      // Cache the result for future queries
      queryClient.setQueryData(queryKeys.simulation(variables), data);
    },
    onError: (error, variables) => {
      // Log API failure for monitoring
      logApiFailure({
        url: "/simulate",
        method: "POST",
        message: error instanceof Error ? error.message : "Unknown error",
      });
    },
    meta: {
      errorMessage: "Simulation failed",
    },
  });
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Hook to prefetch simulation data
 */
export function usePrefetchSimulation() {
  const queryClient = useQueryClient();

  return (request: SimulationRequest) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.simulation(request),
      queryFn: () => apiClient.simulate(request),
      staleTime: 10 * 60 * 1000,
    });
  };
}

/**
 * Hook to invalidate simulation cache
 */
export function useInvalidateSimulations() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({
      queryKey: ["simulation"],
    });
  };
}

/**
 * Hook to get cached simulation count for performance monitoring
 */
export function useCacheStats() {
  const queryClient = useQueryClient();

  const getCacheStats = () => {
    const cache = queryClient.getQueryCache();
    const queries = cache.getAll();

    const simulationQueries = queries.filter(
      (query) => query.queryKey[0] === "simulation"
    );

    const heatmapQueries = queries.filter(
      (query) => query.queryKey[0] === "heatmap"
    );

    return {
      total_queries: queries.length,
      simulation_queries: simulationQueries.length,
      heatmap_queries: heatmapQueries.length,
      cache_size_mb:
        Math.round(
          (JSON.stringify(queries.map((q) => q.state.data)).length /
            1024 /
            1024) *
            100
        ) / 100,
    };
  };

  return { getCacheStats };
}

// ============================================================================
// Error Handling Hook
// ============================================================================

/**
 * Hook for centralized error handling
 */
export function useApiErrorHandler() {
  return (error: unknown, context: string) => {
    console.error(`API Error in ${context}:`, error);

    // Log to error tracking if available
    if (error instanceof Error) {
      logApiFailure({
        url: context,
        method: "GET",
        message: error.message,
      });
    }
  };
}



