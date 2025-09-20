"use client";

import { useState, useCallback, useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { debounce } from "lodash";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SimulationResults } from "@/components/simulation-results";
import { useSimulateMutation } from "@/lib/hooks";
import {
  type SimulationRequest,
  type SimulationResponse,
  SimulationRequestSchema,
} from "@/lib/api";
import {
  GRAND_PRIX_OPTIONS,
  DRIVER_OPTIONS,
  TIRE_COMPOUNDS,
  YEAR_OPTIONS,
} from "@/types/simulation";

// Extract only the form fields from the API schema for consistency
const simulationSchema = SimulationRequestSchema.pick({
  gp: true,
  year: true,
  driver_a: true,
  driver_b: true,
  compound_a: true,
  lap_now: true,
  samples: true,
});

type SimulationFormData = z.infer<typeof simulationSchema>;

export function SimulationForm() {
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [lastSubmission, setLastSubmission] = useState<Date | null>(null);

  // Debug: Alert when component loads
  console.log("SimulationForm component loaded");

  const form = useForm<SimulationFormData>({
    resolver: zodResolver(simulationSchema),
    defaultValues: {
      gp: "bahrain", // Use a valid enum value instead of empty string
      year: 2024,
      driver_a: "VER", // Default to a valid driver
      driver_b: "LEC", // Default to a valid driver
      compound_a: "MEDIUM",
      lap_now: 25,
      samples: 1000,
    },
  });

  // Use React Query mutation for simulations
  const simulateMutation = useSimulateMutation();

  // Debounced submit function to prevent duplicate submissions
  const debouncedSubmit = useMemo(
    () =>
      debounce(async (data: SimulationFormData) => {
        // Prevent duplicate submissions within 300ms
        const now = new Date();
        if (lastSubmission && now.getTime() - lastSubmission.getTime() < 300) {
          return;
        }
        setLastSubmission(now);

        try {
          // Create a complete simulation request with all required fields
          const simulationRequest: SimulationRequest = {
            gp: data.gp,
            year: data.year,
            driver_a: data.driver_a,
            driver_b: data.driver_b,
            compound_a: data.compound_a,
            lap_now: data.lap_now,
            samples: data.samples || 1000,
            H: 2, // Default horizon value
            p_pit_next: 1.0, // Default pit probability
          };

          console.log("Submitting simulation request:", simulationRequest);
          const result = await simulateMutation.mutateAsync(simulationRequest);
          console.log("Received simulation result:", result);
          setResult(result);
        } catch (error) {
          // Error handling is done by React Query
          console.error("Simulation failed:", error);
        }
      }, 300),
    [simulateMutation, lastSubmission]
  );

  // Memoized submit handler
  const onSubmit = useCallback(
    (data: SimulationFormData) => {
      alert("Form submitted! Check console for details.");
      console.log("Form submitted with data:", data);
      console.log("Form errors:", form.formState.errors);
      console.log("Form is valid:", form.formState.isValid);
      debouncedSubmit(data);
    },
    [debouncedSubmit, form.formState.errors, form.formState.isValid]
  );

  // Memoized derived state
  const isLoading = simulateMutation.isPending;
  const error = simulateMutation.error?.message || null;

  // Debug form state
  console.log("Current form errors:", form.formState.errors);
  console.log("Form is valid:", form.formState.isValid);
  console.log("Current form values:", form.getValues());

  // Watch form values for memoization
  const driverAValue = form.watch("driver_a");
  const driverBValue = form.watch("driver_b");
  const gpValue = form.watch("gp");

  // Memoized selected options for performance
  const selectedDriverA = useMemo(
    () => DRIVER_OPTIONS.find((d) => d.id === driverAValue),
    [driverAValue]
  );

  const selectedDriverB = useMemo(
    () => DRIVER_OPTIONS.find((d) => d.id === driverBValue),
    [driverBValue]
  );

  const selectedGP = useMemo(
    () => GRAND_PRIX_OPTIONS.find((gp) => gp.id === gpValue),
    [gpValue]
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Simulation Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🏁 Simulation Parameters
          </CardTitle>
          <CardDescription>
            Configure the undercut scenario you want to analyze
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Grand Prix Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Grand Prix</label>
              <Select
                value={form.watch("gp")}
                onValueChange={(value) => form.setValue("gp", value as any)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a Grand Prix" />
                </SelectTrigger>
                <SelectContent>
                  {GRAND_PRIX_OPTIONS.map((gp) => (
                    <SelectItem key={gp.id} value={gp.id}>
                      {gp.country} {gp.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {form.formState.errors.gp && (
                <p className="text-sm text-destructive">
                  {form.formState.errors.gp.message}
                </p>
              )}
            </div>

            {/* Year Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Year</label>
              <Select
                value={form.watch("year").toString()}
                onValueChange={(value) =>
                  form.setValue("year", parseInt(value))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {YEAR_OPTIONS.map((year) => (
                    <SelectItem key={year} value={year.toString()}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Driver Selection */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  🚗 Driver A (Undercutting)
                </label>
                <Select
                  value={form.watch("driver_a")}
                  onValueChange={(value) => form.setValue("driver_a", value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select driver" />
                  </SelectTrigger>
                  <SelectContent>
                    {DRIVER_OPTIONS.map((driver) => (
                      <SelectItem key={driver.id} value={driver.id}>
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: driver.color }}
                          />
                          {driver.name} ({driver.id})
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedDriverA && (
                  <p className="text-xs text-muted-foreground">
                    {selectedDriverA.team}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">
                  🎯 Driver B (Being Undercut)
                </label>
                <Select
                  value={form.watch("driver_b")}
                  onValueChange={(value) => form.setValue("driver_b", value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select driver" />
                  </SelectTrigger>
                  <SelectContent>
                    {DRIVER_OPTIONS.map((driver) => (
                      <SelectItem key={driver.id} value={driver.id}>
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: driver.color }}
                          />
                          {driver.name} ({driver.id})
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedDriverB && (
                  <p className="text-xs text-muted-foreground">
                    {selectedDriverB.team}
                  </p>
                )}
              </div>
            </div>

            {/* Tire Compound */}
            <div className="space-y-2">
              <label className="text-sm font-medium">
                🛞 Tire Compound (Driver A)
              </label>
              <Select
                value={form.watch("compound_a")}
                onValueChange={(value) =>
                  form.setValue(
                    "compound_a",
                    value as "SOFT" | "MEDIUM" | "HARD"
                  )
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TIRE_COMPOUNDS.map((compound) => (
                    <SelectItem key={compound.id} value={compound.id}>
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full border border-gray-300"
                          style={{ backgroundColor: compound.color }}
                        />
                        {compound.name}
                        <span className="text-xs text-muted-foreground">
                          ({compound.description})
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Current Lap */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Current Lap</label>
              <Input
                type="number"
                min="1"
                max="100"
                {...form.register("lap_now", { valueAsNumber: true })}
                placeholder="25"
              />
              {form.formState.errors.lap_now && (
                <p className="text-sm text-destructive">
                  {form.formState.errors.lap_now.message}
                </p>
              )}
            </div>

            {/* Monte Carlo Samples */}
            <div className="space-y-2">
              <label className="text-sm font-medium">
                🎲 Monte Carlo Samples
              </label>
              <Select
                value={form.watch("samples")?.toString() || "1000"}
                onValueChange={(value) =>
                  form.setValue("samples", parseInt(value))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="100">100 (Fast)</SelectItem>
                  <SelectItem value="500">500 (Balanced)</SelectItem>
                  <SelectItem value="1000">1,000 (Accurate)</SelectItem>
                  <SelectItem value="2500">2,500 (High Precision)</SelectItem>
                  <SelectItem value="5000">5,000 (Maximum)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                More samples = more accurate but slower
              </p>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
              size="lg"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-background border-t-transparent mr-2" />
                  Simulating...
                </>
              ) : (
                <>🚀 Run Simulation</>
              )}
            </Button>

            {/* Scenario Summary */}
            {selectedGP && selectedDriverA && selectedDriverB && (
              <div className="mt-4 p-3 bg-muted rounded-md">
                <p className="text-sm font-medium">Scenario Summary:</p>
                <p className="text-sm text-muted-foreground">
                  {selectedDriverA.name} attempting to undercut{" "}
                  {selectedDriverB.name}
                  at the {selectedGP.name} on lap {form.watch("lap_now")}
                  using {form.watch("compound_a")} tires
                </p>
              </div>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Results Display */}
      <div className="space-y-6">
        {error && (
          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="text-destructive">
                ⚠️ Simulation Error
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm">{error}</p>
              <p className="text-xs text-muted-foreground mt-2">
                Make sure the FastAPI backend is running on
                http://localhost:8000
              </p>
            </CardContent>
          </Card>
        )}

        {result && <SimulationResults result={result} />}

        {!result && !error && !isLoading && (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="text-6xl mb-4">📊</div>
              <p className="text-muted-foreground text-center">
                Configure your simulation parameters and click &quot;Run
                Simulation&quot; to see the undercut probability analysis
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
