#!/bin/bash
# scripts/test-bulletproof.sh
# Local test script to run bulletproof CI tests matching the CI environment

set -e

echo "🛡️ Running bulletproof parameter fallback tests locally..."

# Set CI-equivalent environment
export ENV=test
export TZ=UTC
export OFFLINE=1
export RNG_SEED=42
export FAST_MODE=true
export PYTEST_TOLERANCE=1e-4

# Change to backend directory
cd "$(dirname "$0")/../backend"

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Activated virtual environment"
else
    echo "⚠️ No virtual environment found, using system Python"
fi

# Set up synthetic model parameters
echo "📊 Setting up synthetic model parameters..."
mkdir -p features/model_params
python -c "
from backend.tests.fixtures.model_params import setup_minimal_model_params
from pathlib import Path
setup_minimal_model_params(Path('.'))
print('✅ Synthetic model parameters created')
"

# Run the bulletproof tests
echo "🧪 Running bulletproof tests..."
pytest backend/tests/test_deg_backoff.py \
       backend/tests/test_outlap_backoff.py \
       backend/tests/test_multihorizon.py \
  -v \
  --tb=short \
  --strict-markers \
  --disable-warnings \
  --durations=10

echo ""
echo "🎯 Testing marker filtering..."
echo "Fallback tests:"
pytest -m "fallback" --collect-only -q | grep "::test_" | wc -l
echo "Multihorizon tests:"
pytest -m "multihorizon" --collect-only -q | grep "::test_" | wc -l

echo ""
echo "✅ All bulletproof tests passed! Your parameter behavior is rock solid."
echo "🚀 Ready for CI deployment."