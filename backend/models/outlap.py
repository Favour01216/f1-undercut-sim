"""
Outlap Performance Model

Model for predicting first lap performance after tire changes,
accounting for cold tire penalties by compound type.
Enhanced version with circuit-specific learning and parameter persistence.
"""

import logging
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List, Union
from scipy import stats
from collections import defaultdict
from dataclasses import dataclass

from backend.services.model_params import ModelParametersManager

logger = logging.getLogger(__name__)


class OutlapModel:
    """
    Cold tire outlap performance model with circuit-specific learning.
    
    Analyzes lap time penalties on the first lap after a pit stop,
    modeling compound-specific warm-up characteristics per circuit.
    Enhanced version integrates with ModelParametersManager for persistence.
    """
    
    def __init__(self, circuit: str = None, compound: str = None):
        """
        Initialize the outlap model with optional circuit/compound specificity.
        
        Args:
            circuit: Circuit name for circuit-specific modeling
            compound: Tire compound for compound-specific modeling
        """
        self.circuit = circuit
        self.compound = compound
        self.mean_penalty: float = 1.5  # Default penalty in seconds
        self.std_penalty: float = 0.5   # Default standard deviation
        self.sample_count: int = 0
        self.compound_penalties: Dict[str, Dict[str, float]] = {}
        self.fitted = False
        
        # Initialize parameter manager
        self.params_manager = ModelParametersManager()
        
        # Try to load existing parameters
        self._load_existing_parameters()

    def _load_existing_parameters(self) -> None:
        """Load existing parameters from storage if available."""
        try:
            params = self.params_manager.get_outlap_params(
                circuit=self.circuit, 
                compound=self.compound
            )
            
            if params:
                self.mean_penalty = params.mean_penalty
                self.std_penalty = params.std_penalty
                self.sample_count = params.sample_count
                self.compound_penalties = params.compound_penalties or {}
                self.fitted = True
                
                logger.info(
                    f"Loaded outlap parameters: {self.mean_penalty:.1f}±{self.std_penalty:.1f}s "
                    f"(circuit={self.circuit}, compound={self.compound})"
                )
        except Exception as e:
            logger.debug(f"Could not load existing outlap parameters: {e}")

    def fit(self, lap_data: pd.DataFrame) -> None:
        """
        Fit the outlap model to lap data.
        
        This method maintains compatibility with the original interface.
        """
        self.fit_from_data(lap_data, save_params=True)

    def fit_from_data(self, lap_data: pd.DataFrame, save_params: bool = False) -> None:
        """
        Fit outlap penalty model from lap timing data.
        
        Analyzes first laps vs subsequent laps to estimate cold tire penalties.
        Uses robust statistical methods to filter traffic effects.
        
        Args:
            lap_data: DataFrame with lap timing data including stint information
            save_params: Whether to save fitted parameters to storage
        """
        try:
            if lap_data.empty:
                logger.warning("Empty lap data provided to OutlapModel")
                return
            
            # Check for required columns
            required_cols = ['lap_time', 'stint']
            missing_cols = [col for col in required_cols if col not in lap_data.columns]
            
            if missing_cols:
                logger.warning(f"Missing required columns for OutlapModel: {missing_cols}")
                # Try alternative analysis
                self._analyze_alternative_outlaps(lap_data)
                return
            
            # Analyze outlap penalties
            penalties = self._analyze_outlap_penalties(lap_data)
            
            if len(penalties) < 5:
                logger.warning(f"Insufficient outlap data: {len(penalties)} samples")
                self._use_fallback_parameters()
                return
            
            # Fit statistical model to penalties
            self._fit_penalty_distribution(penalties)
            
            # Analyze by compound if data available
            if 'compound' in lap_data.columns:
                self._analyze_compound_specific_penalties(lap_data)
            
            self.fitted = True
            self.sample_count = len(penalties)
            
            # Save parameters if requested
            if save_params:
                self._save_parameters()
            
            logger.info(
                f"OutlapModel fitted: {self.mean_penalty:.1f}±{self.std_penalty:.1f}s "
                f"from {self.sample_count} outlaps"
            )
            
        except Exception as e:
            logger.error(f"Failed to fit OutlapModel: {e}")
            self._use_fallback_parameters()

    def _analyze_outlap_penalties(self, lap_data: pd.DataFrame) -> List[float]:
        """
        Analyze outlap penalties by comparing first stint laps to subsequent laps.
        
        Enhanced version filters for clean laptime differences suitable for simulation.
        """
        penalties = []
        
        # Group by stint and driver
        groupby_cols = ['stint']
        if 'driver_number' in lap_data.columns:
            groupby_cols.append('driver_number')
        elif 'driver' in lap_data.columns:
            groupby_cols.append('driver')
        
        for group_key, stint_data in lap_data.groupby(groupby_cols):
            if len(stint_data) < 3:  # Need at least 3 laps in stint
                continue
            
            # Sort by lap number
            if 'lap_number' in stint_data.columns:
                stint_data = stint_data.sort_values('lap_number')
            
            # Get lap times
            lap_times = stint_data['lap_time'].values
            
            # Skip if any lap times are invalid
            if np.any(np.isnan(lap_times)) or np.any(lap_times <= 0):
                continue
            
            # Filter reasonable lap times (60-200s for F1)
            if not all(60 <= t <= 200 for t in lap_times):
                continue
            
            # Calculate outlap penalty (first lap vs average of laps 3+)
            first_lap = lap_times[0]
            
            if len(lap_times) >= 4:
                # Use laps 3+ for warmed tire baseline (skip lap 2 as intermediate)
                warmed_laps = lap_times[2:]
                warmed_avg = np.mean(warmed_laps)
            elif len(lap_times) >= 3:
                # Use lap 3 only
                warmed_avg = lap_times[2]
            else:
                continue  # Not enough data
            
            penalty = first_lap - warmed_avg
            
            # Filter realistic penalties (0-8 seconds for simulation use)
            # This removes traffic-heavy outlaps that would skew undercut simulation
            if 0 <= penalty <= 8.0:
                penalties.append(penalty)
        
        return penalties

    def _analyze_alternative_outlaps(self, lap_data: pd.DataFrame) -> None:
        """Fallback analysis when stint data is not available."""
        try:
            # Look for pit_out_lap indicator
            if 'is_pit_out_lap' in lap_data.columns:
                outlaps = lap_data[lap_data['is_pit_out_lap'] == True]
                
                if len(outlaps) > 5:
                    # Compare outlap times to session average
                    session_avg = lap_data['lap_time'].median()
                    penalties = []
                    
                    for _, outlap in outlaps.iterrows():
                        penalty = outlap['lap_time'] - session_avg
                        if 0 <= penalty <= 8.0:  # Filter for simulation-relevant penalties
                            penalties.append(penalty)
                    
                    if penalties:
                        self._fit_penalty_distribution(penalties)
                        self.sample_count = len(penalties)
                        return
            
            # Ultimate fallback
            self._use_fallback_parameters()
            
        except Exception as e:
            logger.warning(f"Alternative outlap analysis failed: {e}")
            self._use_fallback_parameters()

    def _fit_penalty_distribution(self, penalties: List[float]) -> None:
        """Fit statistical distribution to outlap penalties."""
        penalties_array = np.array(penalties)
        
        # Remove outliers using IQR method
        Q1 = np.percentile(penalties_array, 25)
        Q3 = np.percentile(penalties_array, 75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        filtered_penalties = penalties_array[
            (penalties_array >= lower_bound) & (penalties_array <= upper_bound)
        ]
        
        if len(filtered_penalties) > 0:
            self.mean_penalty = float(np.mean(filtered_penalties))
            self.std_penalty = float(np.std(filtered_penalties)) if len(filtered_penalties) > 1 else 0.3
        else:
            # If all data filtered out, use original
            self.mean_penalty = float(np.mean(penalties_array))
            self.std_penalty = float(np.std(penalties_array)) if len(penalties_array) > 1 else 0.3

    def _analyze_compound_specific_penalties(self, lap_data: pd.DataFrame) -> None:
        """Analyze penalties by tire compound."""
        self.compound_penalties = {}
        
        for compound in lap_data['compound'].unique():
            if pd.isna(compound):
                continue
            
            compound_data = lap_data[lap_data['compound'] == compound]
            penalties = self._analyze_outlap_penalties(compound_data)
            
            if len(penalties) >= 3:
                mean_penalty = float(np.mean(penalties))
                std_penalty = float(np.std(penalties)) if len(penalties) > 1 else 0.3
                
                self.compound_penalties[compound] = {
                    'mean': mean_penalty,
                    'std': std_penalty,
                    'count': len(penalties)
                }

    def _use_fallback_parameters(self) -> None:
        """Use fallback parameters when fitting fails."""
        # Try to load global parameters
        try:
            global_params = self.params_manager.get_outlap_params()
            if global_params:
                self.mean_penalty = global_params.mean_penalty
                self.std_penalty = global_params.std_penalty
                logger.info("Using global fallback outlap parameters")
                return
        except Exception:
            pass
        
        # Use compound-specific defaults
        compound_defaults = {
            'SOFT': {'mean': 0.8, 'std': 0.3},
            'MEDIUM': {'mean': 1.4, 'std': 0.4},
            'HARD': {'mean': 2.2, 'std': 0.5}
        }
        
        if self.compound and self.compound in compound_defaults:
            defaults = compound_defaults[self.compound]
            self.mean_penalty = defaults['mean']
            self.std_penalty = defaults['std']
            logger.info(f"Using compound fallback parameters for {self.compound}")
        else:
            # Ultimate fallback
            self.mean_penalty = 1.5
            self.std_penalty = 0.5
            logger.info("Using hardcoded fallback outlap parameters")

    def _save_parameters(self) -> None:
        """Save fitted parameters to storage."""
        try:
            from backend.services.model_params import OutlapParameters
            
            params = OutlapParameters(
                circuit=self.circuit,
                compound=self.compound,
                mean_penalty=self.mean_penalty,
                std_penalty=self.std_penalty,
                sample_count=self.sample_count,
                compound_penalties=self.compound_penalties
            )
            
            self.params_manager.save_outlap_params(params)
            logger.info(f"Saved outlap parameters for {self.circuit}/{self.compound}")
            
        except Exception as e:
            logger.error(f"Failed to save outlap parameters: {e}")

    def sample(self, n: int = 1) -> Union[float, np.ndarray]:
        """
        Sample outlap penalties from the fitted distribution.
        
        Args:
            n: Number of samples to generate
            
        Returns:
            Single penalty value if n=1, otherwise array of penalties
        """
        # Sample from normal distribution
        samples = np.random.normal(self.mean_penalty, self.std_penalty, n)
        
        # Ensure non-negative penalties
        samples = np.maximum(samples, 0.0)
        
        if n == 1:
            return float(samples[0])
        return samples

    def get_penalty_for_compound(self, compound: str) -> float:
        """
        Get penalty estimate for a specific compound.
        
        Args:
            compound: Tire compound ('SOFT', 'MEDIUM', 'HARD')
            
        Returns:
            Expected penalty in seconds
        """
        if compound in self.compound_penalties:
            return self.compound_penalties[compound]['mean']
        
        # Fallback to general model or compound defaults
        compound_defaults = {
            'SOFT': 0.8,
            'MEDIUM': 1.4, 
            'HARD': 2.2
        }
        
        return compound_defaults.get(compound, self.mean_penalty)

    def predict(self, compound: Optional[str] = None) -> float:
        """
        Predict outlap penalty for given conditions.
        
        Args:
            compound: Optional tire compound
            
        Returns:
            Expected penalty in seconds
        """
        if compound:
            return self.get_penalty_for_compound(compound)
        return self.mean_penalty

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the fitted model."""
        return {
            'fitted': self.fitted,
            'circuit': self.circuit,
            'compound': self.compound,
            'mean_penalty': self.mean_penalty,
            'std_penalty': self.std_penalty,
            'sample_count': self.sample_count,
            'compound_penalties': self.compound_penalties
        }

    def __repr__(self) -> str:
        """String representation of the model."""
        return (
            f"OutlapModel(penalty={self.mean_penalty:.1f}±{self.std_penalty:.1f}s, "
            f"circuit={self.circuit}, compound={self.compound}, "
            f"fitted={self.fitted})"
        )