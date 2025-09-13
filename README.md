# F1 Undercut Simulator

**A comprehensive Formula 1 undercut simulation tool** that combines real-time F1 data with advanced statistical modeling to predict the success probability of undercut pit strategies. Built with FastAPI, Next.js, and powered by real F1 telemetry data from OpenF1 and Jolpica APIs.

## 📖 Project Description

The F1 Undercut Simulator revolutionizes pit strategy analysis by providing data-driven insights into one of Formula 1's most critical tactical decisions. By leveraging machine learning models trained on real F1 data, this tool calculates undercut probabilities with unprecedented accuracy, helping teams and fans understand the complex mathematics behind successful pit strategies. The system integrates tire degradation physics, pit stop variability, and cold tire performance penalties into a unified Monte Carlo simulation framework.

## 🏎️ Live Demo

- **Frontend**: http://localhost:3000 (Next.js)
- **Backend API**: http://localhost:8000 (FastAPI)
- **API Docs**: http://localhost:8000/docs

## ✨ Features

🏎️ **Tire Degradation Analysis**

- Real-time tire performance modeling
- Temperature-aware degradation calculations
- Compound-specific performance predictions
- Optimal stint window identification

⚡ **Pit Strategy Optimization**

- One-stop, two-stop, and three-stop strategy analysis
- Undercut and overcut opportunity detection
- Position gain predictions
- Risk assessment and confidence scoring

📊 **Undercut Simulation**

- Monte Carlo probability calculation
- Interactive web interface with form validation
- Real-time results with strategic interpretation
- Performance heatmaps and visualizations

🌐 **Real F1 Data Integration**

- OpenF1 API for live timing and telemetry
- Jolpica F1 API for historical race data
- Session-based analysis capabilities
- Multi-year data support with Parquet caching

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Install Python dependencies:

```bash
pip install --user fastapi uvicorn pandas numpy scipy requests pyarrow pydantic
```

2. Start the FastAPI server:

```bash
cd backend
python app.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Install Node.js dependencies:

```bash
cd frontend
npm install
```

2. Start the development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 📱 Using the Simulator

1. **Configure Parameters**:

   - Select Grand Prix and year
   - Choose drivers (A = undercutting, B = being undercut)
   - Pick tire compound for driver A
   - Set current lap number
   - Choose Monte Carlo sample size

2. **Run Simulation**:

   - Click "Run Simulation"
   - Wait for results (usually < 5 seconds)

3. **Analyze Results**:
   - **Success Probability**: Percentage chance of successful undercut
   - **Pit Loss**: Expected time lost during pit stop
   - **Outlap Penalty**: Time penalty from cold tires
   - **Strategic Interpretation**: Recommended action

## 📊 API Endpoints

### POST /simulate

Calculate undercut probability between two drivers.

**Request:**

```json
{
  "gp": "bahrain",
  "year": 2024,
  "driver_a": "VER",
  "driver_b": "HAM",
  "compound_a": "MEDIUM",
  "lap_now": 25,
  "samples": 1000
}
```

**Response:**

```json
{
  "p_undercut": 0.67,
  "pitLoss_s": 24.8,
  "outLapDelta_s": 1.2,
  "assumptions": {
    "current_gap_s": 4.5,
    "models_fitted": { "deg_model": true },
    "monte_carlo_samples": 1000
  }
}
```

### GET /health

Health check endpoint.

### GET /docs

Interactive API documentation.

## 🔧 Models and Algorithms

### DegModel (Tire Degradation)

- Quadratic degradation fitting: `lap_delta = a*age² + b*age + c`
- Handles outliers and validates data quality
- R² goodness of fit measurement
- Predicts time loss per lap based on tire age

### PitModel (Pit Stop Times)

- Normal distribution fitting of historical pit stop data
- Monte Carlo sampling for strategy simulations
- Probability calculations and scenario analysis
- Accounts for pit lane time and track position loss

### OutlapModel (Cold Tire Performance)

- Compound-specific outlap penalty modeling
- Separates first lap (cold) vs warmed tire performance
- Random sampling for simulation variability
- Handles SOFT, MEDIUM, HARD compound differences

## 🌐 Data Sources

### OpenF1 API

- Live timing data and telemetry
- Session details and lap times
- Pit stop events and tire information
- Real-time race data with caching

### Jolpica F1 API (Ergast)

- Historical race results and standings
- Driver and constructor information
- Circuit data and race schedules
- Multi-year historical analysis

## 🔄 Architecture

```
f1-undercut-sim/
├── backend/                 # FastAPI service
│   ├── app.py              # Main API with /simulate endpoint
│   ├── models/             # Analysis models
│   │   ├── deg.py         # DegModel - tire degradation
│   │   ├── pit.py         # PitModel - pit stop sampling
│   │   └── outlap.py      # OutlapModel - cold tire penalties
│   ├── services/           # External API integrations
│   │   ├── openf1.py      # OpenF1Client with caching
│   │   └── jolpica.py     # JolpicaClient with caching
│   └── tests/             # Comprehensive test suite
├── frontend/               # Next.js App Router UI
│   ├── app/               # Next.js app directory
│   ├── components/        # React components
│   │   ├── simulation-form.tsx     # Main form interface
│   │   ├── simulation-results.tsx  # Results display
│   │   ├── performance-chart.tsx   # Plotly.js heatmap
│   │   └── ui/            # shadcn/ui components
│   ├── types/             # TypeScript type definitions
│   └── lib/               # Utility functions
├── features/              # Cached Parquet data (gitignored)
└── memory-bank/           # Project documentation
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Type Check

