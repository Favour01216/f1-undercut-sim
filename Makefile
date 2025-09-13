# F1 Undercut Simulator - Test Commands
# Run these commands to reproduce CI behavior locally

.PHONY: test-backend test-frontend e2e help

help:
	@echo "Available commands:"
	@echo "  test-backend  - Run backend unit tests (excludes integration tests)"
	@echo "  test-frontend - Run frontend lint, typecheck, and build"
	@echo "  e2e          - Run end-to-end tests (optional, not gating)"

test-backend:
	@echo "Running backend tests..."
	pytest -q -m "not integration" --cov=backend --cov-report=term-missing

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && pnpm run lint && pnpm run typecheck && pnpm run build

e2e:
	@echo "Running e2e tests (optional)..."
	cd frontend && pnpm run e2e || echo "E2E optional; not gating"