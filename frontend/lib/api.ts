/**
 * API client for the F1 Undercut Simulator backend
 */

import { SimulationRequest, SimulationResponse } from '@/types/simulation'

/**
 * Base API utility for making requests to the backend
 */
export const api = {
  /**
   * Run an undercut simulation
   */
  simulate: async (params: SimulationRequest): Promise<SimulationResponse> => {
    const response = await fetch('/api/simulate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Simulation failed (${response.status}): ${errorText}`)
    }

    return response.json()
  },

  /**
   * Check API health status
   */
  healthCheck: async (): Promise<{ status: string }> => {
    const response = await fetch('/api/health')
    
    if (!response.ok) {
      throw new Error(`Health check failed (${response.status})`)
    }

    return response.json()
  }
}
