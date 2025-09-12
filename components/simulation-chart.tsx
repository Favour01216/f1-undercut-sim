'use client'

import { useMemo } from 'react'

interface SimulationChartProps {
  data: {
    degradation?: {
      analyses?: Array<{
        compound: string
        predicted_performance: number[]
        stint_length: number
      }>
    }
    strategy?: {
      recommended_strategy?: {
        pit_windows?: Array<{
          lap_start: number
          lap_end: number
          tire_compound: string
        }>
      }
    }
  }
}

export function SimulationChart({ data }: SimulationChartProps) {
  const chartData = useMemo(() => {
    if (!data.degradation?.analyses) return null

    const analyses = data.degradation.analyses
    const maxPerformance = Math.max(...analyses.flatMap(a => a.predicted_performance || []))
    const minPerformance = Math.min(...analyses.flatMap(a => a.predicted_performance || []))
    const maxLaps = Math.max(...analyses.map(a => a.stint_length))

    return { analyses, maxPerformance, minPerformance, maxLaps }
  }, [data])

  if (!chartData) {
    return (
      <div className="flex items-center justify-center h-64 bg-muted rounded-lg">
        <p className="text-muted-foreground">No data available for visualization</p>
      </div>
    )
  }

  const { analyses, maxPerformance, minPerformance, maxLaps } = chartData

  return (
    <div className="w-full h-96 p-4 border rounded-lg bg-background">
      <h3 className="text-lg font-semibold mb-4">Tire Performance Analysis</h3>
      
      <div className="relative h-80 w-full">
        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-muted-foreground">
          <span>{Math.round(maxPerformance)}%</span>
          <span>{Math.round((maxPerformance + minPerformance) / 2)}%</span>
          <span>{Math.round(minPerformance)}%</span>
        </div>
        
        {/* Chart area */}
        <div className="ml-8 h-full border-l border-b border-border relative">
          {/* Grid lines */}
          <div className="absolute inset-0 grid grid-rows-4 opacity-20">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="border-t border-border" />
            ))}
          </div>
          
          {/* Performance curves */}
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            {analyses.map((analysis, index) => {
              const color = getTireColor(analysis.compound)
              const points = analysis.predicted_performance.map((perf, lapIndex) => {
                const x = (lapIndex / (analysis.stint_length - 1)) * 100
                const y = 100 - ((perf - minPerformance) / (maxPerformance - minPerformance)) * 100
                return `${x},${y}`
              }).join(' ')
              
              return (
                <polyline
                  key={analysis.compound}
                  points={points}
                  fill="none"
                  stroke={color}
                  strokeWidth="2"
                  vectorEffect="non-scaling-stroke"
                />
              )
            })}
          </svg>
        </div>
        
        {/* X-axis labels */}
        <div className="ml-8 mt-2 flex justify-between text-xs text-muted-foreground">
          <span>Lap 1</span>
          <span>Lap {Math.round(maxLaps / 2)}</span>
          <span>Lap {maxLaps}</span>
        </div>
      </div>
      
      {/* Legend */}
      <div className="mt-4 flex gap-4 justify-center">
        {analyses.map((analysis) => (
          <div key={analysis.compound} className="flex items-center gap-2">
            <div 
              className="w-4 h-1 rounded"
              style={{ backgroundColor: getTireColor(analysis.compound) }}
            />
            <span className="text-sm">{analysis.compound}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function getTireColor(compound: string): string {
  switch (compound.toUpperCase()) {
    case 'SOFT':
      return '#ef4444' // Red
    case 'MEDIUM':
      return '#eab308' // Yellow
    case 'HARD':
      return '#6b7280' // Gray
    default:
      return '#888888'
  }
}