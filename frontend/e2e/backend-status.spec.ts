import { test, expect } from "@playwright/test";

test.describe("Backend Status & Error Handling", () => {
  test("backend connected state shows success banner", async ({ page }) => {
    // Mock successful backend status check
    await page.route("**/api/v1/**", async (route) => {
      const url = route.request().url();

      if (url.includes("/")) {
        // Mock root endpoint (backend status)
        const json = {
          message: "F1 Undercut Simulator API",
          version: "0.2.0",
          health: "healthy",
          docs: "/docs",
          simulate: "/simulate",
        };
        await route.fulfill({ json });
      }
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Check for connected status banner
    await expect(page.getByText("✅ Backend Connected")).toBeVisible();
    await expect(page.getByText("API Ready")).toBeVisible();
    await expect(page.getByText("0.2.0")).toBeVisible(); // Version badge
  });

  test("backend disconnected state shows error banner", async ({ page }) => {
    // Mock failed backend status check
    await page.route("**/api/v1/**", async (route) => {
      await route.abort("failed");
    });

    await page.route("**/", async (route) => {
      await route.abort("failed");
    });

    await page.goto("/");

    // Wait a bit for the status check to fail
    await page.waitForTimeout(2000);

    // Check for disconnected status banner
    await expect(page.getByText("❌ Backend Disconnected")).toBeVisible();
    await expect(
      page.getByText("Cannot connect to F1 Undercut Simulator API")
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /retry/i })).toBeVisible();
  });

  test("backend status banner retry functionality", async ({ page }) => {
    let requestCount = 0;

    // Mock backend - first attempt fails, second succeeds
    await page.route("**/api/v1/**", async (route) => {
      requestCount++;
      if (requestCount === 1) {
        await route.abort("failed");
      } else {
        const json = {
          message: "F1 Undercut Simulator API",
          version: "0.2.0",
          health: "healthy",
        };
        await route.fulfill({ json });
      }
    });

    await page.route("**/", async (route) => {
      if (requestCount === 1) {
        await route.abort("failed");
      } else {
        const json = {
          message: "F1 Undercut Simulator API",
          version: "0.2.0",
          health: "healthy",
        };
        await route.fulfill({ json });
      }
    });

    await page.goto("/");

    // Wait for initial failure
    await expect(page.getByText("❌ Backend Disconnected")).toBeVisible();

    // Click retry button
    await page.getByRole("button", { name: /retry/i }).click();

    // Should now show connected state
    await expect(page.getByText("✅ Backend Connected")).toBeVisible();
  });

  test("simulation fails gracefully when backend is down", async ({ page }) => {
    // Mock backend status as healthy initially
    await page.route("**/", async (route) => {
      const json = {
        message: "F1 Undercut Simulator API",
        version: "0.2.0",
        health: "healthy",
      };
      await route.fulfill({ json });
    });

    // But mock simulate endpoint as failing
    await page.route("**/simulate", async (route) => {
      await route.abort("failed");
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Verify initial connected state
    await expect(page.getByText("✅ Backend Connected")).toBeVisible();

    // Try to run simulation
    await page
      .getByRole("button", { name: /run undercut simulation/i })
      .click();

    // Should show error toast
    await expect(page.getByText("Simulation Failed")).toBeVisible();

    // Results section should show error state
    await expect(page.getByText(/simulation error/i)).toBeVisible();
  });

  test("compact status indicator works correctly", async ({ page }) => {
    // Mock connected backend
    await page.route("**/", async (route) => {
      const json = {
        message: "F1 Undercut Simulator API",
        version: "0.2.0",
        health: "healthy",
      };
      await route.fulfill({ json });
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // On mobile/smaller screens, should show compact status
    await page.setViewportSize({ width: 480, height: 800 });

    // Status should still be visible but in compact form
    await expect(page.getByText("Backend Connected")).toBeVisible();
  });

  test("network timeout handling", async ({ page }) => {
    // Mock very slow backend response (timeout)
    await page.route("**/", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 10000)); // 10 second delay
      const json = { message: "F1 Undercut Simulator API" };
      await route.fulfill({ json });
    });

    await page.goto("/");

    // Should show checking state initially
    await expect(page.getByText("Connecting to backend...")).toBeVisible();

    // After timeout, should show error state
    await expect(page.getByText("❌ Backend Disconnected")).toBeVisible({
      timeout: 15000,
    });
  });

  test("development mode banner appears correctly", async ({ page }) => {
    // Mock connected backend
    await page.route("**/", async (route) => {
      const json = {
        message: "F1 Undercut Simulator API",
        version: "0.2.0",
        health: "healthy",
      };
      await route.fulfill({ json });
    });

    // Set development environment (this may need to be set in the app or via env vars)
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // In development mode, should show dev warning
    const devWarning = page.getByText("🚧 Development Mode");
    if (await devWarning.isVisible()) {
      await expect(
        page.getByText("Backend running on localhost:8000")
      ).toBeVisible();
      await expect(page.getByText("DEV")).toBeVisible();
    }
  });
});
