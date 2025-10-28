"use client";

import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

// Create a client with optimized defaults for our simulation API
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache simulation results for 10 minutes
      staleTime: 10 * 60 * 1000, // 10 minutes
      // Keep data fresh for 5 minutes, then mark as stale
      gcTime: 15 * 60 * 1000, // 15 minutes (renamed from cacheTime)
      // Retry failed requests up to 2 times
      retry: 2,
      // Don't refetch on window focus for simulation results
      refetchOnWindowFocus: false,
      // Don't refetch on reconnect unless data is stale
      refetchOnReconnect: "always",
      // Don't refetch on mount if data is fresh
      refetchOnMount: true,
    },
    mutations: {
      // Retry failed mutations once
      retry: 1,
    },
  },
});

interface ReactQueryProviderProps {
  children: React.ReactNode;
}

export function ReactQueryProvider({ children }: ReactQueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === "development" && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}

