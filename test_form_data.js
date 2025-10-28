/**
 * Test to simulate what React Hook Form might be doing to the data
 */

// Simulate form data that might come from HTML inputs
const formData = {
  gp: "monza", // string
  year: "2024", // might be string from form
  driver_a: "VER", // string
  driver_b: "LEC", // string
  compound_a: "SOFT", // string
  lap_now: "25", // might be string from form
  samples: "1000", // might be string from form
  H: "2", // might be string from form
  p_pit_next: "1.0", // might be string from form
};

// Convert to expected types (what valueAsNumber should do)
const convertedData = {
  gp: formData.gp,
  year: parseInt(formData.year),
  driver_a: formData.driver_a,
  driver_b: formData.driver_b,
  compound_a: formData.compound_a,
  lap_now: parseInt(formData.lap_now),
  samples: parseInt(formData.samples),
  H: parseInt(formData.H),
  p_pit_next: parseFloat(formData.p_pit_next),
};

console.log("📝 Form data (strings):", JSON.stringify(formData, null, 2));
console.log(
  "🔄 Converted data (numbers):",
  JSON.stringify(convertedData, null, 2)
);

// Test both versions
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

const SimulationRequestSchema = z.object({
  gp: z.enum(GP_CHOICES),
  year: z.number().int().min(2020).max(2024),
  driver_a: z.string().min(1).max(50),
  driver_b: z.string().min(1).max(50),
  compound_a: z.enum(COMPOUND_CHOICES),
  lap_now: z.number().int().min(1).max(100),
  samples: z.number().int().min(1).max(10000),
  H: z.number().int().min(1).max(5),
  p_pit_next: z.number().min(0).max(1),
});

console.log("\n🧪 Testing string form data...");
try {
  const validated = SimulationRequestSchema.parse(formData);
  console.log("✅ String data validation passed");
} catch (error) {
  console.error(
    "❌ String data validation failed:",
    JSON.stringify(error.errors || error.message, null, 2)
  );
}

console.log("\n🧪 Testing converted data...");
try {
  const validated = SimulationRequestSchema.parse(convertedData);
  console.log("✅ Converted data validation passed");
} catch (error) {
  console.error(
    "❌ Converted data validation failed:",
    JSON.stringify(error.errors || error.message, null, 2)
  );
}
