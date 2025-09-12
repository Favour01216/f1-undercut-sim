'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import dynamic from 'next/dynamic'

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })

export function PerformanceChart() {
  // Placeholder data for the heatmap - in a real implementation, 
  // this would be calculated based on actual tire degradation models
  const generateHeatmapData = () => {
    const laps = Array.from({ length: 20 }, (_, i) => i + 1) // Laps 1-20
    const compounds = ['SOFT', 'MEDIUM', 'HARD']
    
    // Generate sample undercut probability data
    const z = compounds.map(compound => 
      laps.map(lap => {
        // Simulate probability based on lap and compound
        let baseProbability = 0.5
        
        // Compound effects
        if (compound === 'SOFT') baseProbability += 0.1
        else if (compound === 'HARD') baseProbability -= 0.1
        
        // Lap effects (sweet spot around lap 15-25)
        const lapFactor = Math.sin((lap - 1) * Math.PI / 25) * 0.3
        baseProbability += lapFactor
        
        // Add some randomness
        baseProbability += (Math.random() - 0.5) * 0.2
        
        // Clamp between 0 and 1
        return Math.max(0, Math.min(1, baseProbability))
      })
    )

    return { x: laps, y: compounds, z }
  }

  const { x, y, z } = generateHeatmapData()

  const plotData = [{
    x,
    y,
    z,
    type: 'heatmap' as const,
    colorscale: [
      [0, '#dc2626'],      // Red for low probability
      [0.3, '#f59e0b'],    // Orange 
      [0.6, '#eab308'],    // Yellow
      [0.8, '#22c55e'],    // Green
      [1, '#16a34a']       // Dark green for high probability
    ],
    hoverongaps: false,
    hovertemplate: 
      '<b>Lap %{x}</b><br>' +
      'Compound: %{y}<br>' +
      'Undercut Probability: %{z:.1%}' +
      '<extra></extra>',
  }]

  const layout = {
    title: {
      text: 'Undercut Probability Heatmap',
      font: { size: 16 }
    },
    xaxis: {
      title: 'Current Lap',
      tickmode: 'linear',
      tick0: 1,
      dtick: 2
    },
    yaxis: {
      title: 'Tire Compound',
    },
    margin: { t: 60, r: 20, b: 60, l: 80 },
    height: 300,
    coloraxis: {
      colorbar: {
        title: 'Success<br>Probability',
        titlefont: { size: 12 },
        tickformat: '.0%'
      }
    }
  }

  const config = {
    displayModeBar: false,
    responsive: true
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          📈 Performance Heatmap
        </CardTitle>
        <CardDescription>
          Undercut success probability by lap and tire compound (simulated data)
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
            <strong>How to read:</strong> Darker green indicates higher undercut success probability. 
            This heatmap shows how tire compound and current lap affect the likelihood of a successful undercut.
          </p>
          <p className="mt-2">
            <strong>Note:</strong> This is placeholder data. In production, this would be generated 
            from real F1 data and your trained models.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
