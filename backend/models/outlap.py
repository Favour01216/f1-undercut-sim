"""
Outlap Performance Model

Model for predicting first lap performance after tire changes,
accounting for cold tire penalties by compound type.
Enhanced version with circuit-specific learning and parameter persistence.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List, Union
import logging
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
        self.scope = self._determine_scope()
        
        # Model state
        self.compound_models: Dict[str, Dict[str, float]] = {}
        self.fitted: bool = False
        self.sample_counts: Dict[str, int] = {}
        
        # For learned parameters
        self.mean_penalty: Optional[float] = None
        self.std_penalty: Optional[float] = None
        self.baseline_time: Optional[float] = None
        
        # Parameter manager
        self._param_manager = ModelParametersManager()
        
        # Try to load existing parameters
        self._load_parameters()
        
    def _determine_scope(self) -> str:
        """Determine the scope based on available specificity."""
        if self.circuit and self.compound:
            return "circuit_compound"
        elif self.compound:
            return "compound"
        elif self.circuit:
            return "circuit"
        else:
            return "global"
        
    def _load_parameters(self) -> bool:
        """
        Load parameters from persistent storage if available.
        
        Returns:
            True if parameters were loaded successfully
        """
        try:
            params = self._param_manager.get_outlap_params(
                circuit=self.circuit,
                compound=self.compound
            )
            
            if params:
                self.mean_penalty = params.mean_penalty
                self.std_penalty = params.std_penalty
                self.baseline_time = params.baseline_time
                self.fitted = True
                logger.info(f"Loaded outlap parameters for {self.scope}: "
                           f"penalty={self.mean_penalty:.3f}±{self.std_penalty:.3f}")
                return True
                
        except Exception as e:
            logger.warning(f"Could not load outlap parameters: {e}")
            
        return False
        
    def fit_from_data(self, df_laps: pd.DataFrame, save_params: bool = True) -> 'OutlapModel':
        """
        Enhanced fit method with circuit/compound-specific learning and persistence.
        Gracefully handles missing compound data by using general outlap analysis.
        
        Args:
            df_laps: DataFrame with lap time data
            save_params: Whether to save learned parameters to storage
            
        Returns:
            Self for method chaining
        """
        if df_laps.empty:
            raise ValueError("Cannot fit model with empty DataFrame")
        
        # Find required columns
        lap_time_col = self._find_column(df_laps, ['lap_time', 'lap_duration', 'laptime'])
        
        # Look for outlap indicators (OpenF1 API uses 'is_pit_out_lap')
        outlap_col = None
        try:
            outlap_col = self._find_column(df_laps, ['is_pit_out_lap', 'stint_lap', 'tire_age'])
        except ValueError:
            raise ValueError("No outlap identification column found. Need 'is_pit_out_lap', 'stint_lap', or 'tire_age'")
        
        # Optional compound column (gracefully handle missing compound data)
        compound_col = None
        try:
            compound_col = self._find_column(df_laps, ['compound', 'tire_compound'])
        except ValueError:
            logger.warning("No compound data available - using general outlap analysis")
        
        # Optional circuit column
        circuit_col = None
        try:
            circuit_col = self._find_column(df_laps, ['circuit', 'track', 'circuit_name'])
        except ValueError:
            pass  # Circuit column is optional
        
        # Clean and filter data
        df_work = self._prepare_data(df_laps, lap_time_col, compound_col, outlap_col, circuit_col)
        
        if df_work.empty:
            raise ValueError("No valid data after cleaning and filtering")
        
        # Analyze outlap penalties (compound-agnostic if needed)
        outlap_analysis = self._analyze_outlap_penalties(df_work, lap_time_col, compound_col, outlap_col)
        
        if not outlap_analysis:
            raise ValueError("Could not extract outlap penalty statistics")
        
        # Store results
        self.mean_penalty = outlap_analysis['mean_penalty']
        self.std_penalty = outlap_analysis['std_penalty']
        self.baseline_time = outlap_analysis['baseline_time']
        self.n_samples = outlap_analysis['n_samples']
        self.fitted = True
        
        # Save parameters if requested
        if save_params:
            self._save_parameters()
        
        logger.info(f"Fitted outlap model for {self.scope}: "
                   f"penalty={self.mean_penalty:.3f}±{self.std_penalty:.3f} "
                   f"(n={outlap_analysis['n_samples']})")
        
        return self
        
    def _prepare_data(self, df_laps: pd.DataFrame, lap_time_col: str, compound_col: Optional[str], 
                     outlap_col: str, circuit_col: Optional[str]) -> pd.DataFrame:
        """Prepare and filter data for analysis. Handles missing compound data gracefully."""
        
        # Select relevant columns
        cols = [lap_time_col, outlap_col]
        if compound_col:
            cols.append(compound_col)
        if circuit_col:
            cols.append(circuit_col)
            
        df_work = df_laps[cols].copy()
        df_work = df_work.dropna()
        
        # Clean numeric columns
        df_work[lap_time_col] = pd.to_numeric(df_work[lap_time_col], errors='coerce')
        
        # Handle different outlap column types
        if outlap_col in ['stint_lap', 'tire_age']:
            df_work[outlap_col] = pd.to_numeric(df_work[outlap_col], errors='coerce')
        # 'is_pit_out_lap' is already boolean, no conversion needed
        
        df_work = df_work.dropna()
        
        # Normalize compound names if available
        if compound_col and compound_col in df_work.columns:
            df_work[compound_col] = df_work[compound_col].str.upper().str.strip()
            df_work[compound_col] = df_work[compound_col].replace({'S': 'SOFT', 'M': 'MEDIUM', 'H': 'HARD'})
            
            # Filter by compound if specified
            if self.compound:
                df_work = df_work[df_work[compound_col] == self.compound.upper()]
        
        # Filter by circuit if specified
        if self.circuit and circuit_col and circuit_col in df_work.columns:
            df_work = df_work[df_work[circuit_col].str.upper() == self.circuit.upper()]
        
        # Remove obvious outliers
        df_work = df_work[
            (df_work[lap_time_col] >= 60) & 
            (df_work[lap_time_col] <= 200)
        ]
        
        # Additional filtering for stint lap columns
        if outlap_col in ['stint_lap', 'tire_age']:
            df_work = df_work[
                (df_work[outlap_col] >= 1) &
                (df_work[outlap_col] <= 50)
            ]
        
        return df_work
        
    def _analyze_outlap_penalties(self, df_work: pd.DataFrame, lap_time_col: str, 
                                 compound_col: Optional[str], outlap_col: str) -> Optional[Dict[str, float]]:
        """Analyze outlap penalties from prepared data. Works with or without compound data."""
        
        # Get outlaps and warmed laps based on the column type
        if outlap_col == 'is_pit_out_lap':
            # OpenF1 API format: True = outlap, False = normal lap
            outlaps = df_work[df_work[outlap_col] == True][lap_time_col]
            warmed = df_work[df_work[outlap_col] == False][lap_time_col]
        elif outlap_col in ['stint_lap', 'tire_age']:
            # Traditional format: stint_lap == 1 = outlap, stint_lap >= 3 = warmed
            outlaps = df_work[df_work[outlap_col] == 1][lap_time_col]
            warmed = df_work[df_work[outlap_col] >= 3][lap_time_col]
        else:
            logger.error(f"Unknown outlap column type: {outlap_col}")
            return None
        
        if len(outlaps) < 3 or len(warmed) < 3:
            logger.warning(f"Insufficient data: {len(outlaps)} outlaps, {len(warmed)} warmed laps")
            return None
        
        # Calculate baseline from warmed laps (using 25th percentile for better representation)
        baseline_time = np.percentile(warmed, 25)
        
        # Calculate penalties
        penalties = outlaps - baseline_time
        
        # For undercut simulation, we want PURE TIRE PENALTY, not traffic effects
        # Real outlaps include ~15-20s of traffic/position penalties that don't apply to clean undercuts
        # Filter for the lower range (0-8s) to get pure tire effects only
        pure_tire_penalties = penalties[(penalties >= 0) & (penalties <= 8.0)]
        
        if len(pure_tire_penalties) < 3:
            # If insufficient, gradually expand range but cap at realistic simulation values
            pure_tire_penalties = penalties[(penalties >= 0) & (penalties <= 12.0)]
            if len(pure_tire_penalties) < 3:
                # As last resort, use all reasonable penalties but cap at 8s for simulation
                all_penalties = penalties[(penalties >= 0) & (penalties <= 30.0)]
                if len(all_penalties) < 3:
                    logger.warning(f"Insufficient valid penalties: {len(all_penalties)}")
                    return None
                # Cap at 8s to remove traffic effects for simulation use
                pure_tire_penalties = np.minimum(all_penalties, 8.0)
            else:
                # Cap at 6s for intermediate range
                pure_tire_penalties = np.minimum(pure_tire_penalties, 6.0)
        
        # The result represents PURE TIRE PENALTY suitable for undercut simulation
        capped_penalties = pure_tire_penalties
        
        # Use robust statistics
        mean_penalty = float(np.mean(capped_penalties))
        std_penalty = float(max(0.1, np.std(capped_penalties)))
        
        # Log compound-specific info if available
        if compound_col and compound_col in df_work.columns:
            compounds = df_work[compound_col].unique()
            logger.info(f"Analyzed outlaps for compounds: {compounds}")
        else:
            logger.info("Analyzed outlaps without compound information (general model)")
        
        logger.info(f"Outlap analysis: {len(outlaps)} outlaps, {len(warmed)} warmed laps, "
                   f"{len(pure_tire_penalties)} pure tire penalties, penalty={mean_penalty:.3f}±{std_penalty:.3f}s")
        
        return {
            'mean_penalty': mean_penalty,
            'std_penalty': std_penalty,
            'baseline_time': baseline_time,
            'n_samples': len(capped_penalties)
        }
        
    def _save_parameters(self) -> None:
        """Save learned parameters to persistent storage."""
        try:
            from services.model_params import OutlapParameters
            
            params = OutlapParameters(
                circuit=self.circuit or "unknown",
                compound=self.compound or "unknown", 
                mean_penalty=self.mean_penalty,
                std_penalty=self.std_penalty,
                n_samples=getattr(self, 'n_samples', 0),
                scope=self.scope
            )
            
            self._param_manager.save_outlap_params([params])
            logger.info(f"Saved outlap parameters for {self.scope}")
        except Exception as e:
            logger.error(f"Failed to save outlap parameters: {e}")
        
    def fit(self, df_laps: pd.DataFrame) -> 'OutlapModel':
        """
        Backward compatibility method for existing code.
        Fits a simple model without circuit/compound specificity.
        """
        return self.fit_from_data(df_laps, save_params=False)
        
    def sample(self, compound: str = None, n: int = 1, rng: Optional[np.random.Generator] = None) -> Union[float, np.ndarray]:
        """
        Generate random outlap time penalty samples.
        
        Args:
            compound: Tire compound ('SOFT', 'MEDIUM', 'HARD'). 
                     If None and model has compound specificity, uses model's compound.
            n: Number of samples
            rng: Random number generator for reproducible results (default: None)
            
        Returns:
            Array of outlap penalties in seconds
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before sampling")
        
        if n < 0:
            raise ValueError("Number of samples must be non-negative")
            
        # Handle edge case where n=0
        if n == 0:
            return np.array([])
        
        # Determine which parameters to use
        if self.mean_penalty is not None:
            # Use specific model parameters
            mean_penalty = self.mean_penalty
            std_penalty = self.std_penalty
        elif compound and compound.upper() in self.compound_models:
            # Use legacy compound-specific model
            model = self.compound_models[compound.upper()]
            mean_penalty = model['mean_penalty']
            std_penalty = model['std_penalty']
        else:
            # Fallback to default penalty
            logger.warning("No specific model available, using default penalty")
            mean_penalty = 1.0
            std_penalty = 0.5
        
        # Sample from normal distribution
        if rng is not None:
            samples = rng.normal(mean_penalty, std_penalty, size=n)
        else:
            samples = np.random.normal(mean_penalty, std_penalty, size=n)
        
        # Ensure reasonable bounds (for simulation, cap outlap penalties at 30s)
        samples = np.clip(samples, 0.0, 30.0)
        
        return samples if n > 1 else samples[0]
        
    def get_expected_penalty(self, compound: str = None) -> float:
        """
        Get expected outlap penalty for a compound.
        
        Args:
            compound: Tire compound (optional if model has specificity)
            
        Returns:
            Expected penalty in seconds
        """
        if not self.fitted:
            return 1.0  # Default penalty
        
        if self.mean_penalty is not None:
            return self.mean_penalty
        elif compound and compound.upper() in self.compound_models:
            return self.compound_models[compound.upper()]['mean_penalty']
        else:
            return 1.0  # Default penalty
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the fitted model."""
        if not self.fitted:
            return {"fitted": False}
        
        info = {
            "fitted": True,
            "circuit": self.circuit,
            "compound": self.compound,
            "scope": self.scope
        }
        
        if self.mean_penalty is not None:
            info.update({
                "mean_penalty": float(self.mean_penalty),
                "std_penalty": float(self.std_penalty),
                "baseline_time": float(self.baseline_time) if self.baseline_time else None
            })
        
        if self.compound_models:
            info["compound_models"] = {
                compound: {
                    "mean_penalty": model['mean_penalty'],
                    "std_penalty": model['std_penalty'],
                    "sample_count": self.sample_counts.get(compound, 0)
                }
                for compound, model in self.compound_models.items()
            }
        
        return info
    
    def _find_column(self, df: pd.DataFrame, candidates: List[str]) -> str:
        """Find the first matching column from candidates."""
        for col in candidates:
            if col in df.columns:
                return col
        raise ValueError(f"No column found from candidates: {candidates}")