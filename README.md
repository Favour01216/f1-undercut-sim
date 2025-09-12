# F1 Undercut Simulator

Advanced Formula 1 undercut strategy simulation and analysis tool that helps teams and enthusiasts analyze tire degradation, optimize pit strategies, and discover undercut opportunities using real F1 data.

## Features

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

📊 **Outlap Performance Prediction**
- Fresh tire performance modeling
- Fuel load impact calculations
- Tire warm-up time estimation
- Track evolution considerations

🌐 **Real F1 Data Integration**
- OpenF1 API for live timing and telemetry
- Jolpica F1 API for historical race data
- Session-based analysis capabilities
- Multi-year data support

## Architecture

```
f1-undercut-sim/
├── backend/                 # FastAPI service
│   ├── app.py              # Main FastAPI application
│   ├── models/             # Analysis models
│   │   ├── deg.py         # Tire degradation model
│   │   ├── pit.py         # Pit strategy model
│   │   └── outlap.py      # Outlap performance model
│   ├── services/           # External API integrations
│   │   ├── openf1.py      # OpenF1 API client
│   │   └── jolpica.py     # Jolpica F1 API client
│   └── tests/             # Backend tests
├── frontend/               # Next.js UI (App Router)
│   ├── app/               # Next.js app directory
│   ├── components/        # Reusable UI components
│   └── lib/               # Frontend utilities
├── features/              # Cached Parquet data (gitignored)
├── notebooks/             # Jupyter notebooks for analysis
└── .github/workflows/     # CI/CD pipelines
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Install Python dependencies:
```bash
pip install -e ".[dev]"
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the FastAPI server:
```bash
cd backend
python app.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Install Node.js dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Documentation

### Endpoints

#### Sessions
- `GET /api/v1/sessions?year={year}` - Get available F1 sessions

#### Tire Analysis
- `GET /api/v1/tire-degradation/{session_key}` - Analyze tire degradation

#### Strategy Optimization
- `POST /api/v1/pit-strategy` - Optimize pit stop strategy

#### Outlap Prediction
- `GET /api/v1/outlap-prediction/{session_key}` - Predict outlap performance

### Example Request

```javascript
// Optimize pit strategy
const response = await fetch('/api/v1/pit-strategy', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    current_position: 8,
    current_lap: 15,
    total_laps: 50,
    current_tire: 'MEDIUM',
    tire_age: 12,
    fuel_load: 45.0,
    weather: 'dry',
    traffic_density: 0.6
  })
})
```

## Development

### Running Tests

Backend tests:
```bash
pytest backend/tests/ -v
```

Frontend type checking:
```bash
npm run type-check
```

### Code Quality

The project uses:
- **Ruff** for Python linting and formatting
- **Black** for Python code formatting
- **ESLint** for TypeScript/React linting
- **Prettier** for frontend code formatting

Run linting:
```bash
# Backend
ruff check backend/
black backend/

# Frontend
npm run lint
```

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pre-commit install
```

This ensures code quality checks run automatically before commits.

## Data Sources

### OpenF1 API
- Live timing data
- Telemetry information
- Session details
- Real-time race data

### Jolpica F1 API
- Historical race results
- Driver and constructor standings
- Circuit information
- Multi-year race data

## Models and Algorithms

### Tire Degradation Model
- Exponential degradation curves
- Temperature impact factors
- Compound-specific characteristics
- Performance prediction algorithms

### Pit Strategy Optimizer
- Position gain calculations
- Traffic density analysis
- Undercut opportunity detection
- Multi-stop strategy evaluation

### Outlap Performance Predictor
- Fresh tire performance modeling
- Fuel load impact calculations
- Track evolution considerations
- Confidence interval estimation

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Deployment

### Backend Deployment

The FastAPI backend can be deployed using:
- Docker containers
- Cloud platforms (AWS, GCP, Azure)
- Serverless functions

### Frontend Deployment

The Next.js frontend can be deployed to:
- Vercel (recommended)
- Netlify
- AWS Amplify
- Docker containers

### Environment Variables

Required environment variables:
```bash
# Backend
API_HOST=localhost
API_PORT=8000
DEBUG=True
OPENF1_API_URL=https://api.openf1.org/v1
JOLPICA_API_URL=https://jolpica-f1-api.com/v1

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Performance Considerations

- **Caching**: Implement Redis for API response caching
- **Database**: Consider PostgreSQL for persistent data storage
- **CDN**: Use CDN for static assets and frontend deployment
- **Rate Limiting**: Implement rate limiting for external API calls

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **OpenF1** for providing real-time F1 data API
- **Jolpica F1 API** for historical F1 data
- **Formula 1** for the amazing sport that inspired this project
- **shadcn/ui** for the beautiful UI components
- **FastAPI** and **Next.js** communities for excellent frameworks

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/Favour01216/f1-undercut-sim/issues) page
2. Create a new issue with detailed information
3. Join our community discussions

## Roadmap

- [ ] Machine learning-enhanced predictions
- [ ] Real-time race strategy recommendations
- [ ] Driver performance analysis
- [ ] Weather impact modeling
- [ ] Mobile app development
- [ ] Integration with more F1 data sources

---

Made with ❤️ for Formula 1 enthusiasts and strategy nerds.