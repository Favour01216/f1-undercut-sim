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
    # Frontend sends these field names
    gp: str  # Circuit name from frontend
    driver_a: str
    driver_b: str
    compound_a: str
    lap_now: int  # Current lap from frontend
    
    # Optional fields that frontend might send
    year: int = 2024
    samples: int = 1000
    H: int = 2
    p_pit_next: float = 1.0
    compound_b: str = "MEDIUM"  # Default if not provided
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

@app.get("/simulate")
async def simulate_undercut_get(
    strategy1: str = "one_stop",
    strategy2: str = "two_stop", 
    circuit: str = "monza"
):
    """GET endpoint for browser testing"""
    # Mock calculation based on strategies
    mock_probability = 0.72 if strategy1 == "one_stop" else 0.45
    mock_delta = 1.8 if circuit.lower() == "monza" else 2.1
    
    return {
        "undercut_probability": mock_probability,
        "time_delta": mock_delta,
        "optimal_pit_lap": 18,
        "strategy_recommendation": f"Undercut viable with {strategy1} vs {strategy2} at {circuit}",
        "confidence": 0.85,
        "circuit": circuit,
        "strategies": {"strategy1": strategy1, "strategy2": strategy2}
    }

@app.post("/simulate", response_model=SimulationResponse)
async def simulate_undercut_post(request: SimulationRequest):
    """POST endpoint for API clients"""
    # Use the frontend field names directly
    circuit = request.gp
    current_lap = request.lap_now
    
    # Mock calculation based on inputs
    mock_probability = 0.75 if circuit.lower() == "monza" else 0.65
    mock_delta = 1.8 if request.driver_a == "VER" else 1.2
    mock_optimal_lap = current_lap + 3
    
    return SimulationResponse(
        undercut_probability=mock_probability,
        time_delta=mock_delta,
        optimal_pit_lap=mock_optimal_lap,
        strategy_recommendation=f"Undercut {request.driver_a} vs {request.driver_b} at {circuit} on lap {mock_optimal_lap}",
        confidence=0.85
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)