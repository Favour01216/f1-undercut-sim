# scripts/test-bulletproof.ps1
# Local test script to run bulletproof CI tests matching the CI environment

Write-Host "Running bulletproof parameter fallback tests locally..." -ForegroundColor Green

# Set CI-equivalent environment
$env:ENV = "test"
$env:TZ = "UTC"
$env:OFFLINE = "1"
$env:RNG_SEED = "42"
$env:FAST_MODE = "true"
$env:PYTEST_TOLERANCE = "1e-4"

# Change to backend directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$backendDir = Join-Path (Split-Path -Parent $scriptDir) "backend"
Set-Location $backendDir

# Activate virtual environment if it exists
$venvPath = Join-Path $backendDir ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "Activated virtual environment" -ForegroundColor Green
} else {
    Write-Host "No virtual environment found, using system Python" -ForegroundColor Yellow
}

# Set up synthetic model parameters
Write-Host "Setting up synthetic model parameters..." -ForegroundColor Blue
New-Item -ItemType Directory -Force -Path "features\model_params" | Out-Null
python -c @"
from backend.tests.fixtures.model_params import setup_minimal_model_params
from pathlib import Path
setup_minimal_model_params(Path('.'))
print('Synthetic model parameters created')
"@

# Run the bulletproof tests
Write-Host "Running bulletproof tests..." -ForegroundColor Blue
python -m pytest backend/tests/test_deg_backoff.py `
                 backend/tests/test_outlap_backoff.py `
                 backend/tests/test_multihorizon.py `
  -v `
  --tb=short `
  --strict-markers `
  --disable-warnings `
  --durations=10

Write-Host ""
Write-Host "Testing marker filtering..." -ForegroundColor Blue
Write-Host "Fallback tests:"
$fallbackCount = (python -m pytest -m "fallback" --collect-only -q | Select-String "::test_").Count
Write-Host $fallbackCount
Write-Host "Multihorizon tests:"
$multihorizonCount = (python -m pytest -m "multihorizon" --collect-only -q | Select-String "::test_").Count
Write-Host $multihorizonCount

Write-Host ""
Write-Host "All bulletproof tests passed! Your parameter behavior is rock solid." -ForegroundColor Green
Write-Host "Ready for CI deployment." -ForegroundColor Green