"use client";

/**
 * F1 Undercut Simulator - Racing Results Component
 * F1-themed results visualization with racing aesthetics
 */

import React from "react";
import { type SimulationResponse } from "@/lib/f1-api";

interface F1ResultsProps {
  result: SimulationResponse;
}

export function F1Results({ result }: F1ResultsProps) {
  const probability = result.p_undercut;
  const probabilityPercent = (probability * 100).toFixed(1);

  // Determine success level and colors
  const getSuccessLevel = (prob: number) => {
    if (prob >= 0.7)
      return {
        level: "VICTORY",
        flag: "🏁",
        class: "success",
        message: "Excellent undercut opportunity! High probability of success.",
      };
    if (prob >= 0.4)
      return {
        level: "CAUTION",
        flag: "🟡",
        class: "warning",
        message:
          "Risky but possible undercut. Consider track position and alternatives.",
      };
    return {
      level: "DANGER",
      flag: "🔴",
      class: "danger",
      message: "Undercut likely to fail. Gap too small or pit loss too high.",
    };
  };

  const successInfo = getSuccessLevel(probability);

  return (
    <div className="space-y-6">
      {/* Main Results Header */}
      <div className="pit-card p-6">
        <div className="racing-stripe">
          <h2 className="f1-title text-2xl mb-2">🎯 Simulation Results</h2>
          <p className="f1-body text-gray-300">
            Monte Carlo analysis with{" "}
            {result.assumptions.monte_carlo_samples.toLocaleString()} samples
          </p>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Main Probability */}
        <div className={`result-metric ${successInfo.class}`}>
          <div className="text-4xl mb-2">{successInfo.flag}</div>
          <p className="result-value">{probabilityPercent}%</p>
          <p className="result-label">Undercut Success</p>
          <div className="text-xs mt-2 font-semibold">{successInfo.level}</div>
        </div>

        {/* Pit Loss */}
        <div className="result-metric bg-gradient-to-br from-gray-800 to-gray-900 text-white">
          <div className="text-4xl mb-2">⏱️</div>
          <p className="result-value">{result.pitLoss_s.toFixed(2)}s</p>
          <p className="result-label">Pit Stop Loss</p>
          <div className="text-xs mt-2 text-gray-300">
            Time lost in pit lane
          </div>
        </div>

        {/* Outlap Penalty */}
        <div className="result-metric bg-gradient-to-br from-orange-600 to-red-600 text-white">
          <div className="text-4xl mb-2">🔥</div>
          <p className="result-value">{result.outLapDelta_s.toFixed(2)}s</p>
          <p className="result-label">Outlap Penalty</p>
          <div className="text-xs mt-2">Fresh tire warm-up loss</div>
        </div>
      </div>

      {/* Expected Margins */}
      {result.expected_margin_s && (
        <div className="pit-card p-6">
          <h3 className="f1-subtitle text-lg mb-4 text-white">
            📊 Expected Time Margins
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <p className="f1-number text-2xl text-white">
                {result.expected_margin_s.toFixed(2)}s
              </p>
              <p className="f1-body text-sm text-gray-300 mt-1">
                Expected Margin
              </p>
            </div>
            {result.ci_low_s && result.ci_high_s && (
              <>
                <div className="text-center">
                  <p className="f1-number text-2xl text-red-400">
                    {result.ci_low_s.toFixed(2)}s
                  </p>
                  <p className="f1-body text-sm text-gray-300 mt-1">
                    90% CI Lower
                  </p>
                </div>
                <div className="text-center">
                  <p className="f1-number text-2xl text-green-400">
                    {result.ci_high_s.toFixed(2)}s
                  </p>
                  <p className="f1-body text-sm text-gray-300 mt-1">
                    90% CI Upper
                  </p>
                </div>
              </>
            )}
          </div>
          <div className="mt-4 p-3 bg-gray-800 rounded-lg">
            <p className="f1-body text-xs text-gray-300">
              <strong>Interpretation:</strong> Positive values indicate likely
              success, negative values indicate likely failure. The confidence
              interval shows the range of expected outcomes.
            </p>
          </div>
        </div>
      )}

      {/* Race Situation Analysis */}
      <div className="pit-card p-6">
        <h3 className="f1-subtitle text-lg mb-4 text-white">
          🏁 Race Situation
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="f1-number text-xl text-blue-400">
              {result.assumptions.current_gap_s.toFixed(2)}s
            </p>
            <p className="f1-body text-sm text-gray-300 mt-1">Current Gap</p>
          </div>
          <div className="text-center">
            <p className="f1-number text-xl text-purple-400">
              {result.assumptions.tire_age_driver_b}
            </p>
            <p className="f1-body text-sm text-gray-300 mt-1">
              Defender Tire Age
            </p>
          </div>
          <div className="text-center">
            <p className="f1-number text-xl text-green-400">{result.H_used}</p>
            <p className="f1-body text-sm text-gray-300 mt-1">Laps Simulated</p>
          </div>
          <div className="text-center">
            <div
              className={`tire-indicator mx-auto ${
                result.assumptions.compound_a === "SOFT"
                  ? "tire-soft"
                  : result.assumptions.compound_a === "MEDIUM"
                  ? "tire-medium"
                  : "tire-hard"
              }`}
            >
              {result.assumptions.compound_a[0]}
            </div>
            <p className="f1-body text-sm text-gray-300 mt-1">New Compound</p>
          </div>
        </div>
      </div>

      {/* Models Status */}
      <div className="pit-card p-6">
        <h3 className="f1-subtitle text-lg mb-4 text-white">🔧 Model Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg">
            <div
              className={`w-3 h-3 rounded-full ${
                result.assumptions.models_fitted.degradation_model
                  ? "bg-green-500"
                  : "bg-red-500"
              }`}
            />
            <div>
              <p className="f1-body text-sm text-white">Tire Degradation</p>
              <p className="f1-body text-xs text-gray-300">
                {result.assumptions.models_fitted.degradation_model
                  ? "Active"
                  : "Fallback"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg">
            <div
              className={`w-3 h-3 rounded-full ${
                result.assumptions.models_fitted.pit_model
                  ? "bg-green-500"
                  : "bg-red-500"
              }`}
            />
            <div>
              <p className="f1-body text-sm text-white">Pit Stop Model</p>
              <p className="f1-body text-xs text-gray-300">
                {result.assumptions.models_fitted.pit_model
                  ? "Active"
                  : "Fallback"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg">
            <div
              className={`w-3 h-3 rounded-full ${
                result.assumptions.models_fitted.outlap_model
                  ? "bg-green-500"
                  : "bg-red-500"
              }`}
            />
            <div>
              <p className="f1-body text-sm text-white">Outlap Performance</p>
              <p className="f1-body text-xs text-gray-300">
                {result.assumptions.models_fitted.outlap_model
                  ? "Active"
                  : "Fallback"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Strategic Interpretation */}
      <div className="pit-card p-6">
        <h3 className="f1-subtitle text-lg mb-4 text-white">
          🧠 Strategic Analysis
        </h3>
        <div
          className={`p-4 rounded-lg border-l-4 ${
            successInfo.class === "success"
              ? "bg-green-900/30 border-green-500"
              : successInfo.class === "warning"
              ? "bg-yellow-900/30 border-yellow-500"
              : "bg-red-900/30 border-red-500"
          }`}
        >
          <p className="f1-body text-white mb-2">
            <strong>
              {successInfo.flag} {successInfo.level}
            </strong>
          </p>
          <p className="f1-body text-gray-300 text-sm">{successInfo.message}</p>
        </div>

        {/* Additional insights */}
        <div className="mt-4 space-y-2">
          {result.assumptions.avg_degradation_penalty_s && (
            <div className="flex justify-between items-center p-2 bg-gray-800 rounded">
              <span className="f1-body text-sm text-gray-300">
                Average degradation penalty:
              </span>
              <span className="f1-number text-sm text-white">
                {result.assumptions.avg_degradation_penalty_s.toFixed(3)}s/lap
              </span>
            </div>
          )}
          <div className="flex justify-between items-center p-2 bg-gray-800 rounded">
            <span className="f1-body text-sm text-gray-300">
              Pit probability scenario:
            </span>
            <span className="f1-number text-sm text-white">
              {(result.assumptions.p_pit_next * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        <div className="mt-4 p-3 bg-gray-900 rounded-lg border border-gray-700">
          <p className="f1-body text-xs text-gray-400">
            <strong>⚠️ Disclaimer:</strong> This simulation uses Monte Carlo
            methods with tire degradation, pit stop time, and outlap performance
            models. Results are probabilistic estimates based on historical data
            and current race conditions. Real F1 strategy involves many more
            variables.
          </p>
        </div>
      </div>
    </div>
  );
}
