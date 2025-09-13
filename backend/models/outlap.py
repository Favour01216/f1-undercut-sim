"""
Outlap Performance Model

Model for predicting first lap performance after tire changes,
accounting for cold tire penalties by compound type.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List, Union
import logging
from scipy import stats
from collections import defaultdict

logger = logging.getLogger(__name__)


class OutlapModel:
    """
    Cold tire outlap performance model.
    
    Analyzes lap time penalties on the first lap after a pit stop,
    modeling compound-specific warm-up characteristics.
    """
    
    def __init__(self):
        """Initialize the outlap model."""
        self.compound_models: Dict[str, Dict[str, float]] = {}
        self.fitted: bool = False
        self.sample_counts: Dict[str, int] = {}
        
    def fit(self, df_laps: pd.DataFrame) -> 'OutlapModel':
        """
        Fit the outlap model to lap time data by tire compound.
        
        Expected DataFrame columns:
        - 'lap_time' or 'lap_duration': Lap time in seconds
        - 'compound' or 'tire_compound': Tire compound (SOFT, MEDIUM, HARD)  
        - 'stint_lap' or 'tire_age': Position within stint (1=outlap, 2+)
        
        Args:
            df_laps: DataFrame with lap time data
            
        Returns:
            Self for method chaining
        """
        if df_laps.empty:
            raise ValueError("Cannot fit model with empty DataFrame")
        
        # Find required columns
        lap_time_col = self._find_column(df_laps, ['lap_time', 'lap_duration', 'laptime'])
        compound_col = self._find_column(df_laps, ['compound', 'tire_compound'])
        stint_lap_col = self._find_column(df_laps, ['stint_lap', 'tire_age'])
        
        # Clean data
        df_work = df_laps[[lap_time_col, compound_col, stint_lap_col]].copy()
        df_work = df_work.dropna()
        df_work[lap_time_col] = pd.to_numeric(df_work[lap_time_col], errors='coerce')
        df_work[stint_lap_col] = pd.to_numeric(df_work[stint_lap_col], errors='coerce')
        df_work = df_work.dropna()
        
        # Normalize compound names
        df_work[compound_col] = df_work[compound_col].str.upper().str.strip()
        df_work[compound_col] = df_work[compound_col].replace({'S': 'SOFT', 'M': 'MEDIUM', 'H': 'HARD'})
        
        # Fit models by compound
        for compound in ['SOFT', 'MEDIUM', 'HARD']:
            compound_data = df_work[df_work[compound_col] == compound]
            
            if len(compound_data) < 5:
                continue
            
            # Get outlaps (stint_lap == 1) and warmed laps (stint_lap >= 3)
            outlaps = compound_data[compound_data[stint_lap_col] == 1][lap_time_col]
            warmed = compound_data[compound_data[stint_lap_col] >= 3][lap_time_col]
            
            if len(outlaps) < 2 or len(warmed) < 2:
                continue
            
            # Calculate baseline and penalties
            baseline = np.percentile(warmed, 10)
            penalties = outlaps - baseline
            penalties = penalties[(penalties >= 0) & (penalties <= 5)]
            
            if len(penalties) < 2:
                continue
            
            # Store model parameters
            self.compound_models[compound] = {
                'mean_penalty': float(penalties.mean()),
                'std_penalty': float(max(0.1, penalties.std())),
                'baseline_time': baseline
            }
            self.sample_counts[compound] = len(penalties)
        
        if not self.compound_models:
            raise ValueError("Could not fit model for any compounds")
        
        self.fitted = True
        return self
    
    def sample(self, compound: str, n: int = 1, rng: Optional[np.random.Generator] = None) -> float | np.ndarray:
        """
        Generate random outlap time penalty samples.
        
        Args:
            compound: Tire compound ('SOFT', 'MEDIUM', 'HARD')
            n: Number of samples
            rng: Random number generator for reproducible results (default: None)
            
        Returns:
            Array of outlap penalties in seconds
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before sampling")
        
        compound = compound.upper()
        if compound not in self.compound_models:
            raise ValueError(f"Compound '{compound}' not available")
        
        if n < 0:
            raise ValueError("Number of samples must be non-negative")
            
        # Handle edge case where n=0
        if n == 0:
            return np.array([])
        
        model = self.compound_models[compound]
        
        # Use provided RNG or create deterministic default
        if rng is None:
            rng = np.random.default_rng(42)
        
        # Sample from normal distribution with deterministic RNG
        samples = rng.normal(model['mean_penalty'], model['std_penalty'], size=n)
        
        # Ensure reasonable bounds
        samples = np.clip(samples, 0.0, 5.0)
        
        return samples if n > 1 else samples[0]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the fitted model."""
        if not self.fitted:
            return {"fitted": False}
        
        return {
            "fitted": True,
            "compounds": list(self.compound_models.keys()),
            "models": {
                compound: {
                    "mean_penalty": model['mean_penalty'],
                    "std_penalty": model['std_penalty'],
                    "sample_count": self.sample_counts[compound]
                }
                for compound, model in self.compound_models.items()
            }
        }
    
    def _find_column(self, df: pd.DataFrame, candidates: List[str]) -> str:
        """Find the first matching column from candidates."""
        for col in candidates:
            if col in df.columns:
                return col
        raise ValueError(f"No column found from candidates: {candidates}")
