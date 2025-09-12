'use client'

import { SimulationForm } from '@/components/simulation-form'

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-slate-900 mb-4">
          Undercut Probability Calculator
        </h2>
        <p className="text-slate-600 max-w-2xl mx-auto">
          Analyze the probability of a successful undercut maneuver using real F1 data, 
          tire degradation models, and Monte Carlo simulation.
        </p>
      </div>
      
      <SimulationForm />
    </div>
  )
}
