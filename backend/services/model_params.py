"""
Model Parameters Manager

Handles persistence and retrieval of learned model parameters for F1 simulation models.
Stores circuit-compound specific parameters with robust fallback mechanisms.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import logging
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ParameterScope(Enum):
    """Enumeration of parameter scope levels for fallback hierarchy."""
    CIRCUIT_COMPOUND = "circuit_compound"  # Most specific: monaco_soft
    COMPOUND_ONLY = "compound_only"        # Medium: soft (all circuits)
    GLOBAL = "global"                      # Fallback: all circuits, all compounds


@dataclass
class DegradationParameters:
    """Container for degradation model parameters."""
    circuit: str
    compound: str
    a: float  # quadratic coefficient (age^2)
    b: float  # linear coefficient (age)
    c: float  # constant coefficient
    r2: float  # R-squared from fitting
    rmse: float  # Root mean square error
    n_samples: int  # Number of data points used
    scope: str = ParameterScope.CIRCUIT_COMPOUND.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)


@dataclass 
class OutlapParameters:
    """Container for outlap model parameters."""
    circuit: str
    compound: str
    mean_penalty: float  # Mean outlap penalty in seconds
    std_penalty: float   # Standard deviation of penalty
    n_samples: int       # Number of outlaps used for fitting
    scope: str = ParameterScope.CIRCUIT_COMPOUND.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)


class ModelParametersManager:
    """
    Manages storage and retrieval of learned model parameters.
    
    Provides intelligent fallback hierarchy:
    1. Circuit + Compound specific (e.g., "monaco_soft")
    2. Compound only (e.g., "soft" across all circuits)  
    3. Global fallback (pooled across all circuits and compounds)
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the parameters manager.
        
        Args:
            base_path: Base directory for storing parameter files
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent / "features" / "model_params"
        
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # File paths for different parameter types
        self.degradation_file = self.base_path / "degradation_params.parquet"
        self.outlap_file = self.base_path / "outlap_params.parquet"
        
        # Cache for loaded parameters
        self._deg_cache: Optional[pd.DataFrame] = None
        self._outlap_cache: Optional[pd.DataFrame] = None
        
    def save_degradation_params(self, params: List[DegradationParameters]) -> None:
        """
        Save degradation model parameters to disk.
        
        Args:
            params: List of degradation parameters to save
        """
        if not params:
            logger.warning("No degradation parameters to save")
            return
            
        # Convert to DataFrame
        data = [p.to_dict() for p in params]
        df = pd.DataFrame(data)
        
        # Ensure proper data types
        df['r2'] = df['r2'].astype(float)
        df['rmse'] = df['rmse'].astype(float)
        df['n_samples'] = df['n_samples'].astype(int)
        
        # Save to parquet for efficient storage
        df.to_parquet(self.degradation_file, index=False)
        
        # Clear cache to force reload
        self._deg_cache = None
        
        logger.info(f"Saved {len(params)} degradation parameter sets to {self.degradation_file}")
        
    def save_outlap_params(self, params: List[OutlapParameters]) -> None:
        """
        Save outlap model parameters to disk.
        
        Args:
            params: List of outlap parameters to save
        """
        if not params:
            logger.warning("No outlap parameters to save")
            return
            
        # Convert to DataFrame
        data = [p.to_dict() for p in params]
        df = pd.DataFrame(data)
        
        # Ensure proper data types
        df['mean_penalty'] = df['mean_penalty'].astype(float)
        df['std_penalty'] = df['std_penalty'].astype(float)
        df['n_samples'] = df['n_samples'].astype(int)
        
        # Save to parquet
        df.to_parquet(self.outlap_file, index=False)
        
        # Clear cache
        self._outlap_cache = None
        
        logger.info(f"Saved {len(params)} outlap parameter sets to {self.outlap_file}")
        
    def load_degradation_params(self) -> pd.DataFrame:
        """
        Load degradation parameters from disk with caching.
        
        Returns:
            DataFrame with degradation parameters
        """
        if self._deg_cache is not None:
            return self._deg_cache
            
        if not self.degradation_file.exists():
            logger.warning(f"Degradation params file not found: {self.degradation_file}")
            return pd.DataFrame()
            
        self._deg_cache = pd.read_parquet(self.degradation_file)
        logger.debug(f"Loaded {len(self._deg_cache)} degradation parameter sets")
        return self._deg_cache
        
    def load_outlap_params(self) -> pd.DataFrame:
        """
        Load outlap parameters from disk with caching.
        
        Returns:
            DataFrame with outlap parameters
        """
        if self._outlap_cache is not None:
            return self._outlap_cache
            
        if not self.outlap_file.exists():
            logger.warning(f"Outlap params file not found: {self.outlap_file}")
            return pd.DataFrame()
            
        self._outlap_cache = pd.read_parquet(self.outlap_file)
        logger.debug(f"Loaded {len(self._outlap_cache)} outlap parameter sets")
        return self._outlap_cache
        
    def get_degradation_params(
        self, 
        circuit: str, 
        compound: str,
        min_r2: float = 0.1,
        min_samples: int = 10
    ) -> Optional[DegradationParameters]:
        """
        Get degradation parameters with intelligent fallback.
        
        Args:
            circuit: Circuit name (e.g., "monaco", "silverstone")
            compound: Tire compound ("SOFT", "MEDIUM", "HARD")
            min_r2: Minimum R-squared threshold for accepting parameters
            min_samples: Minimum sample size threshold
            
        Returns:
            Best available degradation parameters or None if none meet criteria
        """
        df = self.load_degradation_params()
        if df.empty:
            return None
            
        # Normalize inputs
        circuit = circuit.lower().strip()
        compound = compound.upper().strip()
        
        # Try fallback hierarchy
        for scope in [ParameterScope.CIRCUIT_COMPOUND, ParameterScope.COMPOUND_ONLY, ParameterScope.GLOBAL]:
            
            if scope == ParameterScope.CIRCUIT_COMPOUND:
                # Most specific: exact circuit + compound match
                candidates = df[
                    (df['circuit'].str.lower() == circuit) & 
                    (df['compound'].str.upper() == compound)
                ]
                
            elif scope == ParameterScope.COMPOUND_ONLY:
                # Medium specificity: compound across all circuits
                candidates = df[
                    (df['compound'].str.upper() == compound) &
                    (df['scope'] == ParameterScope.COMPOUND_ONLY.value)
                ]
                
            else:  # GLOBAL
                # Least specific: global parameters
                candidates = df[df['scope'] == ParameterScope.GLOBAL.value]
            
            # Filter by quality thresholds
            quality_candidates = candidates[
                (candidates['r2'] >= min_r2) & 
                (candidates['n_samples'] >= min_samples)
            ]
            
            if not quality_candidates.empty:
                # Select best candidate (highest R² with sufficient samples)
                best = quality_candidates.loc[quality_candidates['r2'].idxmax()]
                
                logger.debug(f"Found degradation params for {circuit}_{compound} using {scope.value} "
                            f"(R²={best['r2']:.3f}, n={best['n_samples']})")
                
                return DegradationParameters(
                    circuit=best['circuit'],
                    compound=best['compound'],
                    a=float(best['a']),
                    b=float(best['b']),
                    c=float(best['c']),
                    r2=float(best['r2']),
                    rmse=float(best['rmse']),
                    n_samples=int(best['n_samples']),
                    scope=best['scope']
                )
        
        logger.warning(f"No suitable degradation parameters found for {circuit}_{compound}")
        return None
        
    def get_outlap_params(
        self,
        circuit: str,
        compound: str,
        min_samples: int = 5
    ) -> Optional[OutlapParameters]:
        """
        Get outlap parameters with intelligent fallback.
        
        Args:
            circuit: Circuit name
            compound: Tire compound
            min_samples: Minimum sample size threshold
            
        Returns:
            Best available outlap parameters or None
        """
        df = self.load_outlap_params()
        if df.empty:
            return None
            
        # Normalize inputs
        circuit = circuit.lower().strip()
        compound = compound.upper().strip()
        
        # Try fallback hierarchy (same as degradation)
        for scope in [ParameterScope.CIRCUIT_COMPOUND, ParameterScope.COMPOUND_ONLY, ParameterScope.GLOBAL]:
            
            if scope == ParameterScope.CIRCUIT_COMPOUND:
                candidates = df[
                    (df['circuit'].str.lower() == circuit) & 
                    (df['compound'].str.upper() == compound)
                ]
                
            elif scope == ParameterScope.COMPOUND_ONLY:
                candidates = df[
                    (df['compound'].str.upper() == compound) &
                    (df['scope'] == ParameterScope.COMPOUND_ONLY.value)
                ]
                
            else:  # GLOBAL
                candidates = df[df['scope'] == ParameterScope.GLOBAL.value]
            
            # Filter by sample size
            quality_candidates = candidates[candidates['n_samples'] >= min_samples]
            
            if not quality_candidates.empty:
                # Select candidate with most samples
                best = quality_candidates.loc[quality_candidates['n_samples'].idxmax()]
                
                logger.debug(f"Found outlap params for {circuit}_{compound} using {scope.value} "
                            f"(μ={best['mean_penalty']:.2f}s, σ={best['std_penalty']:.2f}s, n={best['n_samples']})")
                
                return OutlapParameters(
                    circuit=best['circuit'],
                    compound=best['compound'],
                    mean_penalty=float(best['mean_penalty']),
                    std_penalty=float(best['std_penalty']),
                    n_samples=int(best['n_samples']),
                    scope=best['scope']
                )
        
        logger.warning(f"No suitable outlap parameters found for {circuit}_{compound}")
        return None
        
    def get_parameter_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics about stored parameters.
        
        Returns:
            Dictionary with parameter counts and quality metrics
        """
        deg_df = self.load_degradation_params()
        outlap_df = self.load_outlap_params()
        
        summary = {
            "degradation": {
                "total_params": len(deg_df),
                "circuits": deg_df['circuit'].nunique() if not deg_df.empty else 0,
                "compounds": deg_df['compound'].nunique() if not deg_df.empty else 0,
                "avg_r2": float(deg_df['r2'].mean()) if not deg_df.empty else 0.0,
                "avg_samples": float(deg_df['n_samples'].mean()) if not deg_df.empty else 0
            },
            "outlap": {
                "total_params": len(outlap_df),
                "circuits": outlap_df['circuit'].nunique() if not outlap_df.empty else 0,
                "compounds": outlap_df['compound'].nunique() if not outlap_df.empty else 0,
                "avg_samples": float(outlap_df['n_samples'].mean()) if not outlap_df.empty else 0
            }
        }
        
        return summary
        
    def clear_cache(self) -> None:
        """Clear parameter cache to force reload."""
        self._deg_cache = None
        self._outlap_cache = None
        logger.debug("Parameter cache cleared")


# Global instance for use across the application
_global_manager: Optional[ModelParametersManager] = None


def get_parameters_manager() -> ModelParametersManager:
    """Get the global parameters manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = ModelParametersManager()
    return _global_manager