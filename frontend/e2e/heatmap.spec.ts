import { test, expect } from "@playwright/test";

test.describe("Heatmap Functionality", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("triggers heatmap generation and verifies Plotly trace exists", async ({
    page,
  }) => {
    let heatmapRequests = 0;

    // Mock the /simulate API for both single simulation and heatmap generation
    await page.route("**/simulate", async (route) => {
      heatmapRequests++;
      const json = {
        p_undercut: 0.45 + Math.random() * 0.3, // Random probability between 0.45-0.75
        pitLoss_s: 24.0 + Math.random() * 2, // Random pit loss 24-26s
        outLapDelta_s: 0.8 + Math.random() * 0.4, // Random outlap 0.8-1.2s
        assumptions: {
          gap_s: 5.0,
          tyre_age_b: 15,
          degradation_model: "quadratic",
          pit_model: "normal_distribution",
          outlap_model: "compound_specific",
        },
      };
      await route.fulfill({ json });
    });

    // First, run a single simulation to enable heatmap
    await page
      .getByRole("button", { name: /run undercut simulation/i })
      .click();

    // Wait for initial simulation to complete
    await expect(page.getByText(/\d+\.\d+%/)).toBeVisible({ timeout: 10000 });

    // Check that heatmap section is now visible
    await expect(page.getByText("Gap-Compound Analysis")).toBeVisible();

    // Wait for heatmap generation to start (should see loading state)
    await expect(page.getByText("Generating heatmap data...")).toBeVisible({
      timeout: 5000,
    });

    // Wait for heatmap to complete (this may take a while as it runs multiple simulations)
    await expect(page.getByText("Generating heatmap data...")).not.toBeVisible({
      timeout: 60000,
    });

    // Verify that Plotly chart is rendered
    await expect(page.locator(".js-plotly-plot")).toBeVisible({
      timeout: 10000,
    });

    // Verify the plot has data (look for plot traces)
    const plotExists = await page
      .locator(".js-plotly-plot .plot-container")
      .count();
    expect(plotExists).toBeGreaterThan(0);

    // Verify heatmap title is present
    await expect(
      page.getByText(/undercut success probability.*bahrain.*2024/i)
    ).toBeVisible();

    // Verify summary statistics cards are rendered
    await expect(page.getByText("High Success Scenarios")).toBeVisible();
    await expect(page.getByText("Average Success Rate")).toBeVisible();
    await expect(page.getByText("Best Compound")).toBeVisible();

    // Verify accessibility instructions are present
    await expect(page.getByText("Accessibility Instructions:")).toBeVisible();
    await expect(
      page.getByText("Use Tab to navigate through interactive elements")
    ).toBeVisible();

    // Verify multiple simulation requests were made for heatmap generation
    expect(heatmapRequests).toBeGreaterThan(10); // Should be ~48 requests (16 gaps × 3 compounds)
  });

  test("shows loading skeleton during heatmap generation", async ({ page }) => {
    // Mock slow API responses for heatmap generation
    await page.route("**/simulate", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 100)); // Small delay
      const json = {
        p_undercut: 0.5,
        pitLoss_s: 25.0,
        outLapDelta_s: 1.0,
        assumptions: { gap_s: 5.0, tyre_age_b: 15 },
      };
      await route.fulfill({ json });
    });

    // Run initial simulation
    await page
      .getByRole("button", { name: /run undercut simulation/i })
      .click();
    await expect(page.getByText(/\d+\.\d+%/)).toBeVisible();

    // Check that loading skeleton appears for heatmap
    await expect(page.getByText("Generating heatmap data...")).toBeVisible();
    await expect(
      page.getByText(/running simulations across.*gaps.*compounds/i)
    ).toBeVisible();

    // Verify skeleton loader structure
    await expect(
      page.locator('[role="status"][aria-label="Heatmap loading"]')
    ).toBeVisible();
  });

  test("handles heatmap generation error gracefully", async ({ page }) => {
    let requestCount = 0;

    // Mock API - first request succeeds, subsequent ones fail
    await page.route("**/simulate", async (route) => {
      requestCount++;
      if (requestCount === 1) {
        // First simulation succeeds
        const json = {
          p_undercut: 0.6,
          pitLoss_s: 24.5,
          outLapDelta_s: 1.1,
          assumptions: { gap_s: 5.0, tyre_age_b: 15 },
        };
        await route.fulfill({ json });
      } else {
        // Heatmap generation fails
        await route.fulfill({ status: 500, body: "Server error" });
      }
    });

    // Run initial simulation
    await page
      .getByRole("button", { name: /run undercut simulation/i })
      .click();
    await expect(page.getByText("60.0%")).toBeVisible();

    // Wait for heatmap error state
    await expect(page.getByText("Heatmap Generation Failed")).toBeVisible({
      timeout: 30000,
    });
    await expect(
      page.getByRole("button", { name: /retry heatmap generation/i })
    ).toBeVisible();

    // Test retry functionality
    await page
      .getByRole("button", { name: /retry heatmap generation/i })
      .click();
    await expect(page.getByText("Generating heatmap data...")).toBeVisible();
  });

  test("heatmap empty state when no base simulation", async ({ page }) => {
    // Check heatmap section shows empty state initially
    await expect(page.getByText("Gap-Compound Analysis")).toBeVisible();
    await expect(page.getByText("No heatmap data available")).toBeVisible();
    await expect(
      page.getByText("Run a simulation first to generate the heatmap analysis")
    ).toBeVisible();
  });

  test("heatmap interaction and tooltip functionality", async ({ page }) => {
    // Mock API for heatmap generation
    await page.route("**/simulate", async (route) => {
      const json = {
        p_undercut: 0.6,
        pitLoss_s: 24.5,
        outLapDelta_s: 1.1,
        assumptions: { gap_s: 5.0, tyre_age_b: 15 },
      };
      await route.fulfill({ json });
    });

    // Run simulation and wait for heatmap
    await page
      .getByRole("button", { name: /run undercut simulation/i })
      .click();
    await expect(page.getByText("60.0%")).toBeVisible();

    // Wait for heatmap to load
    await expect(page.locator(".js-plotly-plot")).toBeVisible({
      timeout: 60000,
    });

    // Try to hover over heatmap (this tests that the interactive elements are present)
    const plotContainer = page.locator(".js-plotly-plot");
    await plotContainer.hover();

    // Verify plot toolbar is present (indicates interactive functionality)
    await expect(page.locator(".modebar")).toBeVisible({ timeout: 5000 });

    // Verify that the chart has proper accessibility attributes
    await expect(plotContainer).toHaveAttribute("role", "img");
  });
});
