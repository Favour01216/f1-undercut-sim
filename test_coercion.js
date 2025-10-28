/**
 * Test the updated Zod schema with coercion
 */
const { z } = require("zod");

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

// Updated schema with coercion
const SimulationRequestSchema = z.object({
  gp: z.enum(GP_CHOICES),
  year: z.coerce.number().int().min(2020).max(2024),
  driver_a: z.string().min(1).max(50),
  driver_b: z.string().min(1).max(50),
  compound_a: z.enum(COMPOUND_CHOICES),
  lap_now: z.coerce.number().int().min(1).max(100),
  samples: z.coerce.number().int().min(1).max(10000),
  H: z.coerce.number().int().min(1).max(5),
  p_pit_next: z.coerce.number().min(0).max(1),
});

// Test data with strings (as might come from form)
const formData = {
  gp: "monza",
  year: "2024",
  driver_a: "VER",
  driver_b: "LEC",
  compound_a: "SOFT",
  lap_now: "25",
  samples: "1000",
  H: "2",
  p_pit_next: "1.0",
};

console.log("🧪 Testing updated schema with coercion...");
console.log("Input data:", JSON.stringify(formData, null, 2));

try {
  const validated = SimulationRequestSchema.parse(formData);
  console.log("✅ Validation passed with coercion!");
  console.log("Output data:", JSON.stringify(validated, null, 2));
} catch (error) {
  console.error("❌ Validation failed:", JSON.stringify(error.errors, null, 2));
}
