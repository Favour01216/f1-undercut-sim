export interface SimulationRequest {
  gp: string
  year: number
  driver_a: string
  driver_b: string
  compound_a: 'SOFT' | 'MEDIUM' | 'HARD'
  lap_now: number
  samples?: number
}

export interface SimulationResponse {
  p_undercut: number
  pitLoss_s: number
  outLapDelta_s: number
  assumptions: {
    current_gap_s: number
    tire_age_driver_b: number
    models_fitted: {
      deg_model: boolean
      pit_model: boolean
      outlap_model: boolean
    }
    monte_carlo_samples: number
    [key: string]: any
  }
}

export interface GrandPrix {
  id: string
  name: string
  country: string
}

export const GRAND_PRIX_OPTIONS: GrandPrix[] = [
  { id: 'bahrain', name: 'Bahrain Grand Prix', country: '🇧🇭' },
  { id: 'saudi-arabia', name: 'Saudi Arabian Grand Prix', country: '🇸🇦' },
  { id: 'australia', name: 'Australian Grand Prix', country: '🇦🇺' },
  { id: 'japan', name: 'Japanese Grand Prix', country: '🇯🇵' },
  { id: 'china', name: 'Chinese Grand Prix', country: '🇨🇳' },
  { id: 'miami', name: 'Miami Grand Prix', country: '🇺🇸' },
  { id: 'monaco', name: 'Monaco Grand Prix', country: '🇲🇨' },
  { id: 'spain', name: 'Spanish Grand Prix', country: '🇪🇸' },
  { id: 'canada', name: 'Canadian Grand Prix', country: '🇨🇦' },
  { id: 'austria', name: 'Austrian Grand Prix', country: '🇦🇹' },
  { id: 'britain', name: 'British Grand Prix', country: '🇬🇧' },
  { id: 'hungary', name: 'Hungarian Grand Prix', country: '🇭🇺' },
  { id: 'belgium', name: 'Belgian Grand Prix', country: '🇧🇪' },
  { id: 'netherlands', name: 'Dutch Grand Prix', country: '🇳🇱' },
  { id: 'italy', name: 'Italian Grand Prix', country: '🇮🇹' },
  { id: 'singapore', name: 'Singapore Grand Prix', country: '🇸🇬' },
  { id: 'azerbaijan', name: 'Azerbaijan Grand Prix', country: '🇦🇿' },
  { id: 'qatar', name: 'Qatar Grand Prix', country: '🇶🇦' },
  { id: 'united-states', name: 'United States Grand Prix', country: '🇺🇸' },
  { id: 'mexico', name: 'Mexican Grand Prix', country: '🇲🇽' },
  { id: 'brazil', name: 'Brazilian Grand Prix', country: '🇧🇷' },
  { id: 'las-vegas', name: 'Las Vegas Grand Prix', country: '🇺🇸' },
  { id: 'abu-dhabi', name: 'Abu Dhabi Grand Prix', country: '🇦🇪' },
]

export const DRIVER_OPTIONS = [
  { id: 'VER', name: 'Max Verstappen', team: 'Red Bull', color: '#0600EF' },
  { id: 'PER', name: 'Sergio Pérez', team: 'Red Bull', color: '#0600EF' },
  { id: 'HAM', name: 'Lewis Hamilton', team: 'Mercedes', color: '#00D2BE' },
  { id: 'RUS', name: 'George Russell', team: 'Mercedes', color: '#00D2BE' },
  { id: 'LEC', name: 'Charles Leclerc', team: 'Ferrari', color: '#DC0000' },
  { id: 'SAI', name: 'Carlos Sainz', team: 'Ferrari', color: '#DC0000' },
  { id: 'NOR', name: 'Lando Norris', team: 'McLaren', color: '#FF9800' },
  { id: 'PIA', name: 'Oscar Piastri', team: 'McLaren', color: '#FF9800' },
  { id: 'ALO', name: 'Fernando Alonso', team: 'Aston Martin', color: '#006F62' },
  { id: 'STR', name: 'Lance Stroll', team: 'Aston Martin', color: '#006F62' },
]

export const TIRE_COMPOUNDS = [
  { id: 'SOFT', name: 'Soft', color: '#FF0000', description: 'Fastest, shortest life' },
  { id: 'MEDIUM', name: 'Medium', color: '#FFD700', description: 'Balanced performance' },
  { id: 'HARD', name: 'Hard', color: '#FFFFFF', description: 'Longest life, slowest' },
] as const

export const YEAR_OPTIONS = [2024, 2023, 2022, 2021, 2020]
