"""
Tire Degradation Model

This module contains the tire degradation analysis model for F1 tires.
It analyzes tire performance degradation over time and distance.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from scipy import interpolate
from pydantic import BaseModel


class TireCompound(BaseModel):
    """Tire compound characteristics."""
    name: str
    hardness: int  # 1-5 scale (1=soft, 5=hard)
    optimal_temp_range: tuple[float, float]  # Celsius
    degradation_rate: float  # seconds per lap


class TireDegradationAnalysis(BaseModel):
    """Results of tire degradation analysis."""
    compound: str
    stint_length: int
    degradation_per_lap: float
    total_degradation: float
    optimal_window: tuple[int, int]  # lap range
    predicted_performance: List[float]


class TireDegradationModel:
    """
    Tire degradation analysis model.
    
    Analyzes tire performance degradation based on:
    - Tire compound characteristics
    - Track temperature
    - Lap times
    - Stint length
    """
    
    def __init__(self):
        """Initialize the tire degradation model."""
        self.compounds = {
            "SOFT": TireCompound(
                name="SOFT",
                hardness=1,
                optimal_temp_range=(90.0, 110.0),
                degradation_rate=0.15
            ),
            "MEDIUM": TireCompound(
                name="MEDIUM", 
                hardness=3,
                optimal_temp_range=(85.0, 105.0),
                degradation_rate=0.08
            ),
            "HARD": TireCompound(
                name="HARD",
                hardness=5,
                optimal_temp_range=(80.0, 100.0),
                degradation_rate=0.05
            )
        }
    
    def analyze(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze tire degradation for a session.
        
        Args:
            session_data: Session data containing lap times, compounds, etc.
            
        Returns:
            Dictionary containing degradation analysis results
        """
        if not session_data:
            return {"error": "No session data provided"}
        
        try:
            # Extract relevant data (placeholder implementation)
            lap_times = session_data.get("lap_times", [])
            tire_compounds = session_data.get("tire_compounds", [])
            track_temp = session_data.get("track_temperature", 30.0)
            
            analyses = []
            
            for compound in set(tire_compounds):
                if compound in self.compounds:
                    analysis = self._analyze_compound_degradation(
                        compound=compound,
                        lap_times=lap_times,
                        track_temp=track_temp
                    )
                    analyses.append(analysis)
            
            return {
                "track_temperature": track_temp,
                "analyses": analyses,
                "recommendations": self._generate_recommendations(analyses)
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _analyze_compound_degradation(
        self, 
        compound: str, 
        lap_times: List[float],
        track_temp: float
    ) -> Dict[str, Any]:
        """Analyze degradation for a specific tire compound."""
        if not lap_times:
            return {"compound": compound, "error": "No lap times available"}
        
        tire_compound = self.compounds[compound]
        
        # Calculate temperature factor
        temp_factor = self._calculate_temperature_factor(track_temp, tire_compound)
        
        # Simulate degradation (simplified model)
        stint_length = len(lap_times)
        base_degradation = tire_compound.degradation_rate * temp_factor
        
        degradation_per_lap = base_degradation * (1 + stint_length * 0.01)
        total_degradation = degradation_per_lap * stint_length
        
        # Calculate optimal stint window
        optimal_start = max(1, int(stint_length * 0.1))
        optimal_end = min(stint_length, int(stint_length * 0.8))
        
        # Predict performance degradation curve
        predicted_performance = self._predict_performance_curve(
            stint_length, degradation_per_lap
        )
        
        return {
            "compound": compound,
            "stint_length": stint_length,
            "degradation_per_lap": round(degradation_per_lap, 3),
            "total_degradation": round(total_degradation, 3),
            "optimal_window": (optimal_start, optimal_end),
            "predicted_performance": predicted_performance,
            "temperature_factor": round(temp_factor, 2)
        }
    
    def _calculate_temperature_factor(
        self, 
        track_temp: float, 
        compound: TireCompound
    ) -> float:
        """Calculate how track temperature affects tire degradation."""
        optimal_min, optimal_max = compound.optimal_temp_range
        optimal_mid = (optimal_min + optimal_max) / 2
        
        if optimal_min <= track_temp <= optimal_max:
            # In optimal range
            return 1.0
        elif track_temp < optimal_min:
            # Too cold - increased degradation
            return 1.0 + (optimal_min - track_temp) * 0.02
        else:
            # Too hot - increased degradation
            return 1.0 + (track_temp - optimal_max) * 0.03
    
    def _predict_performance_curve(
        self, 
        stint_length: int, 
        degradation_per_lap: float
    ) -> List[float]:
        """Predict the performance degradation curve over the stint."""
        performance = []
        base_performance = 100.0  # Starting at 100%
        
        for lap in range(stint_length):
            # Exponential degradation model
            current_performance = base_performance - (
                degradation_per_lap * lap * (1 + lap * 0.01)
            )
            performance.append(round(max(current_performance, 70.0), 2))
        
        return performance
    
    def _generate_recommendations(
        self, 
        analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate strategic recommendations based on analysis."""
        if not analyses:
            return {"message": "No analysis data available"}
        
        # Find best performing compound
        best_compound = min(
            analyses, 
            key=lambda x: x.get("total_degradation", float('inf'))
        )
        
        recommendations = {
            "best_compound": best_compound.get("compound"),
            "recommended_stint_length": best_compound.get("optimal_window", [0, 0])[1],
            "strategy": "conservative"  # Placeholder
        }
        
        return recommendations