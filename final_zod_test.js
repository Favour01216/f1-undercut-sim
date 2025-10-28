/**
 * Final comprehensive test of the frontend Zod schema
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

// Schema WITH coercion (what should be deployed)
const SimulationRequestSchemaWithCoercion = z.object({
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

// Schema WITHOUT coercion (old broken version)
const SimulationRequestSchemaWithoutCoercion = z.object({
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

// Test data - what the form actually sends
const formData = {
  gp: "monza",
  year: "2024", // STRING from form
  driver_a: "VER",
  driver_b: "LEC",
  compound_a: "SOFT",
  lap_now: "25", // STRING from form
  samples: "1000", // STRING from form
  H: "2", // STRING from form
  p_pit_next: "1.0", // STRING from form
};

console.log("=".repeat(70));
console.log("🏎️  F1 UNDERCUT SIMULATOR - ZOD VALIDATION TEST");
console.log("=".repeat(70));

console.log("\n📝 Form Data (what React Hook Form sends):");
console.log(JSON.stringify(formData, null, 2));

console.log("\n\n🧪 TEST 1: Schema WITHOUT coercion (OLD - BROKEN)");
console.log("-".repeat(70));
try {
  const result = SimulationRequestSchemaWithoutCoercion.parse(formData);
  console.log("✅ PASSED (unexpected!)");
} catch (error) {
  console.log("❌ FAILED (expected)");
  if (error.errors && error.errors.length > 0) {
    console.log("Error:", error.errors[0].message);
    console.log("Path:", error.errors[0].path.join("."));
  } else {
    console.log("Error:", error.message);
  }
}

console.log("\n\n🧪 TEST 2: Schema WITH coercion (NEW - FIXED)");
console.log("-".repeat(70));
try {
  const result = SimulationRequestSchemaWithCoercion.parse(formData);
  console.log("✅ PASSED - Validation successful!");
  console.log("\n📤 Validated data (ready to send to backend):");
  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  console.log("❌ FAILED (unexpected!)");
  console.log("Error:", error.errors);
}

console.log("\n" + "=".repeat(70));
console.log("🏁 TEST COMPLETE");
console.log("=".repeat(70));
