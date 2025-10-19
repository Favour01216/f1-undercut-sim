"""
F1 Undercut Simulation FastAPI Application - Minimal Version for Render

This is a minimal version for deployment testing.
"""
import os
import time
from typing import Dict, Any, Optional, Literal, List, Tuple

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="F1 Undercut Simulator API",
    description="A comprehensive API for F1 race strategy analysis and undercut probability calculations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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

# Request models
class SimulationRequest(BaseModel):
    circuit: str = Field(..., description="Circuit name (e.g., 'MONACO', 'SILVERSTONE')")
    driver_a: str = Field(..., description="First driver name")
    driver_b: str = Field(..., description="Second driver name") 
    compound_a: str = Field(..., description="Tire compound for driver A")
    compound_b: str = Field(..., description="Tire compound for driver B")
    current_lap: int = Field(..., ge=1, le=100, description="Current lap number")
    session: str = Field(default="race", description="Session type")

class SimulationResponse(BaseModel):
    undercut_probability: float = Field(..., description="Probability of successful undercut")
    time_delta: float = Field(..., description="Expected time delta in seconds")
    optimal_pit_lap: int = Field(..., description="Optimal pit lap")
    strategy_recommendation: str = Field(..., description="Strategy recommendation")
    confidence: float = Field(..., description="Confidence level")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "ok", "timestamp": time.time()}

# Circuits endpoint
@app.get("/circuits")
async def get_circuits():
    """Get list of supported circuits"""
    circuits = [
        "MONACO", "SILVERSTONE", "MONZA", "SPA", "SUZUKA", 
        "SINGAPORE", "BAHRAIN", "IMOLA", "SPAIN", "AUSTRIA"
    ]
    return {"circuits": circuits}

# Main simulation endpoint (mock for now)
@app.post("/simulate", response_model=SimulationResponse)
async def simulate_undercut(request: SimulationRequest):
    """
    Simulate undercut probability (mock implementation for deployment testing)
    """
    logger.info(f"Simulation request: {request}")
    
    # Mock calculation for now
    mock_probability = 0.65
    mock_delta = 1.2
    mock_optimal_lap = request.current_lap + 3
    
    return SimulationResponse(
        undercut_probability=mock_probability,
        time_delta=mock_delta,
        optimal_pit_lap=mock_optimal_lap,
        strategy_recommendation=f"Mock: Consider undercut on lap {mock_optimal_lap}",
        confidence=0.8
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "F1 Undercut Simulator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)