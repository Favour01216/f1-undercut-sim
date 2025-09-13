import { test, expect } from "@playwright/test";

test.describe("F1 Strategy Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the dashboard
    await page.goto("/");

    // Wait for the page to be fully loaded
    await page.waitForLoadState("networkidle");
  });

  test("loads dashboard and renders SimulationForm controls", async ({
    page,
  }) => {
    // Check main title is visible
    await expect(
      page.getByRole("heading", { name: /F1 Undercut Strategy Dashboard/i })
    ).toBeVisible();

    // Check that all form sections are present
    await expect(page.getByText("Race Configuration")).toBeVisible();
    await expect(page.getByText("Driver Selection")).toBeVisible();
    await expect(page.getByText("Race Situation Parameters")).toBeVisible();

    // Check form controls are rendered and accessible
    await expect(
      page.getByRole("combobox", { name: /select grand prix circuit/i })
    ).toBeVisible();
    await expect(
      page.getByRole("combobox", { name: /select racing season year/i })
    ).toBeVisible();
    await expect(
      page.getByRole("combobox", { name: /select driver attempting undercut/i })
    ).toBeVisible();
    await expect(
      page.getByRole("combobox", { name: /select target driver/i })
    ).toBeVisible();
    await expect(
      page.getByRole("combobox", { name: /select new tire compound/i })
    ).toBeVisible();

    // Check number inputs
    await expect(
      page.getByRole("spinbutton", { name: /current lap number/i })
    ).toBeVisible();
    await expect(
      page.getByRole("spinbutton", { name: /monte carlo samples/i })
    ).toBeVisible();
    await expect(
      page.getByRole("spinbutton", { name: /current gap to driver b/i })
    ).toBeVisible();

    // Check submit button
    await expect(
      page.getByRole("button", { name: /run undercut simulation/i })
    ).toBeVisible();

    // Verify default form values
    await expect(
      page.getByRole("combobox", { name: /select grand prix circuit/i })
    ).toHaveText("🇧🇭 Bahrain International Circuit");
    await expect(
      page.getByRole("spinbutton", { name: /current lap number/i })
    ).toHaveValue("25");
    await expect(
      page.getByRole("spinbutton", { name: /monte carlo samples/i })
    ).toHaveValue("1000");
  });

  test("keyboard navigation works correctly", async ({ page }) => {
    // Start navigation from first form element
    await page
      .getByRole("combobox", { name: /select grand prix circuit/i })
      .focus();

    // Tab through form controls and verify focus
    const tabOrder = [
      { name: /select grand prix circuit/i, role: "combobox" },
      { name: /select racing season year/i, role: "combobox" },
      { name: /select driver attempting undercut/i, role: "combobox" },
      { name: /select target driver/i, role: "combobox" },
      { name: /select new tire compound/i, role: "combobox" },
      { name: /current lap number/i, role: "spinbutton" },
      { name: /monte carlo samples/i, role: "spinbutton" },
      { name: /current gap to driver b/i, role: "spinbutton" },
      { name: /run undercut simulation/i, role: "button" },
    ];

    for (let i = 0; i < tabOrder.length; i++) {
      const element = page.getByRole(tabOrder[i].role as any, {
        name: tabOrder[i].name,
      });
      await expect(element).toBeFocused();

      if (i < tabOrder.length - 1) {
        await page.keyboard.press("Tab");
      }
    }
  });

  test("form validation works correctly", async ({ page }) => {
    // Try to submit with invalid lap number
    await page
      .getByRole("spinbutton", { name: /current lap number/i })
      .fill("0");
    await page
      .getByRole("button", { name: /run undercut simulation/i })
      .click();

    // Should not proceed with invalid data
    await expect(
      page.getByText(/current lap must be greater than 0/i)
    ).toBeVisible();

    // Fix the value
    await page
      .getByRole("spinbutton", { name: /current lap number/i })
      .fill("25");

    // Form should be valid now
    await expect(
      page.getByText(/current lap must be greater than 0/i)
    ).not.toBeVisible();
  });
});
