"""
F1 Undercut Simulation FastAPI Application

This is the main FastAPI application for the F1 undercut simulation tool.
It provides APIs for tire degradation analysis, pit stop optimization,
and undercut simulation with probability calculations.
"""

import logging
import os
from typing import Any, Literal

import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, confloat, conint

# Import our new modeling classes and API clients
from models.deg import DegModel
from models.outlap import OutlapModel
from models.pit import PitModel
from services.jolpica import JolpicaClient
from services.openf1 import OpenF1Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Initialize API clients
openf1_client = OpenF1Client()
jolpica_client = JolpicaClient()

# Global model instances (will be fitted on first use)
global_models = {"deg": None, "pit": None, "outlap": None}


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


class SimIn(BaseModel):
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
    lap_now: conint(ge=1, le=100) = Field(..., description="Current lap number")
    samples: conint(ge=1, le=10000) = Field(
        1000, description="Number of Monte Carlo samples"
    )


class SimOut(BaseModel):
    """Response model for undercut simulation with strict validation."""

    p_undercut: confloat(ge=0, le=1) = Field(
        ..., description="Probability of successful undercut (0-1)"
    )
    pitLoss_s: float = Field(..., description="Expected pit stop time loss in seconds")
    outLapDelta_s: float = Field(..., description="Expected outlap penalty in seconds")
    avgMargin_s: float | None = Field(
        None, description="Average margin of success/failure in seconds"
    )
    assumptions: dict[str, Any] = Field(
        ..., description="Model assumptions and parameters used"
    )


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint providing API information."""
    return {
        "message": "F1 Undercut Simulator API",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
        "simulate": "/simulate",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint returning service status."""
    return {"status": "ok"}


def get_or_fit_models(gp: str, year: int) -> dict[str, Any]:
    """Get fitted models, fitting them if needed."""
    global global_models

    try:
        # Get data from APIs
        logger.info(f"Fetching data for {gp} {year}")

        with openf1_client as client:
            laps_df = client.get_laps(gp, year)
            pit_events_df = client.get_pit_events(gp, year)

        # Fit models if not already fitted or if data is new
        models = {}

        # Fit DegModel
        if not laps_df.empty:
            deg_model = DegModel()
            deg_model.fit(laps_df)
            models["deg"] = deg_model
            logger.info("DegModel fitted successfully")
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

        # Fit OutlapModel
        if not laps_df.empty:
            outlap_model = OutlapModel()
            outlap_model.fit(laps_df)
            models["outlap"] = outlap_model
            logger.info("OutlapModel fitted successfully")
        else:
            models["outlap"] = None
            logger.warning("No lap data available for OutlapModel")

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


