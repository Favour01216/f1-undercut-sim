"""
Outlap Performance Model

This module contains the outlap performance prediction model.
It predicts lap times and performance on the first lap after a pit stop.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from pydantic import BaseModel
from enum import Enum


class TireCompound(str, Enum):
    """Tire compound types."""
    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class OutlapPrediction(BaseModel):
    """Outlap performance prediction result."""
    predicted_lap_time: float
    confidence_interval: Tuple[float, float]
    tire_warm_up_laps: int
    fuel_effect: float
    track_evolution: float
    confidence: float


class OutlapModel:
    """
    Outlap performance prediction model.
    
    Predicts performance on the first lap after a pit stop based on:
    - Tire compound and temperature
    - Fuel load
    - Track conditions
    - Driver characteristics
    - Car setup
    """
    
    def __init__(self):
        """Initialize the outlap model."""
        # Base outlap penalties for different tire compounds (seconds)
        self.tire_outlap_penalties = {
            TireCompound.SOFT: 0.5,    # Soft tires warm up fastest
            TireCompound.MEDIUM: 1.2,  # Medium penalty
            TireCompound.HARD: 2.1     # Hard tires take longest to warm up
        }
        
        # Fuel effect: seconds per kg of fuel
        self.fuel_effect_per_kg = 0.035
        
        # Track evolution effect per lap
        self.track_evolution_per_lap = -0.02  # Track gets faster over time
        
    def predict(
        self, 
        session_key: str, 
        tire_compound: str, 
        fuel_load: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Predict outlap performance for given conditions.
        
        Args:
            session_key: Session identifier
            tire_compound: Tire compound being fitted
            fuel_load: Current fuel load percentage (0-100)
            **kwargs: Additional parameters (track_temp, lap_number, etc.)
            
        Returns:
            Dictionary containing outlap performance prediction
        """
        try:
            # Extract additional parameters
            track_temp = kwargs.get("track_temp", 30.0)
            lap_number = kwargs.get("lap_number", 20)
            baseline_lap_time = kwargs.get("baseline_lap_time", 90.0)
            driver_skill = kwargs.get("driver_skill", 0.8)  # 0-1 scale
            car_balance = kwargs.get("car_balance", 0.7)   # 0-1 scale
            
            # Validate tire compound
            if tire_compound not in [e.value for e in TireCompound]:
                return {"error": f"Invalid tire compound: {tire_compound}"}
            
            compound_enum = TireCompound(tire_compound)
            
            # Calculate outlap prediction
            prediction = self._calculate_outlap_prediction(
                compound_enum=compound_enum,
                fuel_load=fuel_load,
                track_temp=track_temp,
                lap_number=lap_number,
                baseline_lap_time=baseline_lap_time,
                driver_skill=driver_skill,
                car_balance=car_balance
            )
            
            return {
                "session_key": session_key,
                "tire_compound": tire_compound,
                "fuel_load": fuel_load,
                "prediction": prediction,
                "factors": self._get_prediction_factors(
                    compound_enum, fuel_load, track_temp, lap_number
                )
            }
            
        except Exception as e:
            return {"error": f"Outlap prediction failed: {str(e)}"}
    
    def _calculate_outlap_prediction(
        self,
        compound_enum: TireCompound,
        fuel_load: float,
        track_temp: float,
        lap_number: int,
        baseline_lap_time: float,
        driver_skill: float,
        car_balance: float
    ) -> Dict[str, Any]:
        """Calculate the outlap performance prediction."""
        
        # Base tire outlap penalty
        tire_penalty = self.tire_outlap_penalties[compound_enum]
        
        # Temperature factor for tire compound
        temp_factor = self._calculate_temperature_factor(compound_enum, track_temp)
        tire_penalty *= temp_factor
        
        # Fuel load effect
        fuel_kg = fuel_load * 1.1  # Assume 110kg max fuel load
        fuel_penalty = fuel_kg * self.fuel_effect_per_kg
        
        # Track evolution (track gets faster over time)
        track_evolution = lap_number * self.track_evolution_per_lap
        
        # Driver skill factor (better drivers lose less time on outlaps)
        driver_factor = 1.0 - (driver_skill * 0.3)  # Up to 30% reduction
        
        # Car balance factor
        balance_factor = 1.0 - (car_balance * 0.2)  # Up to 20% reduction
        
        # Calculate predicted lap time
        total_penalty = (tire_penalty * driver_factor * balance_factor) + fuel_penalty
        predicted_lap_time = baseline_lap_time + total_penalty + track_evolution
        
        # Calculate confidence interval (±0.5s typically)
        uncertainty = 0.5 + (1.0 - driver_skill) * 0.3
        confidence_interval = (
            predicted_lap_time - uncertainty,
            predicted_lap_time + uncertainty
        )
        
        # Estimate tire warm-up period
        warm_up_laps = self._estimate_warm_up_laps(compound_enum, track_temp)
        
        # Calculate confidence based on various factors
        confidence = self._calculate_prediction_confidence(
            compound_enum, fuel_load, track_temp, driver_skill
        )
        
        return {
            "predicted_lap_time": round(predicted_lap_time, 3),
            "confidence_interval": (
                round(confidence_interval[0], 3),
                round(confidence_interval[1], 3)
            ),
            "tire_warm_up_laps": warm_up_laps,
            "fuel_effect": round(fuel_penalty, 3),
            "track_evolution": round(track_evolution, 3),
            "confidence": round(confidence, 2),
            "baseline_lap_time": baseline_lap_time,
            "total_penalty": round(total_penalty, 3)
        }
    
    def _calculate_temperature_factor(
        self, 
        compound: TireCompound, 
        track_temp: float
    ) -> float:
        """Calculate how track temperature affects outlap performance."""
        # Optimal temperature ranges for each compound
        optimal_ranges = {
            TireCompound.SOFT: (25.0, 35.0),
            TireCompound.MEDIUM: (20.0, 40.0),
            TireCompound.HARD: (15.0, 45.0)
        }
        
        optimal_min, optimal_max = optimal_ranges[compound]
        
        if optimal_min <= track_temp <= optimal_max:
            return 1.0  # Optimal conditions
        elif track_temp < optimal_min:
            # Too cold - harder to warm up
            return 1.0 + (optimal_min - track_temp) * 0.05
        else:
            # Too hot - may overheat quickly
            return 1.0 + (track_temp - optimal_max) * 0.03
    
    def _estimate_warm_up_laps(
        self, 
        compound: TireCompound, 
        track_temp: float
    ) -> int:
        """Estimate how many laps it takes for tires to reach optimal performance."""
        base_warm_up = {
            TireCompound.SOFT: 1,
            TireCompound.MEDIUM: 2,
            TireCompound.HARD: 3
        }
        
        base_laps = base_warm_up[compound]
        
        # Adjust for temperature
        if track_temp < 20:
            return base_laps + 1
        elif track_temp > 40:
            return max(1, base_laps - 1)
        else:
            return base_laps
    
    def _calculate_prediction_confidence(
        self,
        compound: TireCompound,
        fuel_load: float,
        track_temp: float,
        driver_skill: float
    ) -> float:
        """Calculate the confidence level of the prediction."""
        confidence = 0.8  # Base confidence
        
        # Compound familiarity (softs are more predictable)
        if compound == TireCompound.SOFT:
            confidence += 0.1
        elif compound == TireCompound.HARD:
            confidence -= 0.1
        
        # Fuel load predictability (medium loads are most predictable)
        if 40 <= fuel_load <= 70:
            confidence += 0.05
        else:
            confidence -= 0.05
        
        # Temperature conditions
        if 20 <= track_temp <= 35:
            confidence += 0.05
        else:
            confidence -= 0.1
        
        # Driver skill factor
        confidence += driver_skill * 0.1
        
        return max(0.3, min(0.95, confidence))
    
    def _get_prediction_factors(
        self,
        compound: TireCompound,
        fuel_load: float,
        track_temp: float,
        lap_number: int
    ) -> Dict[str, Any]:
        """Get detailed breakdown of factors affecting the prediction."""
        return {
            "tire_compound_effect": {
                "compound": compound.value,
                "base_penalty": self.tire_outlap_penalties[compound],
                "temperature_factor": self._calculate_temperature_factor(compound, track_temp)
            },
            "fuel_effect": {
                "fuel_load_percent": fuel_load,
                "estimated_fuel_kg": fuel_load * 1.1,
                "time_penalty_per_kg": self.fuel_effect_per_kg
            },
            "track_conditions": {
                "temperature": track_temp,
                "lap_number": lap_number,
                "track_evolution_per_lap": self.track_evolution_per_lap
            },
            "warm_up_characteristics": {
                "estimated_warm_up_laps": self._estimate_warm_up_laps(compound, track_temp),
                "optimal_temp_range": self._get_optimal_temp_range(compound)
            }
        }
    
    def _get_optimal_temp_range(self, compound: TireCompound) -> Tuple[float, float]:
        """Get the optimal temperature range for a tire compound."""
        ranges = {
            TireCompound.SOFT: (25.0, 35.0),
            TireCompound.MEDIUM: (20.0, 40.0),
            TireCompound.HARD: (15.0, 45.0)
        }
        return ranges[compound]
    
    def compare_compounds(
        self, 
        session_key: str,
        fuel_load: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Compare outlap performance across all tire compounds."""
        comparisons = {}
        
        for compound in TireCompound:
            prediction = self.predict(
                session_key=session_key,
                tire_compound=compound.value,
                fuel_load=fuel_load,
                **kwargs
            )
            
            if "prediction" in prediction:
                comparisons[compound.value] = prediction["prediction"]
        
        # Rank compounds by predicted lap time
        if comparisons:
            sorted_compounds = sorted(
                comparisons.items(),
                key=lambda x: x[1]["predicted_lap_time"]
            )
            
            return {
                "compound_comparison": comparisons,
                "ranking": [comp[0] for comp in sorted_compounds],
                "fastest_compound": sorted_compounds[0][0],
                "slowest_compound": sorted_compounds[-1][0],
                "time_difference": round(
                    sorted_compounds[-1][1]["predicted_lap_time"] - 
                    sorted_compounds[0][1]["predicted_lap_time"], 3
                )
            }
        
        return {"error": "Unable to compare compounds"}