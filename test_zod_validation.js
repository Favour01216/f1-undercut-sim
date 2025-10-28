/**
 * Test Zod validation with the exact same data structure
 */
const { z } = require("zod");

// Copy the exact schema from frontend
const GP_CHOICES = [
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
];

const COMPOUND_CHOICES = ["SOFT", "MEDIUM", "HARD"];

const SimulationRequestSchema = z.object({
  gp: z.enum(GP_CHOICES),
  year: z.number().int().min(2020).max(2024),
  driver_a: z.string().min(1).max(50),
  driver_b: z.string().min(1).max(50),
  compound_a: z.enum(COMPOUND_CHOICES),
  lap_now: z.number().int().min(1).max(100),
  samples: z.number().int().min(1).max(10000).default(1000),
  H: z.number().int().min(1).max(5).default(2),
  p_pit_next: z.number().min(0).max(1).default(1.0),
});

// Test data exactly as form would send it
const testData = {
  gp: "monza",
  year: 2024,
  driver_a: "VER",
  driver_b: "LEC",
  compound_a: "SOFT",
  lap_now: 25,
  samples: 1000,
  H: 2,
  p_pit_next: 1.0,
};

console.log("🧪 Testing Zod validation...");
console.log("Test data:", JSON.stringify(testData, null, 2));

try {
  const validated = SimulationRequestSchema.parse(testData);
  console.log("✅ Zod validation passed!");
  console.log("Validated data:", JSON.stringify(validated, null, 2));
} catch (error) {
  console.error("❌ Zod validation failed!");
  console.error("Error:", error.errors || error.message);
}