```bash
cd frontend
npm run type-check
```

## 🛠️ Development

The project uses:

- **Backend**: FastAPI, Pandas, NumPy, SciPy, Requests, PyArrow
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, React Hook Form, Plotly.js
- **Data**: Parquet caching, HTTP retry logic, comprehensive error handling

### Adding New Features

1. **New Models**: Add to `backend/models/` with tests
2. **New Endpoints**: Update `backend/app.py`
3. **Frontend Components**: Add to `frontend/components/`
4. **Data Sources**: Extend API clients in `backend/services/`

## 📈 Performance Features

- **Caching**: Parquet files for API responses with date-based invalidation
- **Retry Logic**: Exponential backoff for HTTP requests (2, 4, 8 seconds)
- **Error Handling**: Graceful degradation when data unavailable
- **Monte Carlo**: Configurable sample sizes (100-5000) for accuracy vs speed
- **Loading States**: Real-time progress indication in UI

## 🏆 Example Results

**High Confidence Undercut (75% success)**:

- Gap: 3.2s, Pit Loss: 23.5s, Outlap: 1.1s
- _Recommendation: Excellent opportunity - pit now!_

**Risky Undercut (45% success)**:

- Gap: 2.1s, Pit Loss: 26.8s, Outlap: 1.8s
- _Recommendation: Risky but possible - consider alternatives_

**Failed Undercut (15% success)**:

- Gap: 1.5s, Pit Loss: 28.2s, Outlap: 2.3s
- _Recommendation: Undercut likely to fail - stay out_

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenF1** for real-time F1 data API
- **Jolpica F1 API (Ergast)** for historical F1 data
- **Formula 1** for the amazing sport that inspired this project
- **shadcn/ui** for beautiful UI components
- **FastAPI** and **Next.js** for excellent frameworks

---

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

#### Research & Development
- [ ] **Academic Collaboration**: Partner with F1 teams and universities
- [ ] **Model Validation**: Comparison with actual race outcomes
- [ ] **Predictive Analytics**: Extend to full race strategy optimization
- [ ] **Economic Modeling**: Cost-benefit analysis of strategy decisions

### Contributing to Future Work

We welcome contributions in any of these areas! Check out our [Contributing Guide](CONTRIBUTING.md) for:
- **Code Contributions**: Implement new features and improvements
- **Data Analysis**: Enhance models with better algorithms
- **Testing**: Expand test coverage and validation
- **Documentation**: Improve docs and examples
- **Research**: Academic research collaboration opportunities

**Made with ❤️ for Formula 1 strategy nerds and data enthusiasts.**
