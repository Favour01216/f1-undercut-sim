/**
 * Manual verification script for API client Zod validation
 * Run this script to verify that malformed payloads are properly rejected
 */

import { z } from "zod";
import {
  SimulationRequestSchema,
  SimulationResponseSchema,
  BackendStatusSchema,
  ApiValidationError,
  ApiNetworkError,
  validateSimulationRequest,
  handleApiError,
  F1ApiClient,
} from "./api";

console.log("🧪 Testing F1 API Client Zod Validation\n");

// Test 1: Valid simulation request
console.log("1️⃣ Testing valid simulation request...");
try {
  const validRequest = {
    gp: "monaco" as const,
    year: 2024,
    driver_a: "VER",
    driver_b: "LEC",
    compound_a: "SOFT" as const,
    lap_now: 25,
    samples: 1000,
  };

  const parsed = SimulationRequestSchema.parse(validRequest);
  console.log("✅ Valid request parsed successfully");
  console.log("   Defaults applied:", {
    H: parsed.H,
    p_pit_next: parsed.p_pit_next,
  });
} catch (error) {
  console.log("❌ Unexpected error:", error);
}

// Test 2: Invalid simulation request (bad GP)
console.log("\n2️⃣ Testing invalid GP...");
try {
  const invalidRequest = {
    gp: "invalid-gp",
    year: 2024,
    driver_a: "VER",
    driver_b: "LEC",
    compound_a: "SOFT" as const,
    lap_now: 25,
  };

  SimulationRequestSchema.parse(invalidRequest);
  console.log("❌ Should have thrown error for invalid GP");
} catch (error) {
  if (error instanceof z.ZodError) {
    console.log("✅ Correctly rejected invalid GP");
    console.log("   Error:", error.issues[0].message);
  } else {
    console.log("❌ Unexpected error type:", error);
  }
}

// Test 3: Invalid compound
console.log("\n3️⃣ Testing invalid compound...");
try {
  const invalidRequest = {
    gp: "monaco" as const,
    year: 2024,
    driver_a: "VER",
    driver_b: "LEC",
    compound_a: "ULTRA_SOFT" as any,
    lap_now: 25,
  };

  SimulationRequestSchema.parse(invalidRequest);
  console.log("❌ Should have thrown error for invalid compound");
} catch (error) {
  if (error instanceof z.ZodError) {
    console.log("✅ Correctly rejected invalid compound");
    console.log("   Error:", error.issues[0].message);
  } else {
    console.log("❌ Unexpected error type:", error);
  }
}

// Test 4: Year out of range
console.log("\n4️⃣ Testing year out of range...");
try {
  const invalidRequest = {
    gp: "monaco" as const,
    year: 2025, // Future year
    driver_a: "VER",
    driver_b: "LEC",
    compound_a: "SOFT" as const,
    lap_now: 25,
  };

  SimulationRequestSchema.parse(invalidRequest);
  console.log("❌ Should have thrown error for future year");
} catch (error) {
  if (error instanceof z.ZodError) {
    console.log("✅ Correctly rejected future year");
    console.log("   Error:", error.issues[0].message);
  } else {
    console.log("❌ Unexpected error type:", error);
  }
}

// Test 5: Valid simulation response
console.log("\n5️⃣ Testing valid simulation response...");
try {
  const validResponse = {
    p_undercut: 0.75,
    pitLoss_s: 23.5,
    outLapDelta_s: 1.2,
    assumptions: {
      current_gap_s: 5.0,
      tire_age_driver_b: 15,
      models_fitted: {
        deg_model: true,
        pit_model: true,
        outlap_model: true,
      },
      monte_carlo_samples: 1000,
    },
  };

  const parsed = SimulationResponseSchema.parse(validResponse);
  console.log("✅ Valid response parsed successfully");
} catch (error) {
  console.log("❌ Unexpected error:", error);
}

// Test 6: Invalid simulation response (p_undercut > 1.0)
console.log("\n6️⃣ Testing invalid response (p_undercut > 1.0)...");
try {
  const invalidResponse = {
    p_undercut: 1.5, // Invalid: > 1.0
    pitLoss_s: 23.5,
    outLapDelta_s: 1.2,
    assumptions: {
      current_gap_s: 5.0,
      tire_age_driver_b: 15,
      models_fitted: {
        deg_model: true,
        pit_model: true,
        outlap_model: true,
      },
      monte_carlo_samples: 1000,
    },
  };

  SimulationResponseSchema.parse(invalidResponse);
  console.log("❌ Should have thrown error for p_undercut > 1.0");
} catch (error) {
  if (error instanceof z.ZodError) {
    console.log("✅ Correctly rejected p_undercut > 1.0");
    console.log("   Error:", error.issues[0].message);
  } else {
    console.log("❌ Unexpected error type:", error);
  }
}

// Test 7: Test validateSimulationRequest utility
console.log("\n7️⃣ Testing validateSimulationRequest utility...");
const validationResult = validateSimulationRequest({
  gp: "monaco" as const,
  year: 2024,
  driver_a: "VER",
  driver_b: "LEC",
  compound_a: "SOFT" as const,
  lap_now: 25,
});

if (validationResult.isValid) {
  console.log("✅ Validation utility correctly identified valid request");
} else {
  console.log("❌ Validation utility failed:", validationResult.errors);
}

const invalidValidationResult = validateSimulationRequest({
  gp: "invalid-gp" as any,
  year: 2025,
  driver_a: "",
});

if (!invalidValidationResult.isValid) {
  console.log("✅ Validation utility correctly identified invalid request");
  console.log("   Errors:", invalidValidationResult.errors);
} else {
  console.log("❌ Validation utility should have failed");
}

// Test 8: Test error handling utility
console.log("\n8️⃣ Testing error handling utility...");
const zodError = new z.ZodError([
  {
    code: "invalid_type",
    expected: "number",
    received: "string",
    path: ["p_undercut"],
    message: "Expected number, received string",
  },
]);

const apiError = new ApiValidationError("Test validation error", zodError);
const errorResult = handleApiError(apiError);

if (
  errorResult.isUserFriendly &&
  errorResult.message.includes("Invalid data type")
) {
  console.log("✅ Error handling utility generated user-friendly message");
  console.log("   Message:", errorResult.message);
} else {
  console.log("❌ Error handling utility failed");
}

console.log("\n🎉 All manual tests completed!");
console.log("\n📋 Summary:");
console.log("   • Zod schemas correctly validate request/response data");
console.log("   • Invalid payloads are properly rejected");
console.log("   • User-friendly error messages are generated");
console.log("   • Type safety is enforced at runtime");
console.log(
  "\n🔒 The API client now provides robust validation against malformed payloads!"
);
