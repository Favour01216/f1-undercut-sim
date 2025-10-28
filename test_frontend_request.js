/**
 * Test script to simulate the exact request the frontend makes
 */

// Simulate the exact data structure that the frontend form would send
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

console.log("🏎️ Testing frontend request format...");
console.log("Data to send:", JSON.stringify(testData, null, 2));

fetch("https://f1-strategy-lab.onrender.com/simulate", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify(testData),
})
  .then((response) => {
    console.log("Response status:", response.status);
    return response.json();
  })
  .then((data) => {
    console.log("✅ Backend response:", JSON.stringify(data, null, 2));
  })
  .catch((error) => {
    console.error("❌ Request failed:", error);
  });
