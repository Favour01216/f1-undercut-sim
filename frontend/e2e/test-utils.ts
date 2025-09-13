import { Page, expect } from "@playwright/test";

/**
 * Test utilities for F1 Strategy Dashboard E2E tests
 */

export interface MockSimulationResponse {
  p_undercut: number;
  pitLoss_s: number;
  outLapDelta_s: number;
  assumptions?: {
    gap_s: number;
    tyre_age_b: number;
    degradation_model: string;
    pit_model: string;
    outlap_model: string;
  };
  avgMargin_s?: number;
}

export interface MockBackendStatusResponse {
  message: string;
  version: string;
  health: string;
  docs?: string;
  simulate?: string;
}

/**
 * Mock a successful backend status response
 */
export async function mockBackendConnected(page: Page, version = "0.2.0") {
  await page.route("**/api/v1/**", async (route) => {
    const json: MockBackendStatusResponse = {
      message: "F1 Undercut Simulator API",
      version,
      health: "healthy",
      docs: "/docs",
      simulate: "/simulate",
    };
    await route.fulfill({ json });
  });

  await page.route("**/", async (route) => {
    const json: MockBackendStatusResponse = {
      message: "F1 Undercut Simulator API",
      version,
      health: "healthy",
      docs: "/docs",
      simulate: "/simulate",
    };
    await route.fulfill({ json });
  });
}

/**
 * Mock a backend disconnection (all requests fail)
 */
export async function mockBackendDisconnected(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    await route.abort("failed");
  });

  await page.route("**/", async (route) => {
    await route.abort("failed");
  });
}

/**
 * Mock a successful simulation response
 */
export async function mockSuccessfulSimulation(
  page: Page,
  response: MockSimulationResponse
) {
  await page.route("**/simulate", async (route) => {
    const json: MockSimulationResponse = {
      assumptions: {
        gap_s: 5.0,
        tyre_age_b: 15,
        degradation_model: "quadratic",
        pit_model: "normal_distribution",
        outlap_model: "compound_specific",
      },
      ...response,
    };
    await route.fulfill({ json });
  });
}

/**
 * Mock a failed simulation response
 */
export async function mockFailedSimulation(
  page: Page,
  errorMessage = "Simulation failed",
  statusCode = 500
) {
  await page.route("**/simulate", async (route) => {
    await route.fulfill({
      status: statusCode,
      contentType: "application/json",
      body: JSON.stringify({ detail: errorMessage }),
    });
  });
}

/**
 * Fill out the simulation form with test data
 */
export async function fillSimulationForm(
  page: Page,
  options: {
    gp?: string;
    year?: string;
    driverA?: string;
    driverB?: string;
    compound?: string;
    lap?: string;
    samples?: string;
    gap?: string;
  } = {}
) {
  const {
    gp = "bahrain",
    year = "2024",
    driverA = "verstappen",
    driverB = "hamilton",
    compound = "soft",
    lap = "25",
    samples = "1000",
    gap = "5.0",
  } = options;

  // Fill Grand Prix
  if (gp !== "bahrain") {
    // Skip if already default
    await page
      .getByRole("combobox", { name: /select grand prix circuit/i })
      .click();
    await page.getByRole("option", { name: new RegExp(gp, "i") }).click();
  }

  // Fill Year
  if (year !== "2024") {
    // Skip if already default
    await page
      .getByRole("combobox", { name: /select racing season year/i })
      .click();
    await page.getByRole("option", { name: year }).click();
  }

  // Fill Driver A
  if (driverA !== "verstappen") {
    // Skip if already default
    await page
      .getByRole("combobox", { name: /select driver attempting undercut/i })
      .click();
    await page.getByRole("option", { name: new RegExp(driverA, "i") }).click();
  }

  // Fill Driver B
  if (driverB !== "hamilton") {
    // Skip if already default
    await page.getByRole("combobox", { name: /select target driver/i }).click();
    await page.getByRole("option", { name: new RegExp(driverB, "i") }).click();
  }

  // Fill Compound
  if (compound !== "soft") {
    // Skip if already default
    await page
      .getByRole("combobox", { name: /select new tire compound/i })
      .click();
    await page.getByRole("option", { name: new RegExp(compound, "i") }).click();
  }

  // Fill Lap
  if (lap !== "25") {
    // Skip if already default
    await page
      .getByRole("spinbutton", { name: /current lap number/i })
      .fill(lap);
  }

  // Fill Samples
  if (samples !== "1000") {
    // Skip if already default
    await page
      .getByRole("spinbutton", { name: /monte carlo samples/i })
      .fill(samples);
  }

  // Fill Gap
  if (gap !== "5.0") {
    // Skip if already default
    await page
      .getByRole("spinbutton", { name: /current gap to driver b/i })
      .fill(gap);
  }
}

