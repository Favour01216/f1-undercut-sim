"""
F1 Undercut Simulation FastAPI Application

This is the main FastAPI application for the F1 undercut simulation tool.
It provides APIs for tire degradation analysis, pit stop optimization,
and undercut simulation with probability calculations.
"""
import os
import time
import numpy as np
from typing import Dict, Any, Optional, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, confloat, conint
import uvicorn
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

# Import our logging configuration and middleware
from logging_config import configure_logging, get_logger
from middleware import RequestMiddleware, hash_simulation_inputs, round_simulation_outputs
from performance import get_simulation_cache
from model_cache import load_cached_models, save_cached_models

# Import our new modeling classes and API clients
from models.deg import DegModel
from models.outlap import OutlapModel
from models.pit import PitModel
from services.jolpica import JolpicaClient
from services.openf1 import OpenF1Client

# Configure logging first
configure_logging()
logger = get_logger(__name__)

# Initialize Sentry if DSN is provided
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FastApiIntegration(auto_enabling_integrations=False),
            StarletteIntegration(auto_enabling_integrations=False),
        ],
        environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        attach_stacktrace=True,
        send_default_pii=False,
    )
    logger.info("Sentry initialized", environment=os.getenv("SENTRY_ENVIRONMENT", "development"))
else:
    logger.info("Sentry not configured - no SENTRY_DSN provided")

