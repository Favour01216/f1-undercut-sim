# 🏎️ F1 Undercut Simulator

[![ci-backend](https://github.com/Favour01216/f1-undercut-sim/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/Favour01216/f1-undercut-sim/actions/workflows/ci-backend.yml)
[![ci-frontend](https://github.com/Favour01216/f1-undercut-sim/actions/workflows/ci-frontend.yml/badge.svg)](https://github.com/Favour01216/f1-undercut-sim/actions/workflows/ci-frontend.yml)
[![codecov](https://codecov.io/gh/Favour01216/f1-undercut-sim/branch/main/graph/badge.svg)](https://codecov.io/gh/Favour01216/f1-undercut-sim)

**A comprehensive Formula 1 undercut simulation tool** that combines real-time F1 data with advanced statistical modeling to predict the success probability of undercut pit strategies. Built with FastAPI, Next.js, and powered by real F1 telemetry data from OpenF1 and Jolpica APIs.

## 📖 Project Description

The F1 Undercut Simulator revolutionizes pit strategy analysis by providing data-driven insights into one of Formula 1's most critical tactical decisions. By leveraging machine learning models trained on real F1 data, this tool calculates undercut probabilities with unprecedented accuracy, helping teams and fans understand the complex mathematics behind successful pit strategies. The system integrates tire degradation physics, pit stop variability, and cold tire performance penalties into a unified Monte Carlo simulation framework.

## 🤖 Data-Driven Modeling Architecture

### Enhanced Statistical Models

The simulator employs sophisticated **data-driven models** that learn circuit and compound-specific parameters from historical F1 data, eliminating hard-coded assumptions and providing more accurate predictions.

#### **DegModel - Advanced Tire Degradation**

- **Method**: Robust quadratic regression with Huber loss
- **Features**: Circuit and compound-specific learning
- **Model**: `lap_delta = a*age² + b*age + c` with outlier resistance
- **Validation**: K-fold cross-validation for reliability assessment
- **Fallback Hierarchy**: Circuit+compound → compound → global models

```python
# Circuit-specific model for Monaco with soft tires
model = DegModel(circuit='MONACO', compound='SOFT')
model.fit_from_data(monaco_lap_data)

# Get fresh tire advantage (data-driven, no hard-coded bonuses)
advantage = model.get_fresh_tire_advantage(old_age=15, new_age=2)
# Returns: e.g., 3.2 seconds advantage for Monaco soft tires
```

#### **OutlapModel - Learned Cold Tire Penalties**

- **Method**: Statistical analysis of outlap vs warmed lap performance
- **Features**: Circuit and compound-specific penalty distributions
- **Learning**: Analyzes stint lap 1 (outlap) vs laps 3+ (warmed)
- **Output**: Learned penalty distributions, not fixed values

```python
# Learn circuit-specific outlap penalties
model = OutlapModel(circuit='SPA', compound='MEDIUM')
model.fit_from_data(spa_outlap_data)

# Sample realistic penalties based on learned data
penalty = model.sample(n=1)  # e.g., 1.8s for Spa medium tires
```

#### **ModelParametersManager - Intelligent Parameter Persistence**

- **Storage**: Parquet files in `features/model_params/`
- **Scope Hierarchy**: Circuit+compound specific → compound-only → global
- **Schema**: Structured dataclasses for degradation and outlap parameters
- **Fallback**: Automatic fallback to broader scopes when specific data unavailable

```python
# Automatic parameter loading with intelligent fallback
manager = ModelParametersManager()

# Try: Monaco + SOFT → SOFT only → Global → Default
params = manager.get_degradation_params(circuit='MONACO', compound='SOFT')
```

### **Elimination of Hard-Coded Biases**

✅ **Removed**: Fixed compound bonuses (`{'SOFT': 1.5, 'MEDIUM': 0.5, 'HARD': 0.0}`)  
✅ **Removed**: Arbitrary base advantages (`base_advantage = 3.0`)  
✅ **Removed**: Static outlap penalties (`{'SOFT': 0.5, 'MEDIUM': 1.2, 'HARD': 2.0}`)

✨ **Replaced With**: Circuit and compound-specific parameters learned from real F1 data using robust statistical methods.

## 🏁 Multi-Lap Undercut Simulation

### **Advanced Multi-Lap Strategy Modeling**

The simulator now supports **multi-lap undercut scenarios** that model realistic strategy battles over H laps instead of single-lap comparisons. This provides more accurate insights into how undercuts actually unfold in races.

#### **Key Features**

- **🕐 Configurable Horizon (H)**: Simulate undercuts over 1-5 laps (default: 2)
- **🎲 Strategic Response Modeling**: Configurable probability for opponent pit responses
- **📊 Enhanced Statistics**: 90% confidence intervals and scenario distributions
- **🔄 Stochastic Simulation**: Per-lap degradation with Monte Carlo variation

#### **Multi-Lap Simulation Logic**

```python
# At t0: Driver A pits (incurs pit loss + outlap penalty)
# Driver B decision: Stay out or respond (probability p_pit_next)

# Scenario 1: B stays out (1 - p_pit_next)
for lap in range(1, H+1):
    A_time = fresh_tire_performance(age=lap) + residual
    B_time = old_tire_performance(age=initial_age+lap) + residual

# Scenario 2: B pits on lap 1 (p_pit_next)
lap_1_B = old_tire_time + pit_loss + outlap_penalty
for lap in range(2, H+1):
    A_time = fresh_tire_performance(age=lap) + residual
    B_time = fresh_tire_performance(age=lap-1) + residual
```

#### **API Enhancement (Backward Compatible)**

```json
{
  "gp": "bahrain",
  "year": 2024,
  "driver_a": "44",
  "driver_b": "1",
  "compound_a": "MEDIUM",
  "lap_now": 25,
  "H": 3, // NEW: Laps to simulate (1-5)
  "p_pit_next": 0.7, // NEW: B pit response probability (0-1)
  "samples": 1000
}
```

**Response includes confidence intervals and scenario breakdowns:**

```json
{
  "p_undercut": 0.68,
  "expected_margin_s": 1.8,
  "ci_low_s": -0.5, // 90% CI lower bound
  "ci_high_s": 4.1, // 90% CI upper bound
  "H_used": 3,
  "assumptions": {
    "scenario_distribution": {
      // Strategy breakdown
      "b_stays_out": 300,
      "b_pits_lap1": 700
    }
  }
}
```

## 🚀 Quickstart

### ⚡ Quick Setup & Run

**1. Backend (FastAPI + Python)**

```bash
# Clone repository
git clone https://github.com/Favour01216/f1-undercut-sim.git
cd f1-undercut-sim

# Install Python dependencies
pip install -e .[dev,test]

# Setup pre-commit hooks
pre-commit install

# Start the FastAPI server
cd backend
python app.py
# ✅ Server running at http://localhost:8000
```

**2. Frontend (Next.js + TypeScript)**

```bash
# Install Node.js dependencies
cd frontend
pnpm install

# Start the development server
pnpm run dev
# ✅ Frontend running at http://localhost:3000
```

**3. Access the Application**

- **🌐 Web Interface**: http://localhost:3000
- **📚 API Documentation**: http://localhost:8000/docs
- **❤️ Health Check**: http://localhost:8000/health

## 🧪 Running Tests Like CI

To reproduce the CI test behavior locally, use the provided Makefile commands:

```bash
# Run backend unit tests (excludes integration tests)
make test-backend

# Run frontend lint, typecheck, and build
make test-frontend

# Run end-to-end tests (optional, not gating)
make e2e
```

### Manual Test Commands

**Backend Tests:**

```bash
# Run all backend unit tests
pytest -m "not integration" --cov=backend --cov-report=term-missing

# Run specific test files
pytest backend/tests/test_api.py -v

# Run with coverage
pytest --cov=backend --cov-report=html
```

**Frontend Tests:**

```bash
cd frontend

# Lint code
pnpm run lint

# Type checking
pnpm run typecheck

# Build application
pnpm run build

# Run e2e tests
pnpm run e2e
```

**Pre-commit Checks:**

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Install pre-commit hooks
pre-commit install
```

## 🔬 Methods & Validation

### Statistical Models

### Enhanced Statistical Models

#### DegModel (Enhanced Tire Degradation)

- **Method**: Robust quadratic regression with Huber loss and iterative reweighting
- **Features**: Circuit and compound-specific parameter learning
- **Model**: `lap_delta = a*age² + b*age + c` with k-fold cross-validation
- **Persistence**: Learned parameters saved to parquet files with intelligent fallback
- **Validation**: R² scoring, RMSE calculation, outlier resistance

```python
# Enhanced model with circuit/compound specificity
model = DegModel(circuit='MONACO', compound='SOFT')
model.fit_from_data(lap_data)  # Learns Monaco-specific soft tire behavior

# Get data-driven tire advantages (no hard-coded bonuses)
advantage = model.get_fresh_tire_advantage(old_age=15, new_age=2)
delta = model.predict(tire_age=15)  # Circuit-specific degradation prediction
```

#### PitModel (Pit Stop Times)

- **Method**: Normal distribution fitting
- **Parameters**: Mean and standard deviation of pit losses
- **Validation**: Minimum 5 pit stops, outlier detection
- **Output**: Random pit loss samples from fitted distribution

```python
model = PitModel()
model.fit(pit_data)  # Fits normal distribution
losses = model.sample(n=1000, rng=rng)  # Monte Carlo sampling
```

#### OutlapModel (Enhanced Cold Tire Performance)

- **Method**: Circuit and compound-specific penalty learning
- **Features**: Learned distributions from real outlap analysis
- **Validation**: Separate outlap (stint lap 1) vs warmed laps (lap 3+)
- **Persistence**: Stored parameters with hierarchical fallback system
- **Output**: Data-driven penalty samples, not fixed values

```python
# Enhanced model with circuit/compound learning
model = OutlapModel(circuit='SPA', compound='MEDIUM')
model.fit_from_data(lap_data)  # Learns Spa-specific medium tire outlaps

# Sample from learned penalty distribution
penalty = model.sample(n=1000, rng=rng)  # Real data-driven penalties
expected = model.get_expected_penalty()  # Mean penalty for this context
```

#### PitModel (Pit Stop Times)

- **Method**: Normal distribution fitting
- **Parameters**: Mean and standard deviation of pit losses
- **Validation**: Minimum 5 pit stops, outlier detection
- **Output**: Random pit loss samples from fitted distribution

```python
model = PitModel()
model.fit(pit_data)  # Fits normal distribution
losses = model.sample(n=1000, rng=rng)  # Monte Carlo sampling
```

#### OutlapModel (Cold Tire Performance)

- **Method**: Compound-specific penalty modeling
- **Compounds**: SOFT, MEDIUM, HARD tire analysis
- **Validation**: Separate outlap (stint lap 1) vs warmed laps
- **Output**: Random outlap penalty by compound

```python
model = OutlapModel()
model.fit(lap_data)  # Analyzes outlap vs warmed performance
penalty = model.sample('SOFT', n=1000, rng=rng)  # Samples cold tire penalties
```

### Enhanced Monte Carlo Simulation

The undercut probability calculation uses **data-driven Monte Carlo simulation** with deterministic seeding and circuit-specific models:

```python
# Deterministic RNG for reproducible results
rng = np.random.default_rng(seed=42)

# Enhanced models with circuit/compound specificity
circuit_deg_model = DegModel(circuit=circuit, compound=compound_a)
circuit_outlap_model = OutlapModel(circuit=circuit, compound=compound_a)

# For each simulation iteration (default: 1000)
pit_loss = PitModel.sample(rng=rng)

# Data-driven outlap penalty (learned from real data)
outlap_penalty = circuit_outlap_model.sample(rng=rng)

# Circuit-specific tire degradation (no hard-coded bonuses)
fresh_advantage = circuit_deg_model.get_fresh_tire_advantage(
    old_age=current_tire_age + lap,
    new_age=1.0 + lap
)

# Undercut succeeds if:
undercut_success = (current_gap + pit_loss + outlap_penalty) < fresh_advantage

# Final probability with confidence intervals
p_undercut = (successful_undercuts / total_simulations) * 100
```

**Key Enhancements:**

- ✅ Circuit-specific degradation models
- ✅ Compound-specific outlap penalties
- ✅ Learned parameters from real F1 data
- ✅ Intelligent fallback hierarchy
- ✅ No hard-coded tire advantages

## 📊 Data Sources & Licenses

### OpenF1 API

- **Purpose**: Live timing, telemetry, and session data
- **Website**: [openf1.org](https://openf1.org/)
- **License**: Public API, fair use terms
- **Data**: Lap times, pit stops, session details, driver positions
- **Rate Limits**: Respectful usage with caching and retry logic

### Jolpica F1 API (Ergast)

- **Purpose**: Historical race results and schedule data
- **Website**: [ergast.com/mrd](http://ergast.com/mrd/)
- **License**: Creative Commons Attribution-NonCommercial-ShareAlike
- **Data**: Race results, championship standings, circuit information
- **Historical**: Complete F1 data from 1950 to present

### FastF1 (Optional Enhancement)

- **Purpose**: Advanced telemetry analysis
- **Website**: [docs.fastf1.dev](https://docs.fastf1.dev/)
- **License**: MIT License
- **Data**: Detailed car telemetry, track maps, weather data
- **Note**: Can be integrated for enhanced analysis

## 🧪 Testing & Development

### Running Tests

**Backend Tests**

```bash
cd backend

# Run all unit tests (excludes integration tests)
python -m pytest tests/ -v -m "not integration"

# Run with coverage
python -m pytest tests/ --cov=models --cov=services --cov=app --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_deg.py -v

# Run integration tests (hits real APIs)
python -m pytest tests/ -v -m "integration"
```

**Frontend Tests**

```bash
cd frontend

# Type checking
pnpm run type-check

# Linting
pnpm run lint

# Build check
pnpm run build
```

### Development Setup

**Prerequisites:**

- Python 3.11+
- Node.js 20+
- pnpm 9+

**Environment Setup:**

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
vim .env

# Install pre-commit hooks
pre-commit install
```

### Code Quality

All code is automatically formatted and linted using:

- **Ruff**: Fast Python linter and formatter (line-length: 100)
- **Black**: Python code formatter (fallback)
- **ESLint**: JavaScript/TypeScript linting
- **Prettier**: Code formatting

## 🚦 CI/CD Pipeline

### GitHub Actions Workflows

**Backend CI** (`.github/workflows/ci-backend.yml`):

- Python 3.11 testing
- Pre-commit hook validation
- Unit tests with 80% coverage requirement
- Security scanning with bandit
- Type checking

**Frontend CI** (`.github/workflows/ci-frontend.yml`):

- Node.js 20 with pnpm
- TypeScript compilation
- ESLint validation
- Build verification
- Bundle size analysis

### Branch Protection

**Required Status Checks:**

- `ci-backend` must pass
- `ci-frontend` must pass
- All tests deterministic (no network calls in unit tests)
- 80%+ test coverage

## � Monitoring & Observability

### Error Tracking with Sentry

This application includes comprehensive error tracking and performance monitoring using [Sentry](https://sentry.io/).

#### Backend Configuration

Set the following environment variables for the FastAPI backend:

```bash
# Required: Sentry DSN for error tracking
SENTRY_DSN=https://your-dsn@o12345.ingest.sentry.io/67890

# Optional: Environment name (default: development)
SENTRY_ENVIRONMENT=production

# Optional: Performance monitoring sample rates (default: 0.1)
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1

# Optional: Logging level (default: INFO)
LOG_LEVEL=INFO
```

#### Frontend Configuration

Set the following environment variables for the Next.js frontend:

```bash
# Required: Enable Sentry (must be 'true' to activate)
NEXT_PUBLIC_ENABLE_SENTRY=true

# Required: Sentry DSN (can be same as backend)
NEXT_PUBLIC_SENTRY_DSN=https://your-dsn@o12345.ingest.sentry.io/67890

# Optional: Environment name (default: development)
NEXT_PUBLIC_SENTRY_ENVIRONMENT=production

# Optional: Performance monitoring sample rate (default: 0.1)
NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE=0.1

# Optional: Sentry organization and project for source map uploads
SENTRY_ORG=your-org
SENTRY_PROJECT=your-project
```

#### What Gets Monitored

**Backend (FastAPI):**

- All API endpoint errors with request context
- Performance metrics for `/simulate` endpoint
- Request timing and throughput
- Model fitting failures and data issues
- Structured JSON logs with request IDs

**Frontend (Next.js):**

- JavaScript errors and unhandled exceptions
- API failure responses with status codes
- React component errors via Error Boundary
- User interaction errors and form validation

#### Privacy & Data Protection

**⚠️ Privacy Notice**: This application is designed with privacy in mind:

- **No PII in Logs**: Driver names and personally identifiable information are never logged
- **Input Hashing**: Simulation inputs are hashed (SHA256) for privacy-safe request tracking
- **Rounded Outputs**: Numerical results are rounded before logging to prevent precision-based identification
- **Request IDs**: Each request gets a unique UUID for correlation without exposing user data
- **No Default PII**: Sentry is configured with `sendDefaultPii: false`

**Logged Data Examples:**

```json
{
  "level": "info",
  "timestamp": "2024-01-15T10:30:45Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Simulation completed successfully",
  "input_hash": "a1b2c3d4e5f6789",
  "duration_ms": 245.67,
  "p_undercut": 0.675,
  "models_used": { "deg": true, "pit": true, "outlap": false }
}
```

#### Local Development

For local development, you can disable Sentry monitoring:

```bash
# Disable Sentry completely
NEXT_PUBLIC_ENABLE_SENTRY=false
# Don't set SENTRY_DSN
```

Logs will still be output to the console for debugging purposes.

#### Setting Up Sentry

1. **Create a Sentry Account**: Sign up at [sentry.io](https://sentry.io/)
2. **Create Projects**: Set up separate projects for backend and frontend
3. **Get DSNs**: Copy the DSN from each project's settings
4. **Configure Environment**: Set the environment variables listed above
5. **Deploy**: Your application will start sending telemetry data to Sentry

For more details, see the [Sentry documentation](https://docs.sentry.io/).

## �📦 Project Structure

```
f1-undercut-sim/
├── backend/                    # FastAPI backend
│   ├── models/                 # Statistical models
│   │   ├── deg.py             # DegModel - tire degradation
│   │   ├── pit.py             # PitModel - pit stop sampling
│   │   └── outlap.py          # OutlapModel - cold tire penalties
│   ├── services/              # External API integrations
│   │   ├── openf1.py          # OpenF1 API client
│   │   └── jolpica.py         # Jolpica API client
│   ├── tests/                 # Unit and integration tests
│   │   ├── conftest.py        # Test fixtures and mocks
│   │   ├── test_deg.py        # DegModel tests
│   │   ├── test_pit.py        # PitModel tests
│   │   ├── test_outlap.py     # OutlapModel tests
│   │   └── test_api.py        # FastAPI endpoint tests
│   └── app.py                 # FastAPI application
├── frontend/                  # Next.js frontend
│   ├── app/                   # Next.js App Router
│   ├── components/            # React components
│   │   ├── simulation-form.tsx     # Main form interface
│   │   ├── simulation-results.tsx  # Results display
│   │   ├── performance-chart.tsx   # Plotly.js heatmap
│   │   └── ui/                # shadcn/ui components
│   ├── lib/                   # Utilities and API client
│   ├── types/                 # TypeScript definitions
│   └── styles/               # Global styles
├── docs/                      # Documentation
│   └── glossary.md           # F1 terminology glossary
├── .github/workflows/         # CI/CD pipelines
│   ├── ci-backend.yml        # Backend testing
│   └── ci-frontend.yml       # Frontend testing
├── .pre-commit-config.yaml   # Code quality hooks
├── pyproject.toml            # Python dependencies and tools
└── README.md                 # This file
```

## ⚠️ Limitations & Future Work

### Current Limitations

#### Data Limitations

- **Historical Coverage**: OpenF1 data available from 2023+ (recent seasons only)
- **Session Matching**: GP name matching requires manual mapping for some circuits
- **Weather Data**: Current models don't account for weather impact on strategy
- **Tire Compound**: Limited to basic compound types (SOFT, MEDIUM, HARD)

#### Model Limitations

- **Track Specificity**: Models are not track-specific (Monaco vs Monza differences)
- **Traffic Modeling**: Doesn't account for traffic impact on lap times
- **DRS Zones**: No explicit DRS impact on overtaking probability post-undercut
- **Fuel Load**: Degradation models don't account for decreasing fuel weight

#### Technical Limitations

- **Real-time Data**: No live race integration (historical analysis only)
- **Driver Skill**: Models assume equal driver performance
- **Car Performance**: No car-specific performance differences modeled
- **Strategy Complexity**: Limited to simple undercut scenarios (not overcuts, double-stacks)

### Future Enhancements

#### Data & Modeling

- [ ] **Weather Integration**: Incorporate weather data for strategy impact
- [ ] **Track-Specific Models**: Individual models for each circuit
- [ ] **Machine Learning**: Advanced ML models (Random Forest, Neural Networks)
- [ ] **Real-time Integration**: Live race data streaming and real-time predictions
- [ ] **Multi-compound Strategy**: Complex tire strategy optimization
- [ ] **Traffic Simulation**: Model traffic impact on undercut success

#### Features & User Experience

- [ ] **Mobile App**: React Native mobile application
- [ ] **Team Dashboard**: Multi-driver strategy comparison dashboard
- [ ] **Historical Analysis**: Season-long strategy pattern analysis
- [ ] **API Webhooks**: Real-time notifications for strategy opportunities
- [ ] **Advanced Visualizations**: 3D track visualization with strategy overlay
- [ ] **Collaborative Features**: Team strategy sharing and discussion

#### Technical Improvements

- [ ] **Performance Optimization**: GPU acceleration for Monte Carlo simulations
- [ ] **Database Integration**: PostgreSQL for historical data persistence
- [ ] **Microservices**: Containerized deployment with Kubernetes
- [ ] **A/B Testing**: Model performance comparison framework
- [ ] **Documentation**: Interactive API documentation with live examples
- [ ] **Testing**: Extended integration and end-to-end test coverage

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- **Development Setup**: Local environment configuration
- **Code Style**: Formatting and linting requirements
- **Testing Guidelines**: Unit and integration test standards
- **Pull Request Process**: Review and merge procedures
- **Branch Strategy**: Git Flow workflow

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

**Data Providers:**

- **OpenF1** for live timing and telemetry data
- **Jolpica F1 (Ergast)** for historical race data
- **Formula 1** for the amazing sport that inspired this project

**Technologies:**

- **FastAPI** for the robust backend framework
- **Next.js** for the modern frontend experience
- **Plotly.js** for beautiful data visualizations
- **shadcn/ui** for elegant UI components

---

**Made with ❤️ for Formula 1 strategy nerds and data enthusiasts.**
