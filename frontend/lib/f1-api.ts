/**
 * F1 Undercut Simulator - API Client v2.0
 * Clean, racing-themed API client that exactly matches backend schemas
 */

import { z } from "zod";

// ============================================================================
// Backend Schema Matching (EXACT COPY)
// ============================================================================

// Grand Prix circuits (exactly as backend defines)
export const GP_CHOICES = [
  "bahrain",
  "imola",
  "monza",
  "monaco",
  "spain",
  "canada",
  "austria",
  "silverstone",
  "hungary",
  "belgium",
  "netherlands",
  "italy",
  "singapore",
  "japan",
  "qatar",
  "usa",
  "mexico",
  "brazil",
  "abu_dhabi",
  "australia",
  "china",
  "azerbaijan",
  "miami",
  "france",
  "portugal",
  "russia",
  "turkey",
  "saudi_arabia",
  "las_vegas",
] as const;

// Tire compounds (exactly as backend defines)
export const COMPOUND_CHOICES = ["SOFT", "MEDIUM", "HARD"] as const;

// Request validation schema with string-to-number coercion for form compatibility
export const SimulationRequestSchema = z.object({
  gp: z.enum(GP_CHOICES),
  year: z.coerce.number().int().min(2020).max(2024),
  driver_a: z.string().min(1).max(50),
  driver_b: z.string().min(1).max(50),
  compound_a: z.enum(COMPOUND_CHOICES),
  lap_now: z.coerce.number().int().min(1).max(100),
  samples: z.coerce.number().int().min(1).max(10000).default(1000),
  H: z.coerce.number().int().min(1).max(5).default(2),
  p_pit_next: z.coerce.number().min(0).max(1).default(1.0),
});

// Models fitted sub-schema
const ModelsFittedSchema = z.object({
  degradation_model: z.boolean(),
  pit_model: z.boolean(),
  outlap_model: z.boolean(),
});

// Scenario distribution sub-schema
const ScenarioDistributionSchema = z.object({
  b_stays_out: z.number(),
  b_pits_lap1: z.number(),
});

// Assumptions schema (flexible to match backend)
const AssumptionsSchema = z.object({
  current_gap_s: z.number(),
  tire_age_driver_b: z.number(),
  H_laps_simulated: z.number(),
  p_pit_next: z.number(),
  compound_a: z.string(),
  scenario_distribution: ScenarioDistributionSchema,
  models_fitted: ModelsFittedSchema,
  monte_carlo_samples: z.number(),
  avg_degradation_penalty_s: z.number(),
  success_margin_s: z.number(),
});

// Response validation schema (matches SimulateResponse exactly)
export const SimulationResponseSchema = z.object({
  p_undercut: z.number().min(0).max(1),
  pitLoss_s: z.number(),
  outLapDelta_s: z.number(),
  avgMargin_s: z.number().optional(),
  expected_margin_s: z.number().optional(),
  ci_low_s: z.number().optional(),
  ci_high_s: z.number().optional(),
  H_used: z.number().int(),
  assumptions: AssumptionsSchema,
});

// ============================================================================
// TypeScript Types
// ============================================================================

export type GPChoice = (typeof GP_CHOICES)[number];
export type CompoundChoice = (typeof COMPOUND_CHOICES)[number];
export type SimulationRequest = z.infer<typeof SimulationRequestSchema>;
export type SimulationResponse = z.infer<typeof SimulationResponseSchema>;

// ============================================================================
// F1 Circuit Data
// ============================================================================

export interface F1Circuit {
  id: GPChoice;
  name: string;
  country: string;
  flag: string;
  length: number; // km
  corners: number;
  drsZones: number;
}

