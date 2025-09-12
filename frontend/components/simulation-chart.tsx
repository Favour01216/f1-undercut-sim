'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import dynamic from 'next/dynamic'

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })

interface SimulationChartProps {
  data?: {
    x: number[]
    y: number[]
    driver?: string
    label?: string
  }[]
}

export function SimulationChart({ data }: SimulationChartProps = {}) {
  // If no data is provided, we'll show a default visualization
  const defaultData = [
    {
      x: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
      y: [90.0, 90.1, 90.3, 90.6, 91.0, 91.5, 92.1, 92.8, 93.6, 94.5],
      name: 'SOFT',
      type: 'scatter',
      mode: 'lines+markers',
      marker: { color: '#FF0000' },
      line: { width: 2 }
    },
    {
      x: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
      y: [91.0, 91.1, 91.2, 91.4, 91.7, 92.0, 92.4, 92.9, 93.5, 94.2],
      name: 'MEDIUM',
      type: 'scatter',
      mode: 'lines+markers',
      marker: { color: '#FFDD00' },
      line: { width: 2 }
    },
    {
      x: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
      y: [92.0, 92.0, 92.1, 92.2, 92.4, 92.6, 92.9, 93.3, 93.7, 94.2],
      name: 'HARD',
      type: 'scatter',
      mode: 'lines+markers',
      marker: { color: '#FFFFFF', line: { width: 1, color: '#333' } },
      line: { width: 2 }
    }
  ] as any[]

  const plotData = data || defaultData

  const layout = {
    title: data ? 'Simulation Results' : 'Tire Degradation Example',
    xaxis: {
      title: 'Laps',
      tickmode: 'linear',
      tick0: 1,
      dtick: 2
    },
    yaxis: {
      title: 'Lap Time (s)',
    },
    margin: { t: 60, r: 20, b: 60, l: 80 },
    height: 300,
    legend: {
      orientation: 'h',
      y: -0.2
    },
    hovermode: 'closest'
  }

  const config = {
    displayModeBar: false,
    responsive: true
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          📈 Lap Time Evolution
        </CardTitle>
        <CardDescription>
          {data ? 'Simulation results visualization' : 'Example tire degradation over time'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="w-full">
          <Plot
            data={plotData}
            layout={layout}
            config={config}
            style={{ width: '100%', height: '300px' }}
          />
        </div>
        <div className="mt-4 text-sm text-muted-foreground">
          <p>
            {data ? 
              'This chart shows the actual simulation results.' :
              'Tire compounds have different degradation profiles. Soft tires are faster initially but degrade more quickly.'}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
