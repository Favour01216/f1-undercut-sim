'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { SimulationResults } from '@/components/simulation-results'
import {
  SimulationRequest,
  SimulationResponse,
  GRAND_PRIX_OPTIONS,
  DRIVER_OPTIONS,
  TIRE_COMPOUNDS,
  YEAR_OPTIONS
} from '@/types/simulation'

const simulationSchema = z.object({
  gp: z.string().min(1, 'Please select a Grand Prix'),
  year: z.number().min(2020).max(2024),
  driver_a: z.string().min(1, 'Please select Driver A'),
  driver_b: z.string().min(1, 'Please select Driver B'),
  compound_a: z.enum(['SOFT', 'MEDIUM', 'HARD']),
  lap_now: z.number().min(1).max(100, 'Lap must be between 1 and 100'),
  samples: z.number().min(100).max(10000).optional().default(1000),
})

type SimulationFormData = z.infer<typeof simulationSchema>

export function SimulationForm() {
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<SimulationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const form = useForm<SimulationFormData>({
    resolver: zodResolver(simulationSchema),
    defaultValues: {
      gp: '',
      year: 2024,
      driver_a: '',
      driver_b: '',
      compound_a: 'MEDIUM',
      lap_now: 25,
      samples: 1000,
    },
  })

  const onSubmit = async (data: SimulationFormData) => {
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('/api/simulate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result: SimulationResponse = await response.json()
      setResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  const selectedDriverA = DRIVER_OPTIONS.find(d => d.id === form.watch('driver_a'))
  const selectedDriverB = DRIVER_OPTIONS.find(d => d.id === form.watch('driver_b'))
  const selectedGP = GRAND_PRIX_OPTIONS.find(gp => gp.id === form.watch('gp'))

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
                value={form.watch('gp')}
                onValueChange={(value) => form.setValue('gp', value)}
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
                <p className="text-sm text-destructive">{form.formState.errors.gp.message}</p>
              )}
            </div>

            {/* Year Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Year</label>
              <Select
                value={form.watch('year').toString()}
                onValueChange={(value) => form.setValue('year', parseInt(value))}
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
                  value={form.watch('driver_a')}
                  onValueChange={(value) => form.setValue('driver_a', value)}
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
                  value={form.watch('driver_b')}
                  onValueChange={(value) => form.setValue('driver_b', value)}
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
                value={form.watch('compound_a')}
                onValueChange={(value) => form.setValue('compound_a', value as 'SOFT' | 'MEDIUM' | 'HARD')}
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
                {...form.register('lap_now', { valueAsNumber: true })}
                placeholder="25"
              />
              {form.formState.errors.lap_now && (
                <p className="text-sm text-destructive">{form.formState.errors.lap_now.message}</p>
              )}
            </div>

            {/* Monte Carlo Samples */}
            <div className="space-y-2">
              <label className="text-sm font-medium">
                🎲 Monte Carlo Samples
              </label>
              <Select
                value={form.watch('samples')?.toString() || '1000'}
                onValueChange={(value) => form.setValue('samples', parseInt(value))}
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
                <>
                  🚀 Run Simulation
                </>
              )}
            </Button>

            {/* Scenario Summary */}
            {selectedGP && selectedDriverA && selectedDriverB && (
              <div className="mt-4 p-3 bg-muted rounded-md">
                <p className="text-sm font-medium">Scenario Summary:</p>
                <p className="text-sm text-muted-foreground">
                  {selectedDriverA.name} attempting to undercut {selectedDriverB.name}
                  at the {selectedGP.name} on lap {form.watch('lap_now')}
                  using {form.watch('compound_a')} tires
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
              <CardTitle className="text-destructive">⚠️ Simulation Error</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm">{error}</p>
              <p className="text-xs text-muted-foreground mt-2">
                Make sure the FastAPI backend is running on http://localhost:8000
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
                Configure your simulation parameters and click &quot;Run Simulation&quot;
                to see the undercut probability analysis
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