export const F1_CIRCUITS: F1Circuit[] = [
  {
    id: "bahrain",
    name: "Bahrain International Circuit",
    country: "Bahrain",
    flag: "🇧🇭",
    length: 5.412,
    corners: 15,
    drsZones: 3,
  },
  {
    id: "imola",
    name: "Autodromo Enzo e Dino Ferrari",
    country: "Italy",
    flag: "🇮🇹",
    length: 4.909,
    corners: 19,
    drsZones: 2,
  },
  {
    id: "monza",
    name: "Autodromo Nazionale Monza",
    country: "Italy",
    flag: "🇮🇹",
    length: 5.793,
    corners: 11,
    drsZones: 3,
  },
  {
    id: "monaco",
    name: "Circuit de Monaco",
    country: "Monaco",
    flag: "🇲🇨",
    length: 3.337,
    corners: 19,
    drsZones: 1,
  },
  {
    id: "spain",
    name: "Circuit de Barcelona-Catalunya",
    country: "Spain",
    flag: "🇪🇸",
    length: 4.675,
    corners: 16,
    drsZones: 2,
  },
  {
    id: "canada",
    name: "Circuit Gilles Villeneuve",
    country: "Canada",
    flag: "🇨🇦",
    length: 4.361,
    corners: 14,
    drsZones: 3,
  },
  {
    id: "austria",
    name: "Red Bull Ring",
    country: "Austria",
    flag: "🇦🇹",
    length: 4.318,
    corners: 9,
    drsZones: 3,
  },
  {
    id: "silverstone",
    name: "Silverstone Circuit",
    country: "United Kingdom",
    flag: "🇬🇧",
    length: 5.891,
    corners: 18,
    drsZones: 2,
  },
  {
    id: "hungary",
    name: "Hungaroring",
    country: "Hungary",
    flag: "🇭🇺",
    length: 4.381,
    corners: 14,
    drsZones: 1,
  },
  {
    id: "belgium",
    name: "Circuit de Spa-Francorchamps",
    country: "Belgium",
    flag: "🇧🇪",
    length: 7.004,
    corners: 19,
    drsZones: 2,
  },
  {
    id: "netherlands",
    name: "Circuit Zandvoort",
    country: "Netherlands",
    flag: "🇳🇱",
    length: 4.259,
    corners: 14,
    drsZones: 3,
  },
  {
    id: "italy",
    name: "Autodromo Nazionale Monza",
    country: "Italy",
    flag: "🇮🇹",
    length: 5.793,
    corners: 11,
    drsZones: 3,
  },
  {
    id: "singapore",
    name: "Marina Bay Street Circuit",
    country: "Singapore",
    flag: "🇸🇬",
    length: 5.063,
    corners: 23,
    drsZones: 3,
  },
  {
    id: "japan",
    name: "Suzuka International Racing Course",
    country: "Japan",
    flag: "🇯🇵",
    length: 5.807,
    corners: 18,
    drsZones: 2,
  },
  {
    id: "qatar",
    name: "Lusail International Circuit",
    country: "Qatar",
    flag: "🇶🇦",
    length: 5.419,
    corners: 16,
    drsZones: 3,
  },
  {
    id: "usa",
    name: "Circuit of the Americas",
    country: "United States",
    flag: "🇺🇸",
    length: 5.513,
    corners: 20,
    drsZones: 2,
  },
  {
    id: "mexico",
    name: "Autódromo Hermanos Rodríguez",
    country: "Mexico",
    flag: "🇲🇽",
    length: 4.304,
    corners: 17,
    drsZones: 3,
  },
  {
    id: "brazil",
    name: "Autódromo José Carlos Pace",
    country: "Brazil",
    flag: "🇧🇷",
    length: 4.309,
    corners: 15,
    drsZones: 2,
  },
  {
    id: "abu_dhabi",
    name: "Yas Marina Circuit",
    country: "UAE",
    flag: "🇦🇪",
    length: 5.281,
    corners: 16,
    drsZones: 2,
  },
  {
    id: "australia",
    name: "Albert Park Circuit",
    country: "Australia",
    flag: "🇦🇺",
    length: 5.278,
    corners: 16,
    drsZones: 3,
  },
  {
    id: "china",
    name: "Shanghai International Circuit",
    country: "China",
    flag: "🇨🇳",
    length: 5.451,
    corners: 16,
    drsZones: 2,
  },
  {
    id: "azerbaijan",
    name: "Baku City Circuit",
    country: "Azerbaijan",
    flag: "🇦🇿",
    length: 6.003,
    corners: 20,
    drsZones: 2,
  },
  {
    id: "miami",
    name: "Miami International Autodrome",
    country: "United States",
    flag: "🇺🇸",
    length: 5.412,
    corners: 19,
    drsZones: 3,
  },
  {
    id: "saudi_arabia",
    name: "Jeddah Corniche Circuit",
    country: "Saudi Arabia",
    flag: "🇸🇦",
    length: 6.174,
    corners: 27,
    drsZones: 3,
  },
  {
    id: "las_vegas",
    name: "Las Vegas Street Circuit",
    country: "United States",
    flag: "🇺🇸",
    length: 6.201,
    corners: 17,
    drsZones: 3,
  },
];