/**
 * Submit the simulation form and wait for completion
 */
export async function submitSimulation(page: Page, timeout = 10000) {
  await page.getByRole("button", { name: /run undercut simulation/i }).click();

  // Wait for either success or error state
  await expect.soft(page.getByText(/\d+\.\d+%/)).toBeVisible({ timeout });
}

/**
 * Wait for heatmap to be generated
 */
export async function waitForHeatmap(page: Page, timeout = 60000) {
  // Wait for heatmap generation to complete
  await expect(page.getByText("Generating heatmap data...")).not.toBeVisible({
    timeout,
  });
  await expect(page.locator(".js-plotly-plot")).toBeVisible({ timeout });
}

/**
 * Check accessibility of an element
 */
export async function checkAccessibility(page: Page, selector: string) {
  const element = page.locator(selector);

  // Check that element has proper ARIA attributes
  const hasAriaLabel = await element.getAttribute("aria-label");
  const hasAriaLabelledby = await element.getAttribute("aria-labelledby");
  const hasAriaDescribedby = await element.getAttribute("aria-describedby");
  const hasRole = await element.getAttribute("role");

  // At least one accessibility attribute should be present
  expect(
    hasAriaLabel || hasAriaLabelledby || hasAriaDescribedby || hasRole
  ).toBeTruthy();
}

/**
 * Wait for toast notification to appear
 */
export async function waitForToast(
  page: Page,
  message: string,
  timeout = 5000
) {
  await expect(page.getByText(message)).toBeVisible({ timeout });
}

/**
 * Dismiss toast notification
 */
export async function dismissToast(page: Page, message: string) {
  const toast = page
    .getByText(message)
    .locator("..")
    .locator('button[aria-label="Close notification"]');
  if (await toast.isVisible()) {
    await toast.click();
  }
}

/**
 * Generate multiple heatmap simulation responses
 */
export function generateHeatmapMockData(): MockSimulationResponse[] {
  const responses: MockSimulationResponse[] = [];
  const gaps = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30];
  const compounds = ["SOFT", "MEDIUM", "HARD"];

  compounds.forEach((compound) => {
    gaps.forEach((gap) => {
      // Generate realistic probability based on gap (larger gaps = higher success)
      const baseProbability = Math.min(0.1 + gap * 0.025, 0.8);
      const compoundModifier =
        compound === "SOFT" ? 0.1 : compound === "MEDIUM" ? 0.05 : 0;
      const probability = Math.min(
        baseProbability + compoundModifier + Math.random() * 0.1,
        0.95
      );

      responses.push({
        p_undercut: probability,
        pitLoss_s: 24.0 + Math.random() * 2,
        outLapDelta_s: 0.8 + Math.random() * 0.4,
        assumptions: {
          gap_s: gap,
          tyre_age_b: 15,
          degradation_model: "quadratic",
          pit_model: "normal_distribution",
          outlap_model: "compound_specific",
        },
      });
    });
  });

  return responses;
}
