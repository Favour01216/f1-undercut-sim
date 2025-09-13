# 🏎️ F1 Undercut Simulator

[![ci-backend](https://github.com/Favour01216/f1-undercut-sim/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/Favour01216/f1-undercut-sim/actions/workflows/ci-backend.yml)
[![ci-frontend](https://github.com/Favour01216/f1-undercut-sim/actions/workflows/ci-frontend.yml/badge.svg)](https://github.com/Favour01216/f1-undercut-sim/actions/workflows/ci-frontend.yml)
[![codecov](https://codecov.io/gh/Favour01216/f1-undercut-sim/branch/main/graph/badge.svg)](https://codecov.io/gh/Favour01216/f1-undercut-sim)

**A comprehensive Formula 1 undercut simulation tool** that combines real-time F1 data with advanced statistical modeling to predict the success probability of undercut pit strategies. Built with FastAPI, Next.js, and powered by real F1 telemetry data from OpenF1 and Jolpica APIs.

## 📖 Project Description

The F1 Undercut Simulator revolutionizes pit strategy analysis by providing data-driven insights into one of Formula 1's most critical tactical decisions. By leveraging machine learning models trained on real F1 data, this tool calculates undercut probabilities with unprecedented accuracy, helping teams and fans understand the complex mathematics behind successful pit strategies. The system integrates tire degradation physics, pit stop variability, and cold tire performance penalties into a unified Monte Carlo simulation framework.

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

## 🔬 Methods & Validation

### Statistical Models

#### DegModel (Tire Degradation)
- **Method**: Quadratic regression fitting
- **Formula**: `lap_delta = a*age² + b*age + c`
- **Validation**: R² > 0.7, minimum 5 data points
- **Output**: Predicted lap time delta for given tire age

```python
model = DegModel()
model.fit(lap_data)  # Fits quadratic degradation curve
delta = model.predict(tire_age=15)  # Returns time loss in seconds
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

### Monte Carlo Simulation

The undercut probability calculation uses Monte Carlo simulation with deterministic seeding:

```python
# Deterministic RNG for reproducible results
rng = np.random.default_rng(seed=42)

# For each simulation iteration (default: 1000)
pit_loss = PitModel.sample(rng=rng)
outlap_penalty = OutlapModel.sample(compound, rng=rng)
stay_out_delta = DegModel.predict(current_tire_age + 1)

# Undercut succeeds if:
undercut_success = (current_gap + pit_loss + outlap_penalty) < stay_out_delta

# Final probability
p_undercut = (successful_undercuts / total_simulations) * 100
```

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

## 📦 Project Structure

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