"""
F1 Undercut Simulator API - Standalone Version for Render
"""
import os
import time
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(
    title="F1 Undercut Simulator API",
    description="F1 race strategy analysis and undercut probability calculations",
    version="1.0.0"
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class SimulationRequest(BaseModel):
    circuit: str
    driver_a: str
    driver_b: str
    compound_a: str
    compound_b: str
    current_lap: int
    session: str = "race"

class SimulationResponse(BaseModel):
    undercut_probability: float
    time_delta: float
    optimal_pit_lap: int
    strategy_recommendation: str
    confidence: float

@app.get("/")
async def root():
    return {
        "message": "F1 Undercut Simulator API",
        "version": "1.0.0",
        "status": "online"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": time.time()}

@app.get("/circuits")
async def get_circuits():
    circuits = [
        "MONACO", "SILVERSTONE", "MONZA", "SPA", "SUZUKA", 
        "SINGAPORE", "BAHRAIN", "IMOLA", "SPAIN", "AUSTRIA"
    ]
    return {"circuits": circuits}

@app.post("/simulate", response_model=SimulationResponse)
async def simulate_undercut(request: SimulationRequest):
    # Mock calculation
    mock_probability = 0.65
    mock_delta = 1.2
    mock_optimal_lap = request.current_lap + 3
    
    return SimulationResponse(
        undercut_probability=mock_probability,
        time_delta=mock_delta,
        optimal_pit_lap=mock_optimal_lap,
        strategy_recommendation=f"Consider undercut on lap {mock_optimal_lap}",
        confidence=0.8
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)