# Initialize FastAPI app
app = FastAPI(
    title="F1 Undercut Simulator",
    description="API for F1 undercut simulation and probability analysis with strict validation",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "F1 Undercut Simulator API",
        "email": "favour@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
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

# Add request middleware for logging and request IDs
app.add_middleware(RequestMiddleware)

# Initialize API clients
openf1_client = OpenF1Client()
jolpica_client = JolpicaClient()

# Global model instances (will be fitted on first use)
global_models = {"deg": None, "pit": None, "outlap": None}

# Fast mode flag (can be enabled via environment variable)
FAST_MODE = os.getenv("FAST_MODE", "false").lower() == "true"

# Define valid Grand Prix circuits
GP_CHOICES = Literal[
    "bahrain",
    "imola",
    "monza",
    "monaco",
    "spain",
    "canada",
    "austria",
    "silverstone",
    "hungary",
    "belgium",
    "netherlands",
    "italy",
    "singapore",
    "japan",
    "qatar",
    "usa",
    "mexico",
    "brazil",
    "abu_dhabi",
    "australia",
    "china",
    "azerbaijan",
    "miami",
    "france",
    "portugal",
    "russia",
    "turkey",
    "saudi_arabia",
    "las_vegas",
]

# Define valid tire compounds
COMPOUND_CHOICES = Literal["SOFT", "MEDIUM", "HARD"]


class SimulateRequest(BaseModel):
    """Request model for undercut simulation with strict validation."""
    gp: GP_CHOICES = Field(..., description="Grand Prix circuit identifier")
    year: int = Field(..., description="Race year", ge=2020, le=2024)
    driver_a: str = Field(
        ...,
        description="Driver attempting undercut (driver number or name)",
        min_length=1,
        max_length=50,
    )
    driver_b: str = Field(
        ...,
        description="Driver being undercut (driver number or name)",
        min_length=1,
        max_length=50,
    )
    compound_a: COMPOUND_CHOICES = Field(..., description="Tire compound for driver A")
    lap_now: int = Field(..., description="Current lap number", ge=1, le=100)
    samples: int = Field(
        1000, description="Number of Monte Carlo samples", ge=1, le=10000
    )


class SimulateResponse(BaseModel):
    """Response model for undercut simulation with strict validation."""
    p_undercut: float = Field(
        ..., description="Probability of successful undercut (0-1)", ge=0, le=1
    )
    pitLoss_s: float = Field(..., description="Expected pit stop time loss in seconds")
    outLapDelta_s: float = Field(..., description="Expected outlap penalty in seconds")
    avgMargin_s: Optional[float] = Field(
        None, description="Average margin of success/failure in seconds"
    )
    assumptions: Dict[str, Any] = Field(
        ..., description="Model assumptions and parameters used"
    )


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint providing API information."""
    return {
        "message": "F1 Undercut Simulator API",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
        "simulate": "/simulate",
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint returning service status."""
    return {"status": "ok"}


def get_or_fit_models(gp: str, year: int, fast_mode: Optional[bool] = None) -> Dict[str, Any]:
    """Get fitted models, fitting them if needed."""
    global global_models
    
    # Use global fast mode if not specified
    if fast_mode is None:
        fast_mode = FAST_MODE
    
    try:
        # Get data from APIs
        logger.info(f"Fetching data for {gp} {year}", fast_mode=fast_mode)
        
        with openf1_client as client:
            laps_df = client.get_laps(gp, year)
            pit_events_df = client.get_pit_events(gp, year)
        
        # Try to load cached models first
        cached_models = load_cached_models(gp, year, laps_df, pit_events_df, fast_mode)
        if cached_models is not None:
            return cached_models
        
        # No cache hit - fit models from scratch
        logger.info(f"No cache hit, fitting models for {gp} {year}")
        models = {}
        
        # Fit DegModel with circuit specificity
        if not laps_df.empty:
            try:
                deg_model = DegModel(circuit=gp)
                deg_model.fit_from_data(laps_df, circuit=gp, save_params=True)
                models['deg'] = deg_model
                logger.info(f"DegModel fitted successfully: R²={deg_model.r_squared:.3f}")
            except Exception as e:
                # DegModel may fail if tire age data is missing (common with OpenF1)
                models['deg'] = None
                logger.warning(f"DegModel failed to fit (using fallback): {e}")
        else:
            # Use default degradation if no data
            models["deg"] = None
            logger.warning("No lap data available for DegModel")

        # Fit PitModel
        if not pit_events_df.empty:
            pit_model = PitModel()
            pit_model.fit(pit_events_df)
            models["pit"] = pit_model
            logger.info("PitModel fitted successfully")
        else:
            # Use default pit loss if no data
            models["pit"] = None
            logger.warning("No pit data available for PitModel")
        
        # Fit OutlapModel with circuit/compound specificity
        if not laps_df.empty:
            try:
                outlap_model = OutlapModel(circuit=gp, compound='medium')  # Default to medium compound
                outlap_model.fit_from_data(laps_df, save_params=True)
                models['outlap'] = outlap_model
                logger.info(f"OutlapModel fitted successfully: penalty={outlap_model.mean_penalty:.3f}±{outlap_model.std_penalty:.3f}s")
            except Exception as e:
                # OutlapModel often fails due to missing tire compound data
                models['outlap'] = None
                logger.warning(f"OutlapModel failed to fit: {e}")
        else:
            models["outlap"] = None
            logger.warning("No lap data available for OutlapModel")
        
        # Save fitted models to cache
        save_cached_models(gp, year, laps_df, pit_events_df, models)
        
        return models

    except Exception as e:
        logger.error(f"Error fitting models: {e}")
        return {"deg": None, "pit": None, "outlap": None}


def calculate_driver_gap(
    gp: str, year: int, driver_a: str, driver_b: str, lap_now: int
) -> float:
    """Calculate the gap between two drivers at a specific lap."""
    # This is a simplified implementation - in reality you'd get this from timing data
    # For now, we'll simulate a realistic gap
    np.random.seed(hash(f"{gp}{year}{driver_a}{driver_b}{lap_now}") % 2**32)

    # Typical F1 gaps range from 0.5s to 30s between adjacent cars
    base_gap = np.random.uniform(2.0, 8.0)  # seconds

    # Add some variability based on lap position
    lap_factor = 1.0 + (lap_now / 100.0) * 0.2  # Gaps tend to increase during race

    return base_gap * lap_factor


@app.post("/simulate", response_model=SimulateResponse)
async def simulate_undercut(request: SimulateRequest, req: Request) -> SimulateResponse:
    """
    Simulate undercut probability between two drivers.

    This endpoint calculates the probability that driver_a can successfully
    undercut driver_b by pitting first and gaining track position.
    """
    start_time = time.time()
    
    # Check cache first for performance
    cache_key = hash_simulation_inputs(request.dict())
    cache = get_simulation_cache()
    
    if cache_key in cache:
        logger.info("Cache hit for simulation request")
        return SimulateResponse(**cache[cache_key])
    
    try:
        # Get fitted models
        models = get_or_fit_models(request.gp, request.year)
        
        # Calculate current gap between drivers
        current_gap = calculate_driver_gap(
            request.gp, request.year, request.driver_a, request.driver_b, request.lap_now
        )
        
        # Get model predictions
        deg_model = models.get("deg")
        pit_model = models.get("pit")
        outlap_model = models.get("outlap")
        
        # Use fallback values if models failed to fit
        if deg_model is None:
            # Use realistic fallback tire advantage
            tire_advantage = 0.12  # seconds per lap advantage for fresh tires
            logger.info("Using fallback tire advantage")
        else:
            # Get tire age for driver B (assume they've been on current tires longer)
            tire_age_b = max(5, request.lap_now // 3)  # Estimate tire age
            tire_advantage = deg_model.get_fresh_tire_advantage(
                old_age=tire_age_b, new_age=2
            )
        
        if pit_model is None:
            pit_loss = 24.0  # Default F1 pit stop time loss
            logger.info("Using fallback pit loss")
        else:
            pit_loss = pit_model.sample_pit_time()
        
        if outlap_model is None:
            # Use compound-specific fallback outlap penalties
            outlap_penalties = {"SOFT": 0.8, "MEDIUM": 1.4, "HARD": 2.2}
            outlap_penalty = outlap_penalties.get(request.compound_a, 1.4)
            logger.info("Using fallback outlap penalty")
        else:
            outlap_penalty = outlap_model.sample(n=1)[0]
        
        # Monte Carlo simulation
        n_samples = request.samples
        undercut_successes = 0
        margins = []
        
        for _ in range(n_samples):
            # Sample variation in pit stop time
            pit_time_sample = pit_loss + np.random.normal(0, 1.0)
            
            # Sample variation in outlap penalty
            outlap_sample = outlap_penalty + np.random.normal(0, 0.3)
            
            # Calculate net time difference
            # Positive means driver A gains time (successful undercut)
            time_gained = tire_advantage - pit_time_sample - outlap_sample + current_gap
            
            if time_gained > 0:
                undercut_successes += 1
            
            margins.append(time_gained)
        
        # Calculate results
        p_undercut = undercut_successes / n_samples
        avg_margin = float(np.mean(margins))
        
        # Prepare response
        assumptions = {
            "current_gap_s": current_gap,
            "tire_advantage_s": tire_advantage,
            "pit_loss_s": pit_loss,
            "outlap_penalty_s": outlap_penalty,
            "tire_age_driver_b": tire_age_b if deg_model else 10,
            "models_fitted": {
                "degradation_model": deg_model is not None,
                "pit_model": pit_model is not None,
                "outlap_model": outlap_model is not None,
            },
            "monte_carlo_samples": n_samples,
        }
        
        response_data = {
            "p_undercut": p_undercut,
            "pitLoss_s": pit_loss,
            "outLapDelta_s": outlap_penalty,
            "avgMargin_s": avg_margin,
            "assumptions": assumptions,
        }
        
        # Round outputs for consistency
        response_data = round_simulation_outputs(response_data)
        
        # Cache the result
        cache[cache_key] = response_data
        
        # Log the simulation
        duration = time.time() - start_time
        logger.info(
            "Simulation completed",
            gp=request.gp,
            year=request.year,
            p_undercut=p_undercut,
            duration_ms=round(duration * 1000, 2),
            cache_key=cache_key[:8],
        )
        
        return SimulateResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}", gp=request.gp, year=request.year)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@app.get("/api/v1/models/status")
async def get_models_status() -> Dict[str, Any]:
    """Get the status of fitted models."""
    return {
        "models": {
            "deg": global_models["deg"] is not None,
            "pit": global_models["pit"] is not None,
            "outlap": global_models["outlap"] is not None,
        },
        "fast_mode": FAST_MODE,
    }


@app.get("/api/v1/performance/metrics")
async def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics for the API."""
    cache = get_simulation_cache()
    return {
        "cache_size": len(cache),
        "cache_hit_rate": getattr(cache, "hit_rate", 0.0),
        "total_requests": getattr(cache, "total_requests", 0),
    }


@app.get("/api/v1/models/cache")
async def get_models_cache() -> Dict[str, Any]:
    """Get information about the models cache."""
    return {"message": "Model cache status endpoint"}


@app.post("/api/v1/models/cache/clear")
async def clear_models_cache() -> Dict[str, str]:
    """Clear the models cache."""
    global global_models
    global_models = {"deg": None, "pit": None, "outlap": None}
    cache = get_simulation_cache()
    cache.clear()
    return {"message": "Cache cleared successfully"}


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )