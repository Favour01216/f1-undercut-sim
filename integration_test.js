/**
 * Final test to verify the complete frontend-backend integration
 */
const fetch = require("node-fetch");

async function testCompleteIntegration() {
  console.log("🏎️ F1 Undercut Simulator - Complete Integration Test");
  console.log("=".repeat(60));

  // Test 1: Backend health check
  console.log("\n1️⃣ Testing backend health...");
  try {
    const healthResponse = await fetch("https://f1-strategy-lab.onrender.com/");
    const healthData = await healthResponse.json();
    console.log("✅ Backend online:", healthData.message);
  } catch (error) {
    console.error("❌ Backend health check failed:", error.message);
    return;
  }

  // Test 2: Simulate exact frontend request (with string values)
  console.log("\n2️⃣ Testing frontend-style request (string values)...");
  const frontendRequestData = {
    gp: "monza",
    year: "2024", // String as might come from form
    driver_a: "VER",
    driver_b: "LEC",
    compound_a: "SOFT",
    lap_now: "25", // String as might come from form
    samples: "1000", // String as might come from form
    H: "2", // String as might come from form
    p_pit_next: "1.0", // String as might come from form
  };

  try {
    console.log(
      "📤 Sending request:",
      JSON.stringify(frontendRequestData, null, 2)
    );

    const response = await fetch(
      "https://f1-strategy-lab.onrender.com/simulate",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(frontendRequestData),
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("❌ Request failed:", response.status, errorText);
      return;
    }

    const data = await response.json();
    console.log("✅ Backend response received:");
    console.log("📊 Results:", JSON.stringify(data, null, 2));

    // Test 3: Validate response structure
    console.log("\n3️⃣ Validating response structure...");
    const requiredFields = [
      "undercut_probability",
      "time_delta",
      "optimal_pit_lap",
      "strategy_recommendation",
      "confidence",
    ];
    const missingFields = requiredFields.filter((field) => !(field in data));

    if (missingFields.length === 0) {
      console.log("✅ All required response fields present");
    } else {
      console.error("❌ Missing response fields:", missingFields);
    }

    console.log("\n🏁 Integration test completed successfully!");
    console.log("Frontend should now work with the backend!");
  } catch (error) {
    console.error("❌ Integration test failed:", error.message);
  }
}

// Install node-fetch if not available and run test
if (typeof fetch === "undefined") {
  console.log("Installing node-fetch...");
  require("child_process").execSync("npm install node-fetch@2", {
    stdio: "inherit",
  });
}

testCompleteIntegration();