@app.post("/simulate", response_model=SimOut)
async def simulate_undercut(request: SimIn) -> SimOut:
    """
    Simulate undercut probability between two drivers.

    This endpoint calculates the probability that driver_a can successfully
    undercut driver_b by pitting now while driver_b stays out one more lap.
    """
    try:
        logger.info(
            f"Simulating undercut: {request.driver_a} vs {request.driver_b} at {request.gp} {request.year}"
        )

        # Get fitted models for this GP/year
        models = get_or_fit_models(request.gp, request.year)

        # Calculate current gap between drivers
        gap_seconds = calculate_driver_gap(
            request.gp,
            request.year,
            request.driver_a,
            request.driver_b,
            request.lap_now,
        )

        # Default assumptions
        assumptions = {
            "current_gap_s": gap_seconds,
            "tire_age_driver_b": request.lap_now
            - 1,  # Assume current stint started at lap 1
            "models_fitted": {
                "deg_model": models["deg"] is not None,
                "pit_model": models["pit"] is not None,
                "outlap_model": models["outlap"] is not None,
            },
            "monte_carlo_samples": request.samples,
        }

        # Monte Carlo simulation with deterministic RNG
        rng = np.random.default_rng(int(os.getenv("RNG_SEED", "42")))
        successes = 0
        pit_losses = []
        outlap_deltas = []
        degradation_penalties = []

        for _ in range(request.samples):
            # Sample pit stop time loss
            if models["pit"] is not None and models["pit"].fitted:
                pit_loss = models["pit"].sample(1, rng=rng)
            else:
                # Default F1 pit stop loss: ~25 seconds ± 3s
                pit_loss = rng.normal(25.0, 3.0)

            pit_losses.append(pit_loss)

            # Sample outlap penalty for compound A
            if models["outlap"] is not None and models["outlap"].fitted:
                try:
                    outlap_delta = models["outlap"].sample(
                        request.compound_a, 1, rng=rng
                    )
                except ValueError:
                    # Compound not available, use typical penalty
                    compound_penalties = {"SOFT": 0.5, "MEDIUM": 1.2, "HARD": 2.0}
                    outlap_delta = rng.normal(
                        compound_penalties.get(request.compound_a, 1.2), 0.3
                    )
            else:
                # Default outlap penalties by compound
                compound_penalties = {"SOFT": 0.5, "MEDIUM": 1.2, "HARD": 2.0}
                outlap_delta = rng.normal(
                    compound_penalties.get(request.compound_a, 1.2), 0.3
                )

            outlap_deltas.append(max(0, outlap_delta))

            # Predict driver B's degradation for staying out 1 more lap
            current_tire_age = assumptions["tire_age_driver_b"]
            if models["deg"] is not None and models["deg"].fitted:
                degradation_penalty = models["deg"].predict(
                    current_tire_age + 1
                ) - models["deg"].predict(current_tire_age)
            else:
                # Default degradation: ~0.05s per lap + quadratic component
                degradation_penalty = 0.05 + 0.002 * current_tire_age

            degradation_penalties.append(max(0, degradation_penalty))

            # Calculate undercut success
            # Success if: gap + pit_loss + outlap_penalty < time_gained_from_driver_b_staying_out
            driver_a_time_loss = pit_loss + outlap_delta
            driver_b_time_loss = degradation_penalty

            # Undercut succeeds if driver A's total time loss is less than gap + driver B's degradation
            if driver_a_time_loss < (gap_seconds + driver_b_time_loss):
                successes += 1

        # Calculate results
        p_undercut = successes / request.samples
        avg_pit_loss = np.mean(pit_losses)
        avg_outlap_delta = np.mean(outlap_deltas)

        # Calculate average margin (positive = success, negative = failure)
        margins = [
            (gap_seconds + deg - (pit + outlap))
            for pit, outlap, deg in zip(
                pit_losses, outlap_deltas, degradation_penalties, strict=True
            )
        ]
        avg_margin = float(np.mean(margins))

        # Add more details to assumptions
        assumptions.update(
            {
                "avg_degradation_penalty_s": float(np.mean(degradation_penalties)),
                "pit_loss_range": [
                    float(np.min(pit_losses)),
                    float(np.max(pit_losses)),
                ],
                "outlap_delta_range": [
                    float(np.min(outlap_deltas)),
                    float(np.max(outlap_deltas)),
                ],
                "compound_used": request.compound_a,
                "success_margin_s": avg_margin,
            }
        )

        logger.info(f"Simulation complete: P(undercut) = {p_undercut:.1%}")

        return SimOut(
            p_undercut=p_undercut,
            pitLoss_s=float(avg_pit_loss),
            outLapDelta_s=float(avg_outlap_delta),
            avgMargin_s=avg_margin,
            assumptions=assumptions,
        )

    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Simulation failed: {str(e)}"
        ) from e


@app.get("/api/v1/models/status")
async def get_models_status() -> dict[str, Any]:
    """Get status of fitted models."""
    return {
        "models": {
            "deg_model": (
                global_models["deg"] is not None and global_models["deg"].fitted
                if global_models["deg"]
                else False
            ),
            "pit_model": (
                global_models["pit"] is not None and global_models["pit"].fitted
                if global_models["pit"]
                else False
            ),
            "outlap_model": (
                global_models["outlap"] is not None and global_models["outlap"].fitted
                if global_models["outlap"]
                else False
            ),
        },
        "api_clients": {"openf1_client": "available", "jolpica_client": "available"},
    }


if __name__ == "__main__":
    # Run the application
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "True").lower() == "true"

    uvicorn.run("app:app", host=host, port=port, reload=debug, log_level="info")
