# Bulletproof CI Tests

This directory contains comprehensive bulletproof tests designed to guard learned-parameter behavior and ensure CI reliability for the F1 Undercut Simulation project.

## Test Suite Overview

### 🛡️ Core Test Files (31 Tests Total)

1. **`test_deg_backoff.py`** (9 tests)

   - **Purpose**: Tests degradation model parameter fallback when R² < 0.1
   - **Coverage**: Circuit-specific → compound-only → global parameter hierarchy
   - **Key Behaviors**: Quality threshold enforcement, weak signal detection, parameter scope validation

2. **`test_outlap_backoff.py`** (12 tests)

   - **Purpose**: Tests outlap model parameter fallback with small sample sizes
   - **Coverage**: Sample size thresholds, penalty value ranges, mu/sigma fallback hierarchy
   - **Key Behaviors**: Minimum sample enforcement, compound-only prioritization, edge case handling

3. **`test_multihorizon.py`** (10 tests)
   - **Purpose**: Tests multi-horizon simulation behavior (H=1 through H=5 laps)
   - **Coverage**: Fresh tire advantage validation, scenario distribution, pit window timing
   - **Key Behaviors**: Deterministic reproducibility, horizon probability progression, tire degradation effects

### 🔧 Supporting Infrastructure

4. **`fixtures/model_params.py`**

   - Synthetic parameter generation for CI testing
   - No network dependencies, deterministic data creation
   - Comprehensive degradation and outlap parameter utilities

5. **CI Workflow Enhancements** (`.github/workflows/ci-backend.yml`)
   - Dedicated bulletproof test job for fast feedback
   - `OFFLINE=1` environment with synthetic parameter generation
   - Marker-based test filtering and proper tolerance handling

## 🚀 Quick Start

### Run Bulletproof Tests Locally

```powershell
# Windows PowerShell
.\scripts\test-bulletproof-simple.ps1
```

```bash
# Linux/macOS
./scripts/test-bulletproof.sh
```

### Run Specific Test Categories

```bash
# Test only parameter fallback behavior
pytest -m "fallback" -v

# Test only multi-horizon simulation
pytest -m "multihorizon" -v

# Test specific files
pytest backend/tests/test_deg_backoff.py -v
```

## 🎯 Test Features

### ✅ Deterministic Testing

- Fixed random seeds (`RNG_SEED=42`) for reproducible CI runs
- Synthetic parameter generation without network dependencies
- Consistent tolerance values (1e-4 default, 1e-3 for probabilities)

### ✅ Comprehensive Mocking

- ModelParametersManager with realistic fallback behavior
- Mock simulation functions with tire advantage validation
- Parameter hierarchy testing with proper scope validation

### ✅ CI-Optimized

- Runs in offline mode with `OFFLINE=1`
- Fast execution (~2-3 seconds total)
- Fail-fast design for quick feedback

### ✅ Robust Parameter Validation

- Tests R² quality thresholds (< 0.1 triggers fallback)
- Sample size enforcement for outlap models
- Multi-horizon fresh tire advantage assertions
- Edge case coverage (empty stores, case sensitivity, extreme scenarios)

## 📊 Test Statistics

| Test Category        | Count  | Purpose                                    |
| -------------------- | ------ | ------------------------------------------ |
| Degradation Fallback | 9      | R² threshold and quality enforcement       |
| Outlap Fallback      | 12     | Sample size and penalty validation         |
| Multi-Horizon        | 10     | Fresh tire advantage and scenario coverage |
| **Total**            | **31** | **Complete parameter behavior coverage**   |

## 🔍 Marker System

- `@pytest.mark.unit` - Fast unit tests (no external dependencies)
- `@pytest.mark.fallback` - Parameter fallback behavior tests
- `@pytest.mark.multihorizon` - Multi-horizon simulation tests
- `@pytest.mark.integration` - Integration tests (if needed)
- `@pytest.mark.slow` - Slow-running tests

## 🛠️ Environment Variables

The tests respect these CI environment variables:

```bash
ENV=test                 # Test environment mode
TZ=UTC                  # Timezone standardization
OFFLINE=1               # No network access
RNG_SEED=42            # Deterministic random behavior
FAST_MODE=true         # Optimized for speed
PYTEST_TOLERANCE=1e-4  # Numeric comparison tolerance
```

## 🔒 CI Integration

The bulletproof tests are integrated into CI with a dedicated job that:

1. **Runs First**: Provides fast feedback before full test suite
2. **Uses Synthetic Data**: No external API dependencies
3. **Validates Markers**: Ensures test categorization works correctly
4. **Enforces Quality**: Guards against parameter behavior regressions

### CI Job Flow

```yaml
bulletproof-tests: # Fast parameter validation
  ↓
test: # Full test suite (only runs if bulletproof passes)
  ↓
type-check: # Static analysis
  ↓
security: # Security scanning
```

## 📈 Success Criteria

✅ **All 31 tests pass consistently**  
✅ **Deterministic behavior across runs**  
✅ **Fast execution (< 5 seconds)**  
✅ **Comprehensive parameter hierarchy coverage**  
✅ **Proper fallback behavior validation**

## 🎯 Testing Philosophy

These tests embody a "bulletproof" approach:

- **Guard against regressions** in learned parameter behavior
- **Fail fast** on parameter hierarchy violations
- **Provide clear feedback** on what broke and why
- **Run consistently** across development and CI environments
- **Cover edge cases** that could cause silent failures

The goal is to make parameter behavior changes **intentional and visible**, preventing silent degradation of model quality due to fallback logic issues.
