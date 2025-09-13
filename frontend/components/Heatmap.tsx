"use client";

/**
 * F1 Undercut Simulator - Heatmap Component
 * Interactive heatmap with full accessibility and enhanced UX
 */

import React, { useMemo, memo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import {
  SimulationRequest,
  HeatmapDataPoint,
  apiClient,
  queryKeys,
} from "@/lib/api";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Skeleton } from "./ui/skeleton";
import { Alert, AlertDescription } from "./ui/alert";
import {
  AlertTriangle,
  RefreshCw,
  Info,
  BarChart3,
  TrendingUp,
  Target,
} from "lucide-react";

// Dynamic import of Plotly to avoid SSR issues
const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => (
    <div className="h-96 w-full">
      <HeatmapSkeleton />
    </div>
  ),
});

// ============================================================================
// Types & Constants
// ============================================================================

interface HeatmapProps {
  currentRequest: SimulationRequest | null;
}

const COMPOUND_ORDER = ["SOFT", "MEDIUM", "HARD"];
const GAP_RANGE = { min: 0, max: 30, step: 2 };

// ============================================================================
// Helper Functions (Memoized for Performance)
// ============================================================================

const prepareHeatmapData = (data: HeatmapDataPoint[]) => {
  // Create matrices for Plotly heatmap
  const gaps = Array.from(new Set(data.map((d) => d.gap))).sort(
    (a, b) => a - b
  );
  const compounds = COMPOUND_ORDER;

  // Initialize probability matrix
  const z: number[][] = compounds.map(() => new Array(gaps.length).fill(0));

  // Fill the matrix
  data.forEach((point) => {
    const gapIndex = gaps.indexOf(point.gap);
    const compoundIndex = compounds.indexOf(point.compound);
    if (gapIndex !== -1 && compoundIndex !== -1) {
      z[compoundIndex][gapIndex] = point.probability * 100; // Convert to percentage
    }
  });

  return {
    x: gaps.map((g) => `${g}s`),
    y: compounds,
    z,
    gaps,
    compounds,
  };
};

// ============================================================================
// Components
// ============================================================================

const HeatmapSkeleton: React.FC = () => (
  <div
    className="space-y-4 animate-pulse"
    role="status"
    aria-label="Heatmap loading"
    aria-live="polite"
  >
    {/* Title skeleton */}
    <Skeleton className="h-6 w-64 mx-auto" />

    {/* Main heatmap area */}
    <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-6">
      {/* Y-axis labels */}
      <div className="flex">
        <div className="flex flex-col justify-around h-80 w-16 mr-4">
          <Skeleton className="h-4 w-12" />
          <Skeleton className="h-4 w-12" />
          <Skeleton className="h-4 w-12" />
        </div>

        {/* Heatmap grid */}
        <div className="flex-1">
          <div className="grid grid-cols-8 gap-1 h-80">
            {Array.from({ length: 24 }).map((_, i) => (
              <Skeleton key={i} className="rounded" />
            ))}
          </div>

          {/* X-axis labels */}
          <div className="grid grid-cols-8 gap-1 mt-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-4" />
            ))}
          </div>
        </div>

        {/* Color scale */}
        <div className="w-8 ml-4">
          <div className="h-80 bg-gradient-to-t from-red-200 to-green-200 dark:from-red-800 dark:to-green-800 rounded" />
          <div className="space-y-2 mt-2">
            <Skeleton className="h-3 w-8" />
            <Skeleton className="h-3 w-8" />
            <Skeleton className="h-3 w-8" />
          </div>
        </div>
      </div>
    </div>

    <div className="text-center">
      <div className="flex items-center justify-center gap-2 text-blue-600 dark:text-blue-400">
        <RefreshCw className="w-4 h-4 animate-spin" aria-hidden="true" />
        <span>Generating heatmap data...</span>
      </div>
    </div>
  </div>
);

const EmptyState: React.FC = () => (
  <div className="text-center py-12" role="status" aria-live="polite">
    <div
      className="mx-auto w-24 h-24 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4"
      aria-hidden="true"
    >
      <BarChart3 className="w-10 h-10 text-gray-400" />
    </div>
    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
      No heatmap data available
    </h3>
    <p className="text-gray-500 dark:text-gray-400 max-w-sm mx-auto mb-4">
      Run a simulation first to generate the heatmap analysis across different
      gaps and compounds.
    </p>
    <p className="text-sm text-gray-400 dark:text-gray-500">
      The heatmap will show undercut success probability for various gap sizes
      and tire compounds.
    </p>
  </div>
);

