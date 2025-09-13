# F1 Strategy Dashboard - E2E Tests

This directory contains comprehensive end-to-end tests for the F1 Undercut Strategy Dashboard using Playwright.

## 🎯 Test Coverage

### 1. Dashboard Loading (`dashboard.spec.ts`)

- ✅ Dashboard renders with correct title and structure
- ✅ All SimulationForm controls are accessible and functional
- ✅ Keyboard navigation works correctly through all form elements
- ✅ Form validation displays appropriate error messages
- ✅ Default form values are properly set

### 2. Simulation Functionality (`simulation.spec.ts`)

- ✅ Mocks `/simulate` API and verifies ResultCards render correct data
- ✅ Tests successful simulation flow with probability and stats display
- ✅ Error handling with appropriate toast notifications
- ✅ Loading states during simulation execution
- ✅ Session history functionality (create, copy, delete)

### 3. Heatmap Generation (`heatmap.spec.ts`)

- ✅ Triggers heatmap generation after base simulation
- ✅ Verifies Plotly trace exists and chart renders correctly
- ✅ Loading skeleton during multi-simulation heatmap generation
- ✅ Error handling for failed heatmap generation with retry functionality
- ✅ Empty state display when no base simulation exists
- ✅ Interactive features and tooltip functionality

### 4. Backend Status (`backend-status.spec.ts`)

- ✅ Connected state shows success banner with version info
- ✅ Disconnected state shows error banner with retry button
- ✅ Status banner retry functionality works correctly
- ✅ Graceful simulation failure when backend is down
- ✅ Compact status indicator for mobile viewports
- ✅ Network timeout handling
- ✅ Development mode banner display

## 🛠️ Running Tests

### Prerequisites

```bash
npm install
npx playwright install chromium
```

### Commands

```bash
# Run all tests (headless)
npm run test:e2e

# Run tests with UI (interactive mode)
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Debug specific test
npm run test:e2e:debug -- dashboard.spec.ts

# Generate and view HTML report
npm run test:e2e:report
```

### Specific Test Files

```bash
# Run only dashboard tests
npx playwright test dashboard

# Run only simulation tests
npx playwright test simulation

# Run only heatmap tests
npx playwright test heatmap

# Run only backend status tests
npx playwright test backend-status
```

## 🎭 Test Architecture

### Mock Strategy

All tests use route mocking to avoid external dependencies:

- **Backend API**: Mocked with realistic JSON responses
- **Simulation Endpoints**: Controlled responses for consistent testing
- **Error Conditions**: Simulated network failures and timeouts

### Test Utilities (`test-utils.ts`)

Reusable functions for common operations:

- `mockBackendConnected()` - Mock successful backend connection
- `mockBackendDisconnected()` - Mock backend failure
- `mockSuccessfulSimulation()` - Mock simulation success
- `fillSimulationForm()` - Fill form with test data
- `submitSimulation()` - Submit form and wait for completion
- `waitForHeatmap()` - Wait for heatmap generation
- `generateHeatmapMockData()` - Generate realistic heatmap data

### Accessibility Testing

Tests include accessibility verification:

- ✅ ARIA labels and descriptions
- ✅ Keyboard navigation patterns
- ✅ Screen reader compatibility
- ✅ Focus management
- ✅ Semantic HTML structure

## 📊 CI Integration

### GitHub Actions (`ci-e2e.yml`)

- **Job Name**: `ci-e2e` (for branch protection)
- **Browser**: Headless Chromium
- **Backend**: Python 3.11 with FastAPI
- **Artifacts**: HTML reports and test results
- **Caching**: npm dependencies and pip packages
- **Accessibility Audit**: axe-core integration

### Branch Protection

Add `ci-e2e` to required status checks:

1. Go to repository Settings → Branches
2. Edit main branch protection rule
3. Add `ci-e2e` to required checks

## 🚀 Best Practices

### Writing New Tests

1. **Use Page Object Pattern**: Extract complex interactions to utilities
2. **Mock External Dependencies**: Never rely on real APIs in E2E tests
3. **Test User Journeys**: Focus on complete workflows, not individual components
4. **Include Error Cases**: Test both happy path and error conditions
5. **Verify Accessibility**: Ensure ARIA attributes and keyboard navigation

### Test Data

```typescript
// Good: Realistic test data
const mockResponse = {
  p_undercut: 0.75,
  pitLoss_s: 24.5,
  outLapDelta_s: 1.2,
  assumptions: {
    gap_s: 5.0,
    tyre_age_b: 15,
    degradation_model: "quadratic",
  },
};

// Bad: Unrealistic or minimal data
const mockResponse = { p_undercut: 1.0 };
```

### Assertions

```typescript
// Good: Specific, meaningful assertions
await expect(
  page.getByRole("button", { name: /run undercut simulation/i })
).toBeVisible();
await expect(page.getByText("75.0%")).toBeVisible();

// Bad: Generic assertions
await expect(page.locator("button")).toBeVisible();
await expect(page.getByText("75")).toBeVisible();
```

## 📈 Performance

### Test Execution

- **Average Runtime**: ~2-3 minutes for full suite
- **Parallel Execution**: Tests run in parallel for speed
- **Selective Running**: Target specific test files for faster iteration

### Resource Usage

- **Browser**: Chromium (lightweight for CI)
- **Memory**: ~500MB peak during heatmap tests
- **Network**: All mocked, no external requests

## 🔧 Troubleshooting

### Common Issues

**Tests failing locally?**

```bash
# Ensure dev server is running
npm run dev

# Check backend is accessible
curl http://localhost:8000/
```

**Browser not found?**

```bash
npx playwright install chromium
```

**Flaky tests?**

- Increase timeouts for slow operations (heatmap generation)
- Add proper wait conditions before assertions
- Check for race conditions in async operations

**CI failures?**

- Review uploaded HTML report artifacts
- Check screenshots and videos for failed tests
- Verify backend service is healthy in CI logs

## 📝 Coverage Report

Current test coverage includes:

- 🟢 **Form Interactions**: 100% of form controls tested
- 🟢 **API Integration**: All endpoints mocked and tested
- 🟢 **Error Handling**: All error states covered
- 🟢 **Accessibility**: WCAG compliance verified
- 🟢 **Mobile Responsive**: Mobile viewports tested
- 🟢 **Loading States**: All async operations covered
