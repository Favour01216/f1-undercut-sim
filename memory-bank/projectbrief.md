# F1 Undercut Simulation - Project Brief

## Project Overview

Advanced Formula 1 undercut strategy simulation and analysis tool that helps teams and enthusiasts analyze tire degradation, optimize pit strategies, and discover undercut opportunities using real F1 data.

## Core Goals

1. **Strategic Analysis**: Provide comprehensive F1 race strategy analysis with focus on undercut opportunities
2. **Real-time Integration**: Connect with OpenF1 API for live timing data and Jolpica F1 API for historical data
3. **Predictive Modeling**: Use tire degradation, pit strategy, and outlap performance models for strategic predictions
4. **Data-Driven Insights**: Transform raw F1 data into actionable strategic intelligence

## Technical Architecture

- **Backend**: FastAPI service with analysis models and external API integrations
- **Frontend**: Next.js React application with modern UI components
- **Data Processing**: Pandas/NumPy for analysis, Parquet for caching
- **APIs**: OpenF1 (live data) and Jolpica F1 (historical data) integrations

## Key Features

- Tire degradation analysis with temperature-aware calculations
- Pit strategy optimization (1-stop, 2-stop, 3-stop scenarios)
- Outlap performance prediction with fuel load impact
- Real F1 data integration with session-based analysis
- Undercut/overcut opportunity detection with confidence scoring

## Success Metrics

- Accurate strategy predictions with measurable confidence intervals
- Real-time data processing with sub-second response times
- Historical analysis capabilities across multiple seasons
- User-friendly interface for complex F1 strategy analysis
