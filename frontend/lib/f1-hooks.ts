/**
 * F1 Undercut Simulator - React Query Hooks
 * Racing-themed hooks for API integration
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  f1Api,
  queryKeys,
  type SimulationRequest,
  type SimulationResponse,
} from "./f1-api";

/**
 * Hook for running undercut simulations
 */
export function useF1Simulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SimulationRequest) => f1Api.simulate(request),
    onSuccess: (data, variables) => {
      // Cache successful simulations
      queryClient.setQueryData(queryKeys.simulation(variables), data);
    },
    meta: {
      errorMessage:
        "🏎️ Simulation crashed! Check your parameters and try again.",
    },
  });
}

/**
 * Hook for API health monitoring
 */
export function useF1ApiHealth() {
  return useQuery({
    queryKey: queryKeys.health(),
    queryFn: () => f1Api.health(),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 2 * 60 * 1000, // 2 minutes
    retry: 3,
    meta: {
      errorMessage: "🚨 API connection lost! Check if the backend is running.",
    },
  });
}

/**
 * Hook for getting cached simulation results
 */
export function useCachedSimulation(request: SimulationRequest | null) {
  const queryClient = useQueryClient();

  if (!request) return null;

  return queryClient.getQueryData(queryKeys.simulation(request)) as
    | SimulationResponse
    | undefined;
}
