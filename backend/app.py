"""
F1 Undercut Simulator API - Standalone Version for Render
"""
import os
import time
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

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

# Request/Response models - Accept any data structure
from typing import Optional, Any

class SimulationRequest(BaseModel):
    # Make everything optional to handle any frontend format
    gp: Optional[str] = None
    circuit: Optional[str] = None
    driver_a: Optional[str] = "VER"
    driver_b: Optional[str] = "LEC"
    compound_a: Optional[str] = "SOFT"
    compound_b: Optional[str] = "MEDIUM"
    lap_now: Optional[int] = None
    current_lap: Optional[int] = None
    
    # Accept any other fields frontend might send
    year: Optional[int] = 2024
    samples: Optional[int] = 1000
    H: Optional[int] = 2
    p_pit_next: Optional[float] = 1.0
    session: Optional[str] = "race"
    
    # Accept any additional fields
    class Config:
        extra = "allow"

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

@app.post("/debug")
async def debug_request(request: Request):
    """Debug endpoint to see what data is being sent"""
    try:
        body = await request.json()
        print(f"DEBUG - Received data: {json.dumps(body, indent=2)}")
        return {"received": body, "status": "debug_ok"}
    except Exception as e:
        print(f"DEBUG - Error parsing request: {e}")
        return {"error": str(e), "status": "debug_error"}

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

@app.post("/simulate")
async def simulate_undercut_post(request: Request):
    """POST endpoint for API clients - accepts any JSON"""
    try:
        # Get raw JSON data
        data = await request.json()
        print(f"SIMULATE - Received data: {json.dumps(data, indent=2)}")
        
        # Extract data with multiple fallback options
        circuit = data.get("gp") or data.get("circuit") or "monza"
        current_lap = data.get("lap_now") or data.get("current_lap") or 25
        driver_a = data.get("driver_a") or "VER"
        driver_b = data.get("driver_b") or "LEC"
        
        # Mock calculation
        mock_probability = 0.75 if circuit.lower() == "monza" else 0.65
        mock_delta = 1.8 if driver_a == "VER" else 1.2
        mock_optimal_lap = current_lap + 3
        
        return {
            "undercut_probability": mock_probability,
            "time_delta": mock_delta,
            "optimal_pit_lap": mock_optimal_lap,
            "strategy_recommendation": f"Undercut {driver_a} vs {driver_b} at {circuit} on lap {mock_optimal_lap}",
            "confidence": 0.85
        }
        
    except Exception as e:
        print(f"SIMULATE - Error: {e}")
        return {
            "error": str(e),
            "undercut_probability": 0.65,
            "time_delta": 1.5,
            "optimal_pit_lap": 25,
            "strategy_recommendation": "Default simulation result",
            "confidence": 0.5
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)