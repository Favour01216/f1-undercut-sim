"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SimulationResponse } from "@/lib/api";
import { PerformanceChart } from "@/components/performance-chart";

interface SimulationResultsProps {
  result: SimulationResponse;
}

export function SimulationResults({ result }: SimulationResultsProps) {
  const probability = result.p_undercut;
  const probabilityPercent = (probability * 100).toFixed(1);

  const getSuccessLevel = (prob: number) => {
    if (prob >= 0.7)
      return {
        level: "High",
        color: "text-green-600",
        bg: "bg-green-50",
        emoji: "✅",
      };
    if (prob >= 0.4)
      return {
        level: "Medium",
        color: "text-yellow-600",
        bg: "bg-yellow-50",
        emoji: "⚠️",
      };
    return {
      level: "Low",
      color: "text-red-600",
      bg: "bg-red-50",
      emoji: "❌",
    };
  };

  const successLevel = getSuccessLevel(probability);

  return (
    <div className="space-y-6">
      {/* Main Result Card */}
      <Card className="border-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🎯 Undercut Probability Result
          </CardTitle>
          <CardDescription>
            Monte Carlo simulation with{" "}
            {result.assumptions.monte_carlo_samples.toLocaleString()} samples
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Main Probability */}
            <div className={`p-4 rounded-lg ${successLevel.bg} text-center`}>
              <div className="text-3xl font-bold mb-2">
                {successLevel.emoji}
              </div>
              <div className={`text-3xl font-bold ${successLevel.color}`}>
                {probabilityPercent}%
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Success Probability
              </p>
              <p className={`text-xs font-medium ${successLevel.color} mt-2`}>
                {successLevel.level} Confidence
              </p>
            </div>

            {/* Pit Loss */}
            <div className="p-4 rounded-lg bg-blue-50 text-center">
              <div className="text-2xl mb-2">⛽</div>
              <div className="text-2xl font-bold text-blue-600">
                {result.pitLoss_s.toFixed(2)}s
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Expected Pit Loss
              </p>
            </div>

            {/* Outlap Delta */}
            <div className="p-4 rounded-lg bg-orange-50 text-center">
              <div className="text-2xl mb-2">🔥</div>
              <div className="text-2xl font-bold text-orange-600">
                {result.outLapDelta_s.toFixed(2)}s
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Outlap Time Penalty
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            📋 Analysis Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium">Current Gap</p>
                <p className="text-2xl font-bold">
                  {result.assumptions.current_gap_s?.toFixed(2) || "N/A"}s
                </p>
              </div>

              <div>
                <p className="text-sm font-medium">Driver B Tire Age</p>
                <p className="text-lg">
                  {result.assumptions.tire_age_driver_b || "N/A"} laps
                </p>
              </div>

              {result.assumptions.avg_degradation_penalty_s && (
                <div>
                  <p className="text-sm font-medium">Expected Degradation</p>
                  <p className="text-lg">
                    {result.assumptions.avg_degradation_penalty_s.toFixed(3)}s
                  </p>
                </div>
              )}
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium mb-2">Models Used</p>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        result.assumptions.models_fitted.degradation_model
                          ? "bg-green-500"
                          : "bg-red-500"
                      }`}
                    />
                    <span className="text-sm">Tire Degradation Model</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        result.assumptions.models_fitted.pit_model
                          ? "bg-green-500"
                          : "bg-red-500"
                      }`}
                    />
                    <span className="text-sm">Pit Stop Model</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        result.assumptions.models_fitted.outlap_model
                          ? "bg-green-500"
                          : "bg-red-500"
                      }`}
                    />
                    <span className="text-sm">Outlap Performance Model</span>
                  </div>
                </div>
              </div>

              {result.assumptions.success_margin_s && (
                <div>
                  <p className="text-sm font-medium">Average Success Margin</p>
                  <p className="text-lg">
                    {result.assumptions.success_margin_s.toFixed(2)}s
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Positive = likely success, Negative = likely failure
                  </p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Chart */}
      <PerformanceChart />

      {/* Strategy Interpretation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🧠 Strategic Interpretation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {probability >= 0.7 && (
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="font-medium text-green-800">
                  Excellent Undercut Opportunity! 🟢
                </p>
                <p className="text-sm text-green-700 mt-2">
                  High probability of success. The gap, pit loss, and outlap
                  penalty favor the undercutting driver. This is an ideal time
                  to pit.
                </p>
              </div>
            )}

            {probability >= 0.4 && probability < 0.7 && (
              <div className="p-4 bg-yellow-50 rounded-lg">
                <p className="font-medium text-yellow-800">
                  Risky but Possible Undercut 🟡
                </p>
                <p className="text-sm text-yellow-700 mt-2">
                  Moderate success probability. Consider track position, race
                  situation, and alternative strategies. The undercut could work
                  but carries significant risk.
                </p>
              </div>
            )}

            {probability < 0.4 && (
              <div className="p-4 bg-red-50 rounded-lg">
                <p className="font-medium text-red-800">
                  Undercut Likely to Fail 🔴
                </p>
                <p className="text-sm text-red-700 mt-2">
                  Low success probability. The current gap is likely too small,
                  or the pit loss/outlap penalty is too high. Consider staying
                  out or looking for alternative strategies.
                </p>
              </div>
            )}

            <div className="text-xs text-muted-foreground pt-4 border-t">
              <p>
                <strong>Note:</strong> This simulation uses Monte Carlo methods
                with tire degradation, pit stop time, and outlap performance
                models. Results are probabilistic estimates based on historical
                data and current race conditions.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