const LoadingState: React.FC = () => (
  <div
    className="space-y-4"
    role="status"
    aria-live="polite"
    aria-label="Generating heatmap analysis"
  >
    <div className="flex justify-center mb-6">
      <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
        <RefreshCw className="w-4 h-4 animate-spin" aria-hidden="true" />
        <span className="font-medium">Generating heatmap data...</span>
      </div>
    </div>
    <HeatmapSkeleton />
    <p className="text-center text-sm text-gray-500 dark:text-gray-400">
      Running simulations across{" "}
      {Math.ceil((GAP_RANGE.max - GAP_RANGE.min) / GAP_RANGE.step) + 1} gaps × 3
      compounds...
      <br />
      <span className="text-xs">This may take 30-60 seconds</span>
    </p>
  </div>
);

// ============================================================================
// Main Component
// ============================================================================

export const Heatmap: React.FC<HeatmapProps> = memo(({ currentRequest }) => {
  // Create base request for heatmap (without samples)
  const baseRequest = useMemo(() => {
    if (!currentRequest) return null;
    const { samples, ...rest } = currentRequest;
    return rest;
  }, [currentRequest]);

  // Query for heatmap data
  const {
    data: heatmapData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: baseRequest ? queryKeys.heatmap(baseRequest) : [],
    queryFn: () =>
      baseRequest
        ? apiClient.generateHeatmapData(baseRequest, GAP_RANGE)
        : null,
    enabled: !!baseRequest,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  // Prepare plot data (memoized for performance)
  const plotData = useMemo(() => {
    if (!heatmapData) return null;
    return prepareHeatmapData(heatmapData);
  }, [heatmapData]);

  // Memoized statistical calculations for summary cards
  const summaryStats = useMemo(() => {
    if (!plotData)
      return { highSuccessCount: 0, avgSuccessRate: 0, bestCompound: "N/A" };

    const flatZ = plotData.z.flat();
    const highSuccessCount = flatZ.filter((v) => v >= 50).length;
    const avgSuccessRate = Math.round(
      flatZ.reduce((a, b) => a + b, 0) / flatZ.length
    );

    const bestCompound =
      plotData.compounds.find((c) => {
        const compoundIndex = plotData.compounds.indexOf(c);
        const avgForCompound =
          plotData.z[compoundIndex].reduce((a, b) => a + b, 0) /
          plotData.z[compoundIndex].length;
        return (
          avgForCompound ===
          Math.max(
            ...plotData.compounds.map((comp) => {
              const idx = plotData.compounds.indexOf(comp);
              return (
                plotData.z[idx].reduce((a, b) => a + b, 0) /
                plotData.z[idx].length
              );
            })
          )
        );
      }) || "N/A";

    return { highSuccessCount, avgSuccessRate, bestCompound };
  }, [plotData]);

  // Error state
  if (error) {
    return (
      <Alert variant="destructive" role="alert" aria-live="assertive">
        <AlertTriangle className="h-4 w-4" aria-hidden="true" />
        <AlertDescription>
          <div className="space-y-3">
            <div>
              <strong>Heatmap Generation Failed</strong>
              <br />
              {error.message}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="mt-2"
              aria-label="Retry heatmap generation"
            >
              <RefreshCw className="w-4 h-4 mr-2" aria-hidden="true" />
              Retry Generation
            </Button>
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Empty state
  if (!baseRequest) {
    return <EmptyState />;
  }

  // Loading state
  if (isLoading) {
    return <LoadingState />;
  }

  // No data state
  if (!plotData) {
    return (
      <Alert role="status" aria-live="polite">
        <Info className="h-4 w-4" aria-hidden="true" />
        <AlertDescription>
          <div className="space-y-2">
            <strong>No heatmap data available</strong>
            <p>
              The simulation completed but no data was returned. This might
              happen if:
            </p>
            <ul className="list-disc list-inside text-sm space-y-1">
              <li>
                Network connectivity issues occurred during data generation
              </li>
              <li>The backend simulation service is temporarily unavailable</li>
              <li>Invalid parameters were provided</li>
            </ul>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="mt-2"
              aria-label="Retry heatmap data generation"
            >
              <RefreshCw className="w-4 h-4 mr-2" aria-hidden="true" />
              Try Again
            </Button>
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Info Banner */}
      <Alert>
        <Info className="h-4 w-4" aria-hidden="true" />
        <AlertDescription>
          <strong>Heatmap Analysis:</strong> This visualization shows undercut
          success probability across different gap sizes (0-30s) and tire
          compounds. Darker/warmer colors indicate higher success probability.
          Hover over cells for detailed values.
        </AlertDescription>
      </Alert>

      {/* Plotly Heatmap */}
      <Card>
        <CardContent className="p-6">
          <div
            role="img"
            aria-label={`Heatmap showing undercut success probability for ${baseRequest.gp.toUpperCase()} ${
              baseRequest.year
            }. Interactive chart with gap sizes on X-axis and tire compounds on Y-axis.`}
          >
            <Plot
              data={[
                {
                  x: plotData.x,
                  y: plotData.y,
                  z: plotData.z,
                  type: "heatmap",
                  colorscale: [
                    [0, "#dc2626"], // Red for low probability
                    [0.25, "#f97316"], // Orange
                    [0.5, "#eab308"], // Yellow
                    [0.75, "#22c55e"], // Green
                    [1, "#15803d"], // Dark green for high probability
                  ],
                  showscale: true,
                  colorbar: {
                    title: {
                      text: "Success Probability (%)",
                      side: "right",
                    },
                    ticksuffix: "%",
                    thickness: 15,
                    len: 0.8,
                  },
                  hoverongaps: false,
                  hovertemplate:
                    "<b>Gap:</b> %{x}<br>" +
                    "<b>Compound:</b> %{y}<br>" +
                    "<b>Success Probability:</b> %{z:.1f}%<br>" +
                    "<extra></extra>",
                  zmin: 0,
                  zmax: 100,
                },
              ]}
              layout={{
                title: {
                  text: `Undercut Success Probability - ${baseRequest.gp.toUpperCase()} ${
                    baseRequest.year
                  }`,
                  font: { size: 16 },
                },
                xaxis: {
                  title: "Current Gap to Target Driver",
                  tickangle: 0,
                  showgrid: false,
                },
                yaxis: {
                  title: "New Tire Compound",
                  showgrid: false,
                },
                plot_bgcolor: "rgba(0,0,0,0)",
                paper_bgcolor: "rgba(0,0,0,0)",
                font: {
                  color: "#374151",
                  size: 12,
                },
                margin: { l: 80, r: 80, t: 60, b: 60 },
                height: 400,
              }}
              config={{
                displayModeBar: true,
                modeBarButtonsToRemove: [
                  "pan2d",
                  "lasso2d",
                  "select2d",
                  "autoScale2d",
                  "hoverClosestCartesian",
                  "hoverCompareCartesian",
                ],
                displaylogo: false,
                responsive: true,
                toImageButtonOptions: {
                  format: "png",
                  filename: `f1-undercut-heatmap-${baseRequest.gp}-${baseRequest.year}`,
                  height: 500,
                  width: 800,
                  scale: 1,
                },
              }}
              className="w-full"
            />
          </div>
        </CardContent>
      </Card>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div
              className="text-center"
              role="img"
              aria-label={`High success scenarios: ${
                summaryStats.highSuccessCount
              } out of ${plotData.z.flat().length} total scenarios`}
            >
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {summaryStats.highSuccessCount}
              </p>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                High Success Scenarios
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                ≥50% probability
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div
              className="text-center"
              role="img"
              aria-label={`Average success rate: ${summaryStats.avgSuccessRate}%`}
            >
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {summaryStats.avgSuccessRate}%
              </p>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Average Success Rate
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Across all scenarios
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div
              className="text-center"
              role="img"
              aria-label={`Best compound: ${summaryStats.bestCompound} compound has highest average success rate`}
            >
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {summaryStats.bestCompound}
              </p>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Best Compound
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Highest avg success rate
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Keyboard Instructions */}
      <div className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <p className="font-medium mb-1">Accessibility Instructions:</p>
        <ul className="space-y-1">
          <li>• Use Tab to navigate through interactive elements</li>
          <li>• Hover over heatmap cells to see detailed probability values</li>
          <li>• Use the toolbar above the chart to download or zoom</li>
          <li>
            • Summary statistics are provided in text format below the chart
          </li>
        </ul>
      </div>
    </div>
  );
});
