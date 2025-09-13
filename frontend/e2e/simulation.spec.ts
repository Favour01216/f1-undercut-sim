import { test, expect } from "@playwright/test";

test.describe("Simulation Functionality", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("mocks /simulate API and verifies ResultCards render probability and stats", async ({
    page,
  }) => {
    // Mock the /simulate API endpoint
    await page.route("**/simulate", async (route) => {
      const json = {
        p_undercut: 0.75,
        pitLoss_s: 24.5,
        outLapDelta_s: 1.2,
        assumptions: {
          gap_s: 5.0,
          tyre_age_b: 15,
          degradation_model: "quadratic",
          pit_model: "normal_distribution",
          outlap_model: "compound_specific",
        },
        avgMargin_s: 2.3,
      };
      await route.fulfill({ json });
    });

    // Fill out the form with test data
    await page
      .getByRole("combobox", { name: /select grand prix circuit/i })
      .click();
    await page.getByRole("option", { name: /bahrain/i }).click();

    await page
      .getByRole("combobox", { name: /select driver attempting undercut/i })
      .click();
    await page.getByRole("option", { name: /verstappen/i }).click();

    await page.getByRole("combobox", { name: /select target driver/i }).click();
    await page.getByRole("option", { name: /hamilton/i }).click();

    await page
      .getByRole("combobox", { name: /select new tire compound/i })
      .click();
    await page.getByRole("option", { name: /soft/i }).click();

    // Submit the form
    await page
      .getByRole("button", { name: /run undercut simulation/i })
      .click();

    // Wait for the simulation to complete and results to appear
    await expect(page.getByText("Simulation Results")).toBeVisible();

    // Verify the probability card shows mocked data
    await expect(page.getByText("75.0%")).toBeVisible();
    await expect(page.getByText("Likely Success")).toBeVisible();

    // Verify individual stat cards
    await expect(page.getByText("24.50s")).toBeVisible(); // Pit Loss
    await expect(page.getByText("1.20s")).toBeVisible(); // Outlap Delta

    // Verify success likelihood banner
    await expect(page.getByText("Likely Success")).toBeVisible();
    await expect(
      page.getByText(/based on.*monte carlo simulations/i)
    ).toBeVisible();

    // Verify assumptions section
    await expect(page.getByText("Simulation Assumptions")).toBeVisible();
    await expect(page.getByText("5.00s")).toBeVisible(); // Current Gap
    await expect(page.getByText("15 laps")).toBeVisible(); // Tire Age

    // Verify last updated timestamp appears
    await expect(page.getByText(/last updated:/i)).toBeVisible();

    // Verify toast notification for successful simulation
    await expect(page.getByText("Simulation Complete")).toBeVisible();
    await expect(
      page.getByText(/successfully analyzed.*vs.*undercut scenario/i)
    ).toBeVisible();
  });

  test("handles simulation error gracefully", async ({ page }) => {
    // Mock API error response
    await page.route("**/simulate", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Internal server error during simulation",
        }),
      });
    });

    // Submit the form
    await page
      .getByRole("button", { name: /run undercut simulation/i })
      .click();

    // Wait for error toast to appear
    await expect(page.getByText("Simulation Failed")).toBeVisible();
    await expect(
      page.getByText(/internal server error during simulation/i)
    ).toBeVisible();

    // Verify results section shows appropriate error state
    await expect(page.getByText(/simulation error/i)).toBeVisible();
  });

  test("displays loading states during simulation", async ({ page }) => {
    // Mock slow API response
    await page.route("**/simulate", async (route) => {
      // Delay response by 2 seconds
      await new Promise((resolve) => setTimeout(resolve, 2000));
      const json = {
        p_undercut: 0.5,
        pitLoss_s: 25.0,
        outLapDelta_s: 1.0,
        assumptions: {},
      };
      await route.fulfill({ json });
    });

    // Submit the form
    await page
      .getByRole("button", { name: /run undercut simulation/i })
      .click();

    // Verify loading states
    await expect(page.getByText("Running Simulation...")).toBeVisible();
    await expect(
      page.getByText("Running Monte Carlo simulation...")
    ).toBeVisible();

    // Verify loading skeletons appear
    await expect(page.locator('[aria-label*="loading"]')).toHaveCount(4, {
      timeout: 1000,
    }); // 4 stat cards

    // Wait for completion
    await expect(page.getByText("Running Simulation...")).not.toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText(/50\.0%/)).toBeVisible();
  });

  test("session history functionality works", async ({ page }) => {
    // Mock successful simulation
    await page.route("**/simulate", async (route) => {
      const json = {
        p_undercut: 0.65,
        pitLoss_s: 23.8,
        outLapDelta_s: 0.9,
        assumptions: { gap_s: 4.2, tyre_age_b: 12 },
      };
      await route.fulfill({ json });
    });

    // Run first simulation
    await page
      .getByRole("button", { name: /run undercut simulation/i })
      .click();
    await expect(page.getByText("65.0%")).toBeVisible();

    // Check that history table appears
    await expect(page.getByText("Simulation History")).toBeVisible();
    await expect(page.getByText(/1 recent simulation/)).toBeVisible();

    // Verify history table content
    await expect(page.getByText("VER")).toBeVisible(); // Default driver A
    await expect(page.getByText("HAM")).toBeVisible(); // Default driver B
    await expect(page.getByText("BAHRAIN 2024")).toBeVisible(); // Default race

    // Test copy functionality
    await page
      .getByRole("button", { name: /copy simulation results/i })
      .first()
      .click();

    // Test delete functionality
    await page
      .getByRole("button", { name: /remove from history/i })
      .first()
      .click();
    await expect(page.getByText("Simulation History")).not.toBeVisible();
  });
});
