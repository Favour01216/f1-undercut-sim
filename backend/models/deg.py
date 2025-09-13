"""
Tire Degradation Model

Data-driven tire degradation model that learns circuit and compound-specific
performance characteristics using robust regression techniques.
"""

import logging
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import sys
from scipy.optimize import minimize

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from services.model_params import get_parameters_manager, DegradationParameters, ParameterScope

logger = logging.getLogger(__name__)


class DegModel:
    """
    Data-driven tire degradation model with robust regression and circuit/compound learning.
    
    Fits per-circuit and per-compound models with intelligent fallback:
    lap_delta = a*age² + b*age + c
    
    Uses Huber loss for robust regression and k-fold CV for reliability assessment.
    """
    
    def __init__(self, circuit: Optional[str] = None, compound: Optional[str] = None):
        """Initialize the degradation model."""
        self.circuit = circuit
        self.compound = compound
        self.coefficients: Optional[np.ndarray] = None
        self.baseline_time: Optional[float] = None
        self.r_squared: Optional[float] = None
        self.std_error: Optional[float] = None
        self.sample_count: int = 0
        self.cv_scores: List[float] = []
        self.params_manager = get_parameters_manager()
        self.huber_delta = 1.5  # Huber loss threshold

    def fit(self, lap_data: pd.DataFrame, circuit: Optional[str] = None, 
            save_params: bool = False) -> None:
        """
        Fit the degradation model to lap data.
        
        Args:
            lap_data: DataFrame with lap time and tire age data
            circuit: Optional circuit name for parameter scoping
            save_params: Whether to save fitted parameters
        """
        try:
            self._validate_data(lap_data)
            
            # Try to load existing parameters first
            if self._try_load_existing_params(circuit):
                logger.info(f"Loaded existing degradation parameters for {circuit or 'global'}")
                return
            
            # Filter and prepare data
            clean_data = self._prepare_data(lap_data)
            
            if len(clean_data) < 10:
                raise ValueError(f"Insufficient data points: {len(clean_data)} < 10")
            
            # Extract features and target
            X, y = self._extract_features_target(clean_data)
            
            # Fit robust quadratic model
            self.coefficients, self.r_squared, self.std_error = self._fit_huber_regression(X, y)
            
            # Perform k-fold cross-validation
            self.cv_scores = self._cross_validate(X, y, k=5)
            
            self.sample_count = len(clean_data)
            self.baseline_time = clean_data['lap_time'].median()
            
            # Save parameters if requested
            if save_params and circuit:
                self._save_parameters(circuit)
            
            logger.info(
                f"DegModel fitted: R²={self.r_squared:.3f}, "
                f"CV={np.mean(self.cv_scores):.3f}±{np.std(self.cv_scores):.3f}, "
                f"n={self.sample_count}"
            )
            
        except Exception as e:
            logger.error(f"Failed to fit DegModel: {e}")
            # Load fallback parameters
            self._load_fallback_params()

    def fit_from_data(self, lap_data: pd.DataFrame, circuit: Optional[str] = None, 
                     save_params: bool = False) -> None:
        """Alias for fit method for compatibility."""
        self.fit(lap_data, circuit, save_params)

    def _validate_data(self, data: pd.DataFrame) -> None:
        """Validate input data has required columns."""
        required_cols = ['lap_time', 'tyre_age_at_start']
        missing = [col for col in required_cols if col not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def _prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and filter data for modeling."""
        # Copy and clean data
        clean = data.copy()
        
        # Remove invalid/missing values
        clean = clean.dropna(subset=['lap_time', 'tyre_age_at_start'])
        
        # Filter reasonable lap times (between 60s and 200s for F1)
        clean = clean[(clean['lap_time'] >= 60) & (clean['lap_time'] <= 200)]
        
        # Filter reasonable tire ages (0-50 laps)
        clean = clean[(clean['tyre_age_at_start'] >= 0) & (clean['tyre_age_at_start'] <= 50)]
        
        # Remove outliers using IQR method
        Q1 = clean['lap_time'].quantile(0.25)
        Q3 = clean['lap_time'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        clean = clean[(clean['lap_time'] >= lower_bound) & (clean['lap_time'] <= upper_bound)]
        
        return clean

    def _extract_features_target(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Extract features (age, age²) and target (lap_time) from data."""
        age = data['tyre_age_at_start'].values
        
        # Create quadratic features: [1, age, age²]
        X = np.column_stack([
            np.ones(len(age)),  # intercept
            age,                # linear term
            age**2              # quadratic term
        ])
        
        y = data['lap_time'].values
        
        return X, y

    def _fit_huber_regression(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, float, float]:
        """Fit robust regression using Huber loss."""
        
        def huber_loss(coeffs, X, y, delta=self.huber_delta):
            """Huber loss function."""
            residuals = y - X @ coeffs
            abs_residuals = np.abs(residuals)
            
            # Huber loss: quadratic for small residuals, linear for large ones
            loss = np.where(
                abs_residuals <= delta,
                0.5 * residuals**2,
                delta * abs_residuals - 0.5 * delta**2
            )
            
            return np.sum(loss)
        
        # Initial guess (OLS solution as starting point)
        try:
            initial_coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
        except:
            initial_coeffs = np.zeros(X.shape[1])
        
        # Minimize Huber loss
        result = minimize(
            huber_loss,
            initial_coeffs,
            args=(X, y),
            method='BFGS',
            options={'maxiter': 1000}
        )
        
        if not result.success:
            logger.warning("Huber regression did not converge, using OLS fallback")
            coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
        else:
            coeffs = result.x
        
        # Calculate R² and standard error
        y_pred = X @ coeffs
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        mse = ss_res / (len(y) - len(coeffs)) if len(y) > len(coeffs) else ss_res / len(y)
        std_error = np.sqrt(mse)
        
        return coeffs, r_squared, std_error

    def _cross_validate(self, X: np.ndarray, y: np.ndarray, k: int = 5) -> List[float]:
        """Perform k-fold cross-validation."""
        n = len(y)
        fold_size = n // k
        scores = []
        
        for i in range(k):
            # Split data
            start_idx = i * fold_size
            end_idx = start_idx + fold_size if i < k-1 else n
            
            # Create train/test splits
            test_indices = list(range(start_idx, end_idx))
            train_indices = [j for j in range(n) if j not in test_indices]
            
            X_train, X_test = X[train_indices], X[test_indices]
            y_train, y_test = y[train_indices], y[test_indices]
            
            # Fit on training data
            try:
                coeffs, _, _ = self._fit_huber_regression(X_train, y_train)
                
                # Evaluate on test data
                y_pred = X_test @ coeffs
                ss_res = np.sum((y_test - y_pred)**2)
                ss_tot = np.sum((y_test - np.mean(y_test))**2)
                score = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
                scores.append(score)
                
            except Exception as e:
                logger.warning(f"CV fold {i} failed: {e}")
                scores.append(0.0)
        
        return scores

    def _try_load_existing_params(self, circuit: Optional[str] = None) -> bool:
        """Try to load existing parameters for the given circuit/compound."""
        try:
            scope = ParameterScope.CIRCUIT_COMPOUND if circuit and self.compound else \
                   ParameterScope.COMPOUND if self.compound else \
                   ParameterScope.GLOBAL
            
            params = self.params_manager.get_degradation_params(
                circuit=circuit or self.circuit,
                compound=self.compound,
                scope=scope
            )
            
            if params:
                self.coefficients = np.array([params.intercept, params.linear_coeff, params.quadratic_coeff])
                self.r_squared = params.r_squared
                self.std_error = params.std_error
                self.sample_count = params.sample_count
                self.cv_scores = params.cv_scores or []
                return True
                
        except Exception as e:
            logger.debug(f"Could not load existing params: {e}")
        
        return False

    def _save_parameters(self, circuit: str) -> None:
        """Save fitted parameters to persistent storage."""
        try:
            if self.coefficients is None:
                return
            
            params = DegradationParameters(
                circuit=circuit,
                compound=self.compound,
                intercept=float(self.coefficients[0]),
                linear_coeff=float(self.coefficients[1]),
                quadratic_coeff=float(self.coefficients[2]),
                r_squared=self.r_squared or 0.0,
                std_error=self.std_error or 0.0,
                sample_count=self.sample_count,
                cv_scores=self.cv_scores
            )
            
            self.params_manager.save_degradation_params(params)
            logger.info(f"Saved degradation parameters for {circuit}/{self.compound}")
            
        except Exception as e:
            logger.error(f"Failed to save parameters: {e}")

    def _load_fallback_params(self) -> None:
        """Load fallback parameters when fitting fails."""
        try:
            # Try compound-specific fallback
            if self.compound:
                params = self.params_manager.get_degradation_params(compound=self.compound)
                if params:
                    self.coefficients = np.array([params.intercept, params.linear_coeff, params.quadratic_coeff])
                    self.r_squared = params.r_squared
                    self.std_error = params.std_error
                    logger.info(f"Loaded compound fallback parameters for {self.compound}")
                    return
            
            # Global fallback
            params = self.params_manager.get_degradation_params()
            if params:
                self.coefficients = np.array([params.intercept, params.linear_coeff, params.quadratic_coeff])
                self.r_squared = params.r_squared
                self.std_error = params.std_error
                logger.info("Loaded global fallback parameters")
                return
            
        except Exception as e:
            logger.warning(f"Fallback parameter loading failed: {e}")
        
        # Ultimate fallback - hardcoded reasonable values
        self.coefficients = np.array([85.0, 0.15, 0.001])  # Reasonable F1 degradation
        self.r_squared = 0.5
        self.std_error = 1.0
        logger.info("Using hardcoded fallback parameters")

    def predict_lap_time(self, tire_age: float, baseline_time: Optional[float] = None) -> float:
        """
        Predict lap time for a given tire age.
        
        Args:
            tire_age: Age of the tires in laps
            baseline_time: Optional baseline lap time (uses fitted baseline if None)
        
        Returns:
            Predicted lap time in seconds
        """
        if self.coefficients is None:
            raise ValueError("Model must be fitted before prediction")
        
        # Use provided baseline or fitted baseline
        base = baseline_time or self.baseline_time or 85.0
        
        # Predict using quadratic model: base + a*age² + b*age + c
        delta = (
            self.coefficients[0] +
            self.coefficients[1] * tire_age +
            self.coefficients[2] * tire_age**2
        )
        
        return base + delta

    def get_fresh_tire_advantage(self, old_age: float, new_age: float = 0) -> float:
        """
        Calculate the lap time advantage of fresh tires vs old tires.
        
        Args:
            old_age: Age of the old tires
            new_age: Age of the new tires (default 0 for fresh)
        
        Returns:
            Time advantage in seconds (positive means new tires are faster)
        """
        if self.coefficients is None:
            # Fallback calculation
            degradation_per_lap = 0.05  # seconds per lap
            return (old_age - new_age) * degradation_per_lap
        
        # Calculate difference using quadratic model
        old_delta = (
            self.coefficients[0] +
            self.coefficients[1] * old_age +
            self.coefficients[2] * old_age**2
        )
        
        new_delta = (
            self.coefficients[0] +
            self.coefficients[1] * new_age +
            self.coefficients[2] * new_age**2
        )
        
        return old_delta - new_delta

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the fitted model."""
        return {
            "fitted": self.coefficients is not None,
            "circuit": self.circuit,
            "compound": self.compound,
            "r_squared": self.r_squared,
            "std_error": self.std_error,
            "sample_count": self.sample_count,
            "cv_mean": np.mean(self.cv_scores) if self.cv_scores else None,
            "cv_std": np.std(self.cv_scores) if self.cv_scores else None,
            "coefficients": self.coefficients.tolist() if self.coefficients is not None else None
        }

    def __repr__(self) -> str:
        """String representation of the model."""
        if self.coefficients is None:
            return f"DegModel(unfitted, circuit={self.circuit}, compound={self.compound})"
        
        return (
            f"DegModel(R²={self.r_squared:.3f}, "
            f"circuit={self.circuit}, compound={self.compound}, "
            f"n={self.sample_count})"
        )