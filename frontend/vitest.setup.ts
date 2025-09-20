import "@testing-library/jest-dom/vitest";
import { beforeEach, vi } from "vitest";

// Mock fetch for tests
global.fetch = vi.fn();

beforeEach(() => {
  vi.resetAllMocks();
});
