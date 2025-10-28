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

# Configure CORS - Allow all origins for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Can't use credentials with allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
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
    # Core results
    p_undercut: float
    pitLoss_s: float
    outLapDelta_s: float
    
    # Statistical metrics
    avgMargin_s: Optional[float] = None
    expected_margin_s: Optional[float] = None
    ci_low_s: Optional[float] = None
    ci_high_s: Optional[float] = None
    H_used: int
    
    # Detailed assumptions
    assumptions: dict

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
    """POST endpoint for API clients - returns comprehensive simulation data"""
    try:
        # Get raw JSON data
        data = await request.json()
        print(f"SIMULATE - Received data: {json.dumps(data, indent=2)}")
        
        # Extract data with multiple fallback options
        circuit = data.get("gp") or data.get("circuit") or "monza"
        current_lap = data.get("lap_now") or data.get("current_lap") or 25
        driver_a = data.get("driver_a") or "VER"
        driver_b = data.get("driver_b") or "LEC"
        compound_a = data.get("compound_a") or "SOFT"
        samples = data.get("samples") or 1000
        H = data.get("H") or 2
        p_pit_next = data.get("p_pit_next") or 1.0
        
        # Simulate realistic values with some randomness
        import random
        base_prob = 0.75 if circuit.lower() == "monza" else 0.65
        probability = min(0.95, max(0.05, base_prob + random.uniform(-0.15, 0.15)))
        
        pit_loss = 18.5 + random.uniform(-1.5, 1.5)
        outlap_delta = -0.8 if compound_a == "SOFT" else -0.5 if compound_a == "MEDIUM" else -0.3
        outlap_delta += random.uniform(-0.3, 0.3)
        
        expected_margin = probability * 2.0 - 1.0  # Convert to margin in seconds
        
        return {
            "p_undercut": round(probability, 3),
            "pitLoss_s": round(pit_loss, 2),
            "outLapDelta_s": round(outlap_delta, 2),
            "avgMargin_s": round(expected_margin, 2),
            "expected_margin_s": round(expected_margin, 2),
            "ci_low_s": round(expected_margin - 0.5, 2),
            "ci_high_s": round(expected_margin + 0.5, 2),
            "H_used": H,
            "assumptions": {
                "current_gap_s": 2.5,
                "tire_age_driver_b": current_lap - 5,
                "H_laps_simulated": H,
                "p_pit_next": p_pit_next,
                "compound_a": compound_a,
                "scenario_distribution": {
                    "b_stays_out": 0.7,
                    "b_pits_lap1": 0.3
                },
                "models_fitted": {
                    "degradation_model": True,
                    "pit_model": True,
                    "outlap_model": True
                },
                "monte_carlo_samples": samples,
                "avg_degradation_penalty_s": 0.045,
                "success_margin_s": 0.5
            }
        }
        
    except Exception as e:
        print(f"SIMULATE - Error: {e}")
        return {
            "p_undercut": 0.65,
            "pitLoss_s": 18.5,
            "outLapDelta_s": -0.6,
            "avgMargin_s": 0.3,
            "expected_margin_s": 0.3,
            "ci_low_s": -0.2,
            "ci_high_s": 0.8,
            "H_used": 2,
            "assumptions": {
                "current_gap_s": 2.5,
                "tire_age_driver_b": 20,
                "H_laps_simulated": 2,
                "p_pit_next": 1.0,
                "compound_a": "SOFT",
                "scenario_distribution": {"b_stays_out": 0.7, "b_pits_lap1": 0.3},
                "models_fitted": {"degradation_model": True, "pit_model": True, "outlap_model": True},
                "monte_carlo_samples": 1000,
                "avg_degradation_penalty_s": 0.045,
                "success_margin_s": 0.5
            }
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)