// ============================================================================
// F1 Driver Data
// ============================================================================

export interface F1Driver {
  id: string;
  name: string;
  team: string;
  color: string;
  nationality: string;
  number: number;
}

export const F1_DRIVERS: F1Driver[] = [
  {
    id: "VER",
    name: "Max Verstappen",
    team: "Red Bull Racing",
    color: "#3671C6",
    nationality: "🇳🇱",
    number: 1,
  },
  {
    id: "PER",
    name: "Sergio Pérez",
    team: "Red Bull Racing",
    color: "#3671C6",
    nationality: "🇲🇽",
    number: 11,
  },
  {
    id: "HAM",
    name: "Lewis Hamilton",
    team: "Mercedes",
    color: "#27F4D2",
    nationality: "🇬🇧",
    number: 44,
  },
  {
    id: "RUS",
    name: "George Russell",
    team: "Mercedes",
    color: "#27F4D2",
    nationality: "🇬🇧",
    number: 63,
  },
  {
    id: "LEC",
    name: "Charles Leclerc",
    team: "Ferrari",
    color: "#F91536",
    nationality: "🇲🇨",
    number: 16,
  },
  {
    id: "SAI",
    name: "Carlos Sainz",
    team: "Ferrari",
    color: "#F91536",
    nationality: "🇪🇸",
    number: 55,
  },
  {
    id: "NOR",
    name: "Lando Norris",
    team: "McLaren",
    color: "#FF8000",
    nationality: "🇬🇧",
    number: 4,
  },
  {
    id: "PIA",
    name: "Oscar Piastri",
    team: "McLaren",
    color: "#FF8000",
    nationality: "🇦🇺",
    number: 81,
  },
  {
    id: "ALO",
    name: "Fernando Alonso",
    team: "Aston Martin",
    color: "#229971",
    nationality: "🇪🇸",
    number: 14,
  },
  {
    id: "STR",
    name: "Lance Stroll",
    team: "Aston Martin",
    color: "#229971",
    nationality: "🇨🇦",
    number: 18,
  },
];

// ============================================================================
// API Client
// ============================================================================

class F1ApiError extends Error {
  constructor(
    public message: string,
    public status?: number,
    public validationErrors?: any
  ) {
    super(message);
    this.name = "F1ApiError";
  }
}

export class F1ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl =
      process.env.NEXT_PUBLIC_CLIENT_API_URL || "http://localhost:8000";
  }

  /**
   * Run undercut simulation
   */
  async simulate(request: SimulationRequest): Promise<SimulationResponse> {
    try {
      // Validate request
      const validatedRequest = SimulationRequestSchema.parse(request);

      const response = await fetch(`${this.baseUrl}/simulate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(validatedRequest),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new F1ApiError(
          `Simulation failed: ${errorText}`,
          response.status
        );
      }

      const data = await response.json();

      // Validate response
      return SimulationResponseSchema.parse(data);
    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new F1ApiError("Invalid request data", 400, error.errors);
      }
      throw error;
    }
  }

  /**
   * Check API health
   */
  async health(): Promise<{ status: string; version: string }> {
    const response = await fetch(`${this.baseUrl}/`);

    if (!response.ok) {
      throw new F1ApiError("API health check failed", response.status);
    }

    return response.json();
  }
}

// Singleton instance
export const f1Api = new F1ApiClient();

// ============================================================================
// React Query Keys
// ============================================================================

export const queryKeys = {
  simulation: (request: SimulationRequest) => ["simulation", request],
  health: () => ["health"],
} as const;
