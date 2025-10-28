"use client";

/**
 * F1 Undercut Simulator - Racing Form Component
 * F1-themed simulation form with racing aesthetics
 */

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  SimulationRequestSchema,
  type SimulationRequest,
  F1_CIRCUITS,
  F1_DRIVERS,
  COMPOUND_CHOICES,
} from "@/lib/f1-api";
import { useF1Simulation } from "@/lib/f1-hooks";

interface F1FormProps {
  onSimulationSuccess: (result: any) => void;
}

export function F1SimulationForm({ onSimulationSuccess }: F1FormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<SimulationRequest>({
    resolver: zodResolver(SimulationRequestSchema),
    defaultValues: {
      gp: "monza",
      year: 2024,
      driver_a: "VER",
      driver_b: "LEC",
      compound_a: "SOFT",
      lap_now: 25,
      samples: 1000,
      H: 2,
      p_pit_next: 1.0,
    },
  });

  const simulation = useF1Simulation();

  const onSubmit = async (data: SimulationRequest) => {
    setIsSubmitting(true);
    try {
      const result = await simulation.mutateAsync(data);
      onSimulationSuccess(result);
    } catch (error) {
      console.error("🏎️ Simulation failed:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedCircuit = F1_CIRCUITS.find((c) => c.id === form.watch("gp"));
  const selectedDriverA = F1_DRIVERS.find(
    (d) => d.id === form.watch("driver_a")
  );
  const selectedDriverB = F1_DRIVERS.find(
    (d) => d.id === form.watch("driver_b")
  );

  return (
    <div className="pit-card p-6 space-y-6">
      <div className="racing-stripe">
        <h2 className="f1-title text-2xl mb-2">🏁 Simulation Parameters</h2>
        <p className="f1-body text-gray-300">
          Configure your undercut scenario
        </p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Circuit Selection */}
        <div className="space-y-3">
          <label className="f1-subtitle text-sm text-white">
            🏎️ Grand Prix Circuit
          </label>
          <select
            {...form.register("gp")}
            className="w-full bg-gray-900 border border-gray-600 rounded-lg p-3 text-white focus:border-red-500 focus:ring-1 focus:ring-red-500"
          >
            {F1_CIRCUITS.map((circuit) => (
              <option key={circuit.id} value={circuit.id}>
                {circuit.flag} {circuit.name}
              </option>
            ))}
          </select>
          {selectedCircuit && (
            <div className="circuit-option bg-gray-800 rounded-lg">
              <div className="circuit-flag">{selectedCircuit.flag}</div>
              <div className="circuit-info">
                <p className="circuit-name">{selectedCircuit.name}</p>
                <p className="circuit-details">
                  {selectedCircuit.length}km • {selectedCircuit.corners} corners
                  • {selectedCircuit.drsZones} DRS zones
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Year Selection */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-3">
            <label className="f1-subtitle text-sm text-white">📅 Season</label>
            <select
              {...form.register("year", { valueAsNumber: true })}
              className="w-full bg-gray-900 border border-gray-600 rounded-lg p-3 text-white focus:border-red-500 focus:ring-1 focus:ring-red-500"
            >
              <option value={2024}>2024 Season</option>
              <option value={2023}>2023 Season</option>
              <option value={2022}>2022 Season</option>
              <option value={2021}>2021 Season</option>
              <option value={2020}>2020 Season</option>
            </select>
          </div>

          <div className="space-y-3">
            <label className="f1-subtitle text-sm text-white">
              🏁 Current Lap
            </label>
            <input
              type="number"
              min="1"
              max="100"
              {...form.register("lap_now", { valueAsNumber: true })}
              className="w-full bg-gray-900 border border-gray-600 rounded-lg p-3 text-white focus:border-red-500 focus:ring-1 focus:ring-red-500"
            />
          </div>
        </div>

        {/* Driver Selection */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-3">
            <label className="f1-subtitle text-sm text-white">
              🏆 Driver A (Attacking)
            </label>
            <select
              {...form.register("driver_a")}
              className="w-full bg-gray-900 border border-gray-600 rounded-lg p-3 text-white focus:border-red-500 focus:ring-1 focus:ring-red-500"
            >
              {F1_DRIVERS.map((driver) => (
                <option key={driver.id} value={driver.id}>
                  {driver.nationality} {driver.name} ({driver.id}) -{" "}
                  {driver.team}
                </option>
              ))}
            </select>
            {selectedDriverA && (
              <div className="driver-option bg-gray-800 rounded-lg">
                <div
                  className="driver-team-color"
                  style={{ backgroundColor: selectedDriverA.color }}
                />
                <div className="driver-info">
                  <p className="driver-name">{selectedDriverA.name}</p>
                  <p className="driver-details">{selectedDriverA.team}</p>
                </div>
                <div className="driver-number">#{selectedDriverA.number}</div>
              </div>
            )}
          </div>

          <div className="space-y-3">
            <label className="f1-subtitle text-sm text-white">
              🎯 Driver B (Defending)
            </label>
            <select
              {...form.register("driver_b")}
              className="w-full bg-gray-900 border border-gray-600 rounded-lg p-3 text-white focus:border-red-500 focus:ring-1 focus:ring-red-500"
            >
              {F1_DRIVERS.map((driver) => (
                <option key={driver.id} value={driver.id}>
                  {driver.nationality} {driver.name} ({driver.id}) -{" "}
                  {driver.team}
                </option>
              ))}
            </select>
            {selectedDriverB && (
              <div className="driver-option bg-gray-800 rounded-lg">
                <div
                  className="driver-team-color"
                  style={{ backgroundColor: selectedDriverB.color }}
                />
                <div className="driver-info">
                  <p className="driver-name">{selectedDriverB.name}</p>
                  <p className="driver-details">{selectedDriverB.team}</p>
                </div>
                <div className="driver-number">#{selectedDriverB.number}</div>
              </div>
            )}
          </div>
        </div>

        {/* Tire Strategy */}
        <div className="space-y-3">
          <label className="f1-subtitle text-sm text-white">
            🛞 New Tire Compound
          </label>
          <div className="grid grid-cols-3 gap-4">
            {COMPOUND_CHOICES.map((compound) => (
              <label
                key={compound}
                className={`
                  cursor-pointer rounded-lg p-3 text-center transition-all relative
                  ${
                    form.watch("compound_a") === compound
                      ? "ring-3 ring-cyan-400 shadow-lg shadow-cyan-400/50 transform scale-102"
                      : "ring-1 ring-gray-600 hover:ring-gray-400"
                  }
                  ${
                    compound === "SOFT"
                      ? "tire-soft"
                      : compound === "MEDIUM"
                      ? "tire-medium"
                      : "tire-hard"
                  }
                `}
              >
                <input
                  type="radio"
                  value={compound}
                  {...form.register("compound_a")}
                  className="sr-only"
                />
                {form.watch("compound_a") === compound && (
                  <div className="absolute top-1 right-1 w-6 h-6 bg-cyan-400 rounded-full flex items-center justify-center">
                    <svg
                      className="w-4 h-4 text-gray-900"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                )}
                <div className="f1-subtitle text-sm">{compound}</div>
                <div className="text-xs mt-1">
                  {compound === "SOFT"
                    ? "Fastest lap times"
                    : compound === "MEDIUM"
                    ? "Balanced performance"
                    : "Longest stint"}
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Advanced Parameters */}
        <details className="group">
          <summary className="f1-subtitle text-sm text-white cursor-pointer hover:text-red-400 transition-colors">
            ⚙️ Advanced Parameters
          </summary>
          <div className="mt-4 space-y-4 pl-4 border-l-2 border-red-500">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="f1-body text-sm text-gray-300">
                  Simulation Samples
                </label>
                <input
                  type="number"
                  min="100"
                  max="10000"
                  step="100"
                  {...form.register("samples", { valueAsNumber: true })}
                  className="w-full bg-gray-900 border border-gray-600 rounded-lg p-3 text-white focus:border-red-500 focus:ring-1 focus:ring-red-500"
                />
              </div>
              <div className="space-y-2">
                <label className="f1-body text-sm text-gray-300">
                  Horizon (laps)
                </label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  {...form.register("H", { valueAsNumber: true })}
                  className="w-full bg-gray-900 border border-gray-600 rounded-lg p-3 text-white focus:border-red-500 focus:ring-1 focus:ring-red-500"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="f1-body text-sm text-gray-300">
                Pit Probability
              </label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                {...form.register("p_pit_next", { valueAsNumber: true })}
                className="w-full bg-gray-900 border border-gray-600 rounded-lg p-3 text-white focus:border-red-500 focus:ring-1 focus:ring-red-500"
              />
            </div>
          </div>
        </details>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="f1-button w-full py-4 text-lg speed-lines"
        >
          {isSubmitting ? (
            <div className="flex items-center justify-center gap-3">
              <div className="f1-loading" />
              <span>🏎️ Analyzing Race Strategy...</span>
            </div>
          ) : (
            <span>🚀 Run Undercut Simulation</span>
          )}
        </button>

        {/* Error Display */}
        {simulation.error && (
          <div className="bg-red-900/50 border border-red-500 rounded-lg p-4">
            <p className="f1-body text-red-200">
              🚨 {simulation.error.message}
            </p>
          </div>
        )}
      </form>
    </div>
  );
}

