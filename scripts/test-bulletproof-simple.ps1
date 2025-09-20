# scripts/test-bulletproof-simple.ps1
# Simple local test script for bulletproof CI tests

Write-Host "Running bulletproof parameter fallback tests locally..." -ForegroundColor Green

# Change to the correct directory structure
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

# Set CI-equivalent environment variables
$env:ENV = "test"
$env:TZ = "UTC" 
$env:OFFLINE = "1"
$env:RNG_SEED = "42"
$env:FAST_MODE = "true"
$env:PYTEST_TOLERANCE = "1e-4"

# Check if we're in a virtual environment or need to activate one
$venvPath = ".\backend\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "Activated virtual environment" -ForegroundColor Green
}

# Run the bulletproof tests from the root directory
Write-Host "Running bulletproof tests..." -ForegroundColor Blue
python -m pytest backend\tests\test_deg_backoff.py `
                 backend\tests\test_outlap_backoff.py `
                 backend\tests\test_multihorizon.py `
  -v `
  --tb=short `
  --disable-warnings `
  --override-ini="addopts=-ra --tb=short"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "All bulletproof tests passed! Parameter behavior is rock solid." -ForegroundColor Green
    Write-Host "Ready for CI deployment." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Some tests failed. Check the output above." -ForegroundColor Red
    exit $LASTEXITCODE
}