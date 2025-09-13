"""
F1 Undercut Simulation FastAPI Application

This is the main FastAPI application for the F1 undercut simulation tool.
It provides APIs for tire degradation analysis, pit stop optimization,
and undercut simulation with probability calculations.
"""

import os
import time
import numpy as np
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
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
from models.pit import PitModel  
from models.outlap import OutlapModel
from services.openf1 import OpenF1Client
from services.jolpica import JolpicaClient

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
        send_default_pii=False,  # Don't send PII by default
    )
    logger.info("Sentry initialized", environment=os.getenv("SENTRY_ENVIRONMENT", "development"))
else:
    logger.info("Sentry not configured - no SENTRY_DSN provided")

# Initialize FastAPI app
app = FastAPI(
    title="F1 Undercut Simulator",
    description="API for F1 undercut simulation and probability analysis",
    version="0.2.0",
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

# Add request middleware for logging and request IDs
app.add_middleware(RequestMiddleware)

# Initialize API clients
openf1_client = OpenF1Client()
jolpica_client = JolpicaClient()

# Global model instances (will be fitted on first use)
global_models = {
    'deg': None,
    'pit': None, 
    'outlap': None
}

# Fast mode flag (can be enabled via environment variable)
FAST_MODE = os.getenv("FAST_MODE", "false").lower() == "true"


class SimulateRequest(BaseModel):
    """Request model for undercut simulation."""
    gp: str = Field(..., description="Grand Prix identifier (e.g., 'bahrain', 'monaco')")
    year: int = Field(..., description="Race year", ge=2020, le=2024)
    driver_a: str = Field(..., description="Driver attempting undercut (driver number or name)")
    driver_b: str = Field(..., description="Driver being undercut (driver number or name)")  
    compound_a: str = Field(..., description="Tire compound for driver A", pattern="^(SOFT|MEDIUM|HARD)$")
    lap_now: int = Field(..., description="Current lap number", ge=1, le=100)
    samples: Optional[int] = Field(1000, description="Number of Monte Carlo samples", ge=100, le=10000)


class SimulateResponse(BaseModel):
    """Response model for undercut simulation."""
    p_undercut: float = Field(..., description="Probability of successful undercut (0-1)")
    pitLoss_s: float = Field(..., description="Expected pit stop time loss in seconds")
    outLapDelta_s: float = Field(..., description="Expected outlap penalty in seconds") 
    assumptions: Dict[str, Any] = Field(..., description="Model assumptions and parameters used")


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint providing API information."""
    return {
        "message": "F1 Undercut Simulator API",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
        "simulate": "/simulate"
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "f1-undercut-sim-backend"}


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
            models['deg'] = None
            logger.warning("No lap data available for DegModel")
        
        # Fit PitModel  
        if not pit_events_df.empty:
            pit_model = PitModel()
            pit_model.fit(pit_events_df)
            models['pit'] = pit_model
            logger.info("PitModel fitted successfully")
        else:
            # Use default pit loss if no data
            models['pit'] = None
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
            models['outlap'] = None
            logger.warning("No lap data available for OutlapModel")
        
        # Save fitted models to cache
        save_cached_models(gp, year, laps_df, pit_events_df, models)
        
        return models
        
    except Exception as e:
        logger.error(f"Error fitting models: {e}")
        return {'deg': None, 'pit': None, 'outlap': None}


def calculate_driver_gap(gp: str, year: int, driver_a: str, driver_b: str, lap_now: int) -> float:
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
    undercut driver_b by pitting now while driver_b stays out one more lap.
    """
    # Start timing for detailed logging
    start_time = time.time()
    
    # Hash inputs for privacy-safe logging
    request_dict = request.dict()
    input_hash = hash_simulation_inputs(request_dict)
    
    # Get cache instance
    cache = get_simulation_cache()
    
    try:
        # Calculate current gap between drivers first (for cache key)
        gap_seconds = calculate_driver_gap(
            request.gp, request.year, request.driver_a, request.driver_b, request.lap_now
        )
        
        # Check cache first
        cached_result = cache.get(
            request.gp, request.year, request.driver_a, request.driver_b, 
            request.compound_a, request.lap_now, request.samples, gap_seconds
        )
        
        if cached_result is not None:
            # Cache hit - return cached result
            duration_ms = round((time.time() - start_time) * 1000, 2)
            cache.add_request_time(duration_ms)
            
            logger.info(
                "Cache hit for simulation",
                input_hash=input_hash,
                duration_ms=duration_ms,
                cache_stats=cache.get_cache_stats()
            )
            
            return SimulateResponse(**cached_result)
        
        # Cache miss - perform simulation
        logger.info(
            "Starting undercut simulation",
            gp=request.gp,
            year=request.year,
            compound=request.compound_a,
            lap=request.lap_now,
            samples=request.samples,
            input_hash=input_hash
        )
        
        # Get fitted models for this GP/year
        models = get_or_fit_models(request.gp, request.year)
        
        # Default assumptions
        assumptions = {
            "current_gap_s": gap_seconds,
            "tire_age_driver_b": request.lap_now - 1,  # Assume current stint started at lap 1
            "models_fitted": {
                "deg_model": models['deg'] is not None,
                "pit_model": models['pit'] is not None, 
                "outlap_model": models['outlap'] is not None
            },
            "monte_carlo_samples": request.samples
        }
        
        # Monte Carlo simulation with deterministic RNG
        rng = np.random.default_rng(42)  # Deterministic seed for reproducible results
        successes = 0
        pit_losses = []
        outlap_deltas = []
        degradation_penalties = []
        
        for _ in range(request.samples):
            # Sample pit stop time loss
            if models['pit'] is not None and models['pit'].fitted:
                pit_loss = models['pit'].sample(1, rng=rng)
            else:
                # Default F1 pit stop loss: ~25 seconds ± 3s
                pit_loss = rng.normal(25.0, 3.0)
            
            pit_losses.append(pit_loss)
            
            # Sample outlap penalty 
            if models['outlap'] is not None and models['outlap'].fitted:
                outlap_delta = models['outlap'].sample(n=1, rng=rng)
            else:
                # Fallback to default outlap penalty (realistic F1 outlap slowdown)
                outlap_delta = rng.normal(1.0, 0.3)
            
            outlap_deltas.append(max(0, outlap_delta))
            
            # Predict driver B's degradation for staying out 1 more lap
            current_tire_age = assumptions["tire_age_driver_b"]
            if (models['deg'] is not None and models['deg'].fitted and 
                hasattr(models['deg'], 'r_squared') and models['deg'].r_squared > 0.1):
                # Use fitted model if it has reasonable predictive power
                degradation_penalty = models['deg'].predict(current_tire_age + 1) - models['deg'].predict(current_tire_age)
            else:
                # Use realistic default degradation when model is poor
                # Typical F1 degradation: 0.05-0.2s per lap, increasing with tire age
                base_degradation = 0.08  # seconds per lap
                age_factor = 1 + (current_tire_age / 20)  # increases with age
                degradation_penalty = base_degradation * age_factor
            
            degradation_penalties.append(max(0, degradation_penalty))
            
            # Calculate undercut success using proper multi-lap physics
            # 
            # Undercut scenario:
            # - Driver A pits now and loses pit_loss + outlap_penalty time immediately
            # - Driver B stays out for N more laps, losing degradation_penalty per lap
            # - Driver A has fresh tires with significant initial advantage
            # - Success if Driver A catches up within reasonable stint length (5-8 laps)
            
            driver_a_immediate_loss = pit_loss + outlap_delta
            
            # Model performance over next few laps (typical undercut window)
            # Assume driver B stays out for 2-5 more laps before pitting
            stint_length = min(8, max(2, int(rng.normal(4, 1))))  # 2-8 laps typically
            
            cumulative_driver_a_advantage = 0  # starts behind by pit loss
            cumulative_driver_b_degradation = 0
            
            # Simulate lap-by-lap performance
            for lap in range(stint_length):
                # Calculate tire advantage: fresh vs aged tires
                fresh_advantage = 0.0
                
                if models['deg'] is not None and models['deg'].fitted:
                    # Use fitted DegModel if available
                    try:
                        fresh_advantage = models['deg'].get_fresh_tire_advantage(
                            old_compound=request.compound_a,
                            new_compound=request.compound_a,
                            old_age=current_tire_age + lap,
                            new_age=1.0 + lap  # Fresh tires after pit
                        )
                    except Exception as e:
                        # Fallback if method fails
                        age_diff = (current_tire_age + lap) - (1.0 + lap)
                        fresh_advantage = max(0.0, age_diff * 0.12)  # ~0.12s per lap age diff
                else:
                    # Realistic F1 tire advantage fallback
                    # Fresh tires vs aged tires: ~0.1-0.2s per lap of age difference
                    age_diff = (current_tire_age + lap) - (1.0 + lap)  # old_age - new_age
                    fresh_advantage = max(0.0, age_diff * 0.12)  # Conservative 0.12s per lap
                
                # Apply diminishing returns as stint progresses (fresh tire advantage fades)
                tire_advantage = fresh_advantage * (0.9 ** lap)
                
                cumulative_driver_a_advantage += tire_advantage
                
                # Driver B loses time due to tire degradation (accelerating)
                # Degradation increases as tires get older and more laps are completed
                lap_degradation = degradation_penalty * (1.3 ** lap)  # exponential degradation
                cumulative_driver_b_degradation += lap_degradation
            
            # Total time difference after stint
            net_time_difference = (driver_a_immediate_loss - 
                                 cumulative_driver_a_advantage - 
                                 cumulative_driver_b_degradation)
            
            # Undercut succeeds if A overcomes initial gap + makes up time
            if net_time_difference < gap_seconds:
                successes += 1
        
        # Calculate results
        p_undercut = successes / request.samples
        avg_pit_loss = np.mean(pit_losses)
        avg_outlap_delta = np.mean(outlap_deltas)
        
        # Add more details to assumptions
        assumptions.update({
            "avg_degradation_penalty_s": float(np.mean(degradation_penalties)),
            "pit_loss_range": [float(np.min(pit_losses)), float(np.max(pit_losses))],
            "outlap_delta_range": [float(np.min(outlap_deltas)), float(np.max(outlap_deltas))],
            "compound_used": request.compound_a,
            "success_margin_s": float(np.mean([
                (gap_seconds + deg - (pit + outlap)) 
                for pit, outlap, deg in zip(pit_losses, outlap_deltas, degradation_penalties)
            ]))
        })
        
        # Create response
        response_data = SimulateResponse(
            p_undercut=p_undercut,
            pitLoss_s=float(avg_pit_loss),
            outLapDelta_s=float(avg_outlap_delta),
            assumptions=assumptions
        )
        
        # Store in cache
        cache.set(
            request.gp, request.year, request.driver_a, request.driver_b,
            request.compound_a, request.lap_now, request.samples, gap_seconds,
            response_data.dict()
        )
        
        # Calculate timing and add to performance metrics
        duration_ms = round((time.time() - start_time) * 1000, 2)
        cache.add_request_time(duration_ms)
        
        # Log successful simulation with rounded outputs for privacy
        rounded_response = round_simulation_outputs(response_data.dict())
        logger.info(
            "Simulation completed successfully",
            input_hash=input_hash,
            duration_ms=duration_ms,
            p_undercut=rounded_response["p_undercut"],
            pit_loss_s=rounded_response["pitLoss_s"],
            outlap_delta_s=rounded_response["outLapDelta_s"],
            models_used={
                "deg": models['deg'] is not None,
                "pit": models['pit'] is not None,
                "outlap": models['outlap'] is not None
            },
            cache_stats=cache.get_cache_stats()
        )
        
        return response_data
        
    except Exception as e:
        # Calculate timing for failed requests
        duration_ms = round((time.time() - start_time) * 1000, 2)
        cache.add_request_time(duration_ms)
        
        logger.error(
            "Simulation failed",
            input_hash=input_hash,
            duration_ms=duration_ms,
            error=str(e),
            error_type=type(e).__name__
        )
        
        # Report to Sentry if configured
        if sentry_dsn:
            sentry_sdk.capture_exception(e)
        
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@app.get("/api/v1/models/status")
async def get_models_status() -> Dict[str, Any]:
    """Get status of fitted models."""
    return {
        "models": {
            "deg_model": global_models['deg'] is not None and global_models['deg'].fitted if global_models['deg'] else False,
            "pit_model": global_models['pit'] is not None and global_models['pit'].fitted if global_models['pit'] else False,  
            "outlap_model": global_models['outlap'] is not None and global_models['outlap'].fitted if global_models['outlap'] else False
        },
        "api_clients": {
            "openf1_client": "available",
            "jolpica_client": "available"
        }
    }


@app.get("/api/v1/performance/metrics")
async def get_performance_metrics() -> Dict[str, Any]:
    """Get performance and caching metrics."""
    cache = get_simulation_cache()
    performance_stats = cache.get_performance_stats()
    
    return {
        "cache": {
            "size": performance_stats.get("cache_size", 0),
            "max_size": performance_stats.get("max_cache_size", 0),
            "hits": performance_stats.get("cache_hits", 0),
            "misses": performance_stats.get("cache_misses", 0),
            "hit_rate_percent": performance_stats.get("hit_rate_percent", 0.0)
        },
        "latency": {
            "total_requests": performance_stats.get("count", 0),
            "avg_ms": performance_stats.get("avg_ms"),
            "p50_ms": performance_stats.get("p50_ms"),
            "p90_ms": performance_stats.get("p90_ms"),
            "p95_ms": performance_stats.get("p95_ms"),
            "p99_ms": performance_stats.get("p99_ms"),
            "min_ms": performance_stats.get("min_ms"),
            "max_ms": performance_stats.get("max_ms")
        }
    }


@app.get("/api/v1/models/cache")
async def get_model_cache_info() -> Dict[str, Any]:
    """Get model cache information."""
    from model_cache import get_cache_info
    
    cache_info = get_cache_info()
    cache_info["fast_mode_enabled"] = FAST_MODE
    
    return cache_info


@app.post("/api/v1/models/cache/clear")
async def clear_model_cache() -> Dict[str, str]:
    """Clear the model cache."""
    from model_cache import clear_model_cache
    
    try:
        clear_model_cache()
        return {"status": "success", "message": "Model cache cleared"}
    except Exception as e:
        logger.error(f"Failed to clear model cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


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