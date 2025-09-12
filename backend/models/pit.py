"""
Pit Stop Strategy Model

This module contains the pit stop strategy optimization model.
It analyzes optimal pit windows and strategy decisions.
"""

from typing import Dict, List, Any, Optional
import numpy as np
from pydantic import BaseModel
from enum import Enum


class StrategyType(str, Enum):
    """Pit strategy types."""
    ONE_STOP = "one_stop"
    TWO_STOP = "two_stop"
    THREE_STOP = "three_stop"
    UNDERCUT = "undercut"
    OVERCUT = "overcut"


class PitWindow(BaseModel):
    """Pit window definition."""
    lap_start: int
    lap_end: int
    probability: float
    tire_compound: str
    expected_gain: float


class StrategyRecommendation(BaseModel):
    """Strategy recommendation result."""
    strategy_type: StrategyType
    pit_windows: List[PitWindow]
    expected_position_gain: float
    risk_factor: float
    confidence: float


class PitStopModel:
    """
    Pit stop strategy optimization model.
    
    Analyzes optimal pit stop strategies based on:
    - Track position
    - Tire degradation
    - Fuel load
    - Traffic conditions
    - Weather conditions
    """
    
    def __init__(self):
        """Initialize the pit stop model."""
        self.pit_loss_time = 23.0  # Average pit stop time loss (seconds)
        self.undercut_window = 3  # Laps for effective undercut
        self.tire_compounds = ["SOFT", "MEDIUM", "HARD"]
        
    def optimize(self, strategy_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize pit stop strategy for given conditions.
        
        Args:
            strategy_request: Request containing race conditions and constraints
            
        Returns:
            Dictionary containing strategy recommendations
        """
        try:
            # Extract request parameters
            current_position = strategy_request.get("current_position", 10)
            current_lap = strategy_request.get("current_lap", 1)
            total_laps = strategy_request.get("total_laps", 50)
            current_tire = strategy_request.get("current_tire", "MEDIUM")
            tire_age = strategy_request.get("tire_age", 0)
            fuel_load = strategy_request.get("fuel_load", 100.0)
            weather = strategy_request.get("weather", "dry")
            traffic_density = strategy_request.get("traffic_density", 0.5)
            
            # Analyze different strategy options
            strategies = []
            
            # One-stop strategy
            one_stop = self._analyze_one_stop_strategy(
                current_lap, total_laps, current_tire, tire_age
            )
            strategies.append(one_stop)
            
            # Two-stop strategy
            two_stop = self._analyze_two_stop_strategy(
                current_lap, total_laps, current_tire, tire_age
            )
            strategies.append(two_stop)
            
            # Undercut strategy
            undercut = self._analyze_undercut_strategy(
                current_position, current_lap, total_laps, traffic_density
            )
            strategies.append(undercut)
            
            # Rank strategies by expected outcome
            ranked_strategies = sorted(
                strategies, 
                key=lambda x: x["expected_position_gain"], 
                reverse=True
            )
            
            return {
                "current_conditions": {
                    "position": current_position,
                    "lap": current_lap,
                    "tire": current_tire,
                    "tire_age": tire_age,
                    "weather": weather
                },
                "recommended_strategy": ranked_strategies[0],
                "alternative_strategies": ranked_strategies[1:],
                "analysis_timestamp": "2024-01-01T00:00:00Z"  # Placeholder
            }
            
        except Exception as e:
            return {"error": f"Strategy optimization failed: {str(e)}"}
    
    def _analyze_one_stop_strategy(
        self, 
        current_lap: int, 
        total_laps: int,
        current_tire: str,
        tire_age: int
    ) -> Dict[str, Any]:
        """Analyze one-stop strategy option."""
        # Calculate optimal pit window for one-stop
        remaining_laps = total_laps - current_lap
        optimal_pit_lap = current_lap + int(remaining_laps * 0.6)
        
        # Determine best tire compound
        if remaining_laps > 30:
            recommended_tire = "HARD"
        elif remaining_laps > 15:
            recommended_tire = "MEDIUM"
        else:
            recommended_tire = "SOFT"
        
        pit_window = {
            "lap_start": max(current_lap + 5, optimal_pit_lap - 3),
            "lap_end": min(total_laps - 5, optimal_pit_lap + 3),
            "probability": 0.8,
            "tire_compound": recommended_tire,
            "expected_gain": 0.5
        }
        
        return {
            "strategy_type": "one_stop",
            "pit_windows": [pit_window],
            "expected_position_gain": 1.2,
            "risk_factor": 0.3,
            "confidence": 0.8,
            "description": f"Single pit stop on lap {optimal_pit_lap} to {recommended_tire} tires"
        }
    
    def _analyze_two_stop_strategy(
        self, 
        current_lap: int, 
        total_laps: int,
        current_tire: str,
        tire_age: int
    ) -> Dict[str, Any]:
        """Analyze two-stop strategy option."""
        remaining_laps = total_laps - current_lap
        
        # First pit stop
        first_pit = current_lap + int(remaining_laps * 0.3)
        second_pit = current_lap + int(remaining_laps * 0.7)
        
        pit_windows = [
            {
                "lap_start": first_pit - 2,
                "lap_end": first_pit + 2,
                "probability": 0.9,
                "tire_compound": "MEDIUM",
                "expected_gain": 0.8
            },
            {
                "lap_start": second_pit - 2,
                "lap_end": second_pit + 2,
                "probability": 0.9,
                "tire_compound": "SOFT",
                "expected_gain": 1.2
            }
        ]
        
        return {
            "strategy_type": "two_stop",
            "pit_windows": pit_windows,
            "expected_position_gain": 2.0,
            "risk_factor": 0.5,
            "confidence": 0.7,
            "description": f"Two stops: lap {first_pit} (MEDIUM), lap {second_pit} (SOFT)"
        }
    
    def _analyze_undercut_strategy(
        self, 
        current_position: int,
        current_lap: int, 
        total_laps: int,
        traffic_density: float
    ) -> Dict[str, Any]:
        """Analyze undercut strategy option."""
        # Undercut is most effective when there's a car directly ahead
        if current_position <= 3:
            # Limited undercut potential from top positions
            undercut_gain = 0.3
            confidence = 0.4
        else:
            # Higher potential from mid-field
            undercut_gain = 1.5 - (traffic_density * 0.5)
            confidence = 0.8 - (traffic_density * 0.2)
        
        # Optimal undercut timing: earlier than expected pit window
        standard_pit_lap = current_lap + int((total_laps - current_lap) * 0.5)
        undercut_lap = max(current_lap + 3, standard_pit_lap - self.undercut_window)
        
        pit_window = {
            "lap_start": undercut_lap - 1,
            "lap_end": undercut_lap + 1,
            "probability": confidence,
            "tire_compound": "MEDIUM",
            "expected_gain": undercut_gain
        }
        
        return {
            "strategy_type": "undercut",
            "pit_windows": [pit_window],
            "expected_position_gain": undercut_gain,
            "risk_factor": 0.6,
            "confidence": confidence,
            "description": f"Undercut attempt on lap {undercut_lap} with fresh MEDIUM tires"
        }
    
    def calculate_undercut_advantage(
        self, 
        target_position: int,
        current_lap: int,
        tire_delta: int
    ) -> Dict[str, float]:
        """
        Calculate the potential advantage of an undercut move.
        
        Args:
            target_position: Position of car to undercut
            current_lap: Current lap number
            tire_delta: Age difference between tires
            
        Returns:
            Dictionary containing undercut analysis
        """
        # Base time advantage from fresh tires
        base_advantage = tire_delta * 0.05  # 0.05s per lap of tire age
        
        # Pit stop time loss
        pit_loss = self.pit_loss_time
        
        # Traffic factor (harder to undercut in traffic)
        traffic_factor = max(0.5, 1.0 - (target_position * 0.05))
        
        # Calculate net advantage
        net_advantage = (base_advantage * self.undercut_window * traffic_factor) - pit_loss
        
        return {
            "base_advantage_per_lap": round(base_advantage, 3),
            "total_advantage": round(base_advantage * self.undercut_window, 2),
            "pit_loss": pit_loss,
            "traffic_factor": round(traffic_factor, 2),
            "net_advantage": round(net_advantage, 2),
            "success_probability": min(0.9, max(0.1, net_advantage / 10.0))
        }