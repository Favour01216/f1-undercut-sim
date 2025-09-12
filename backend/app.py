"""
F1 Undercut Simulation FastAPI Application

This is the main FastAPI application for the F1 undercut simulation tool.
It provides APIs for tire degradation analysis, pit stop optimization,
and outlap performance prediction.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from typing import Dict, Any

# Import models and services
from models.deg import TireDegradationModel
from models.pit import PitStopModel
from models.outlap import OutlapModel
from services.openf1 import OpenF1Service
from services.jolpica import JolpicaService

# Initialize FastAPI app
app = FastAPI(
    title="F1 Undercut Simulator",
    description="API for F1 undercut simulation and analysis",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
openf1_service = OpenF1Service()
jolpica_service = JolpicaService()

# Initialize models
tire_deg_model = TireDegradationModel()
pit_stop_model = PitStopModel()
outlap_model = OutlapModel()


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint providing API information."""
    return {
        "message": "F1 Undercut Simulator API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "f1-undercut-sim-backend"}


@app.get("/api/v1/sessions")
async def get_sessions(year: int = 2024) -> Dict[str, Any]:
    """Get available F1 sessions for a given year."""
    try:
        sessions = await openf1_service.get_sessions(year)
        return {"sessions": sessions, "year": year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/tire-degradation/{session_key}")
async def analyze_tire_degradation(session_key: str) -> Dict[str, Any]:
    """Analyze tire degradation for a specific session."""
    try:
        # Get session data from OpenF1
        session_data = await openf1_service.get_session_data(session_key)
        
        # Analyze tire degradation
        degradation_analysis = tire_deg_model.analyze(session_data)
        
        return {
            "session_key": session_key,
            "analysis": degradation_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pit-strategy")
async def optimize_pit_strategy(strategy_request: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize pit stop strategy for given conditions."""
    try:
        optimization = pit_stop_model.optimize(strategy_request)
        return {"optimization": optimization}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/outlap-prediction/{session_key}")
async def predict_outlap_performance(
    session_key: str, 
    tire_compound: str,
    fuel_load: float
) -> Dict[str, Any]:
    """Predict outlap performance for given conditions."""
    try:
        prediction = outlap_model.predict(session_key, tire_compound, fuel_load)
        return {
            "session_key": session_key,
            "tire_compound": tire_compound,
            "fuel_load": fuel_load,
            "prediction": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the application
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )