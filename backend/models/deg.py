"""
Tire Degradation Model

Data-driven tire degradation model that learns circuit and compound-specific
performance characteristics using robust regression techniques.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
import logging
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
        self.fitted: bool = False
        self.r_squared: Optional[float] = None
        self.rmse: Optional[float] = None
        self.n_samples: Optional[int] = None
        self.scope: Optional[str] = None
        
        # Model parameters manager
        self._param_manager = get_parameters_manager()
        
    def fit_from_data(self, df_laps: pd.DataFrame, circuit: str, save_params: bool = True) -> 'DegModel':
        """
        Fit degradation models for all circuit-compound combinations in data.
        
        Args:
            df_laps: DataFrame with lap data including 'circuit', 'compound' columns
            circuit: Current circuit name for context
            save_params: Whether to save learned parameters to disk
            
        Returns:
            Self for method chaining
        """
        if df_laps.empty:
            raise ValueError("Cannot fit model with empty DataFrame")
            
        # Validate required columns
        required_cols = ['circuit', 'compound']
        lap_time_col = self._find_column(df_laps, ['lap_time', 'lap_duration', 'laptime'])
        tire_age_col = self._find_column(df_laps, ['tire_age', 'stint_lap', 'tyre_age'])
        
        if not all(col in df_laps.columns for col in required_cols):
            raise ValueError(f"Missing required columns: {required_cols}")
            
        # Clean data
        df_clean = df_laps[[lap_time_col, tire_age_col, 'circuit', 'compound']].copy()
        df_clean = df_clean.dropna()
        df_clean[lap_time_col] = pd.to_numeric(df_clean[lap_time_col], errors='coerce')
        df_clean[tire_age_col] = pd.to_numeric(df_clean[tire_age_col], errors='coerce')
        df_clean = df_clean.dropna()
        
        # Normalize names
        df_clean['circuit'] = df_clean['circuit'].str.lower().str.strip()
        df_clean['compound'] = df_clean['compound'].str.upper().str.strip()
        
        # Remove outliers
        df_clean = self._remove_outliers(df_clean, lap_time_col)
        
        learned_params = []
        
        # Fit per circuit-compound combination
        for (circuit_name, compound_name), group in df_clean.groupby(['circuit', 'compound']):
            if len(group) < 10:  # Minimum data requirement
                continue
                
            try:
                params = self._fit_robust_regression(
                    group, lap_time_col, tire_age_col, circuit_name, compound_name
                )
                if params:
                    learned_params.append(params)
                    logger.info(f"Fitted {circuit_name}_{compound_name}: R²={params.r2:.3f}, n={params.n_samples}")
                    
            except Exception as e:
                logger.warning(f"Failed to fit {circuit_name}_{compound_name}: {e}")
                
        # Fit compound-only models (fallback level 1)
        for compound_name in df_clean['compound'].unique():
            compound_data = df_clean[df_clean['compound'] == compound_name]
            if len(compound_data) < 30:  # Higher requirement for compound-only
                continue
                
            try:
                params = self._fit_robust_regression(
                    compound_data, lap_time_col, tire_age_col, "all_circuits", compound_name
                )
                if params:
                    params.scope = ParameterScope.COMPOUND_ONLY.value
                    learned_params.append(params)
                    logger.info(f"Fitted compound-only {compound_name}: R²={params.r2:.3f}, n={params.n_samples}")
                    
            except Exception as e:
                logger.warning(f"Failed to fit compound-only {compound_name}: {e}")
                
        # Fit global model (fallback level 2)
        if len(df_clean) >= 50:  # Highest requirement for global
            try:
                params = self._fit_robust_regression(
                    df_clean, lap_time_col, tire_age_col, "all_circuits", "all_compounds"
                )
                if params:
                    params.scope = ParameterScope.GLOBAL.value
                    learned_params.append(params)
                    logger.info(f"Fitted global model: R²={params.r2:.3f}, n={params.n_samples}")
                    
            except Exception as e:
                logger.warning(f"Failed to fit global model: {e}")
        
        # Save learned parameters
        if save_params and learned_params:
            self._param_manager.save_degradation_params(learned_params)
            
        # Load parameters for current circuit/compound if specified
        if self.circuit and self.compound:
            self.load_params(self.circuit, self.compound)
            
        return self
        
    def _fit_robust_regression(
        self, 
        data: pd.DataFrame, 
        lap_time_col: str, 
        tire_age_col: str,
        circuit: str,
        compound: str
    ) -> Optional[DegradationParameters]:
        """
        Fit robust quadratic regression with k-fold cross-validation.
        
        Returns:
            DegradationParameters if successful, None if poor fit
        """
        tire_ages = data[tire_age_col].values
        lap_times = data[lap_time_col].values
        
        # Calculate baseline (5th percentile)
        baseline = np.percentile(lap_times, 5)
        lap_deltas = lap_times - baseline
        
        # Prepare design matrix: [1, age, age²]
        X = np.column_stack([
            np.ones(len(tire_ages)),
            tire_ages,
            tire_ages ** 2
        ])
        
        # Fit robust regression using iteratively reweighted least squares
        coeffs = self._robust_least_squares(X, lap_deltas)
        
        # Calculate R² and RMSE
        y_pred = X @ coeffs
        ss_res = np.sum((lap_deltas - y_pred) ** 2)
        ss_tot = np.sum((lap_deltas - np.mean(lap_deltas)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        rmse = np.sqrt(np.mean((lap_deltas - y_pred) ** 2))
        
        # K-fold cross-validation for reliability
        k_fold_r2 = self._kfold_validation(X, lap_deltas, k=5)
        
        # Quality check: use k-fold R² for reliability assessment
        if k_fold_r2 < 0.1:  # Poor predictive power
            return None
            
        return DegradationParameters(
            circuit=circuit,
            compound=compound,
            a=float(coeffs[2]),  # quadratic coefficient
            b=float(coeffs[1]),  # linear coefficient  
            c=float(coeffs[0]),  # constant
            r2=float(k_fold_r2),  # Use CV R² for reliability
            rmse=float(rmse),
            n_samples=len(data),
            scope=ParameterScope.CIRCUIT_COMPOUND.value
        )
        
    def _robust_least_squares(self, X: np.ndarray, y: np.ndarray, max_iter: int = 50) -> np.ndarray:
        """
        Iteratively reweighted least squares with Huber weights.
        
        Args:
            X: Design matrix
            y: Target values
            max_iter: Maximum iterations
            
        Returns:
            Fitted coefficients
        """
        # Initial OLS fit
        try:
            coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
        except np.linalg.LinAlgError:
            raise ValueError("Singular matrix in regression")
            
        # Iteratively reweight for robustness
        for _ in range(max_iter):
            residuals = y - X @ coeffs
            mad = np.median(np.abs(residuals - np.median(residuals)))
            
            if mad == 0:  # Perfect fit, stop
                break
                
            # Huber weights (threshold at 1.345 * MAD)
            threshold = 1.345 * mad
            weights = np.where(
                np.abs(residuals) <= threshold,
                1.0,
                threshold / np.abs(residuals)
            )
            
            # Weighted least squares
            W = np.diag(weights)
            try:
                coeffs_new = np.linalg.lstsq(X.T @ W @ X, X.T @ W @ y, rcond=None)[0]
            except np.linalg.LinAlgError:
                break  # Use previous coefficients
                
            # Check convergence
            if np.allclose(coeffs, coeffs_new, rtol=1e-6):
                break
                
            coeffs = coeffs_new
            
        return coeffs
        
    def _kfold_validation(self, X: np.ndarray, y: np.ndarray, k: int = 5) -> float:
        """
        K-fold cross-validation for model reliability assessment.
        
        Returns:
            Average R² across folds
        """
        n = len(y)
        if n < k:
            return 0.0
            
        fold_size = n // k
        r2_scores = []
        
        for i in range(k):
            # Create train/test split
            start_idx = i * fold_size
            end_idx = start_idx + fold_size if i < k - 1 else n
            
            test_idx = np.arange(start_idx, end_idx)
            train_idx = np.concatenate([np.arange(0, start_idx), np.arange(end_idx, n)])
            
            if len(train_idx) < 3:  # Need minimum training data
                continue
                
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            try:
                # Fit on training data
                coeffs = self._robust_least_squares(X_train, y_train)
                
                # Predict on test data
                y_pred = X_test @ coeffs
                
                # Calculate R²
                ss_res = np.sum((y_test - y_pred) ** 2)
                ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
                r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
                
                r2_scores.append(r2)
                
            except Exception:
                continue  # Skip failed folds
                
        return np.mean(r2_scores) if r2_scores else 0.0
        
    def load_params(self, circuit: str, compound: str) -> bool:
        """
        Load parameters for specific circuit and compound.
        
        Returns:
            True if parameters loaded successfully
        """
        params = self._param_manager.get_degradation_params(circuit, compound)
        if params:
            self.coefficients = np.array([params.c, params.b, params.a])  # [constant, linear, quadratic]
            self.r_squared = params.r2
            self.rmse = params.rmse
            self.n_samples = params.n_samples
            self.scope = params.scope
            self.fitted = True
            self.circuit = circuit
            self.compound = compound
            
            logger.debug(f"Loaded degradation params for {circuit}_{compound} "
                        f"(R²={params.r2:.3f}, scope={params.scope})")
            return True
            
        return False
        
    def fit(self, df_laps: pd.DataFrame) -> 'DegModel':
        """
        Backward compatibility method for existing code.
        Fits a simple model without circuit/compound specificity.
        """
        if df_laps.empty:
            raise ValueError("Cannot fit model with empty DataFrame")
            
        # Find required columns
        lap_time_col = self._find_column(df_laps, ['lap_time', 'lap_duration', 'laptime'])
        tire_age_col = self._find_column(df_laps, ['tire_age', 'stint_lap', 'tyre_age'])
        
        # Clean data
        df_clean = df_laps[[lap_time_col, tire_age_col]].copy()
        df_clean = df_clean.dropna()
        df_clean[lap_time_col] = pd.to_numeric(df_clean[lap_time_col], errors='coerce')
        df_clean[tire_age_col] = pd.to_numeric(df_clean[tire_age_col], errors='coerce')
        df_clean = df_clean.dropna()
        
        if len(df_clean) < 5:
            raise ValueError(f"Insufficient data for fitting. Need at least 5 valid points, got {len(df_clean)}")
            
        # Remove outliers
        df_clean = self._remove_outliers(df_clean, lap_time_col)
        
        if len(df_clean) < 5:
            raise ValueError("Insufficient data after outlier removal")
            
        # Extract features and target
        tire_ages = df_clean[tire_age_col].values
        lap_times = df_clean[lap_time_col].values
        
        # Use baseline as 5th percentile
        self.baseline_time = np.percentile(lap_times, 5)
        lap_deltas = lap_times - self.baseline_time
        
        # Fit quadratic model using robust regression
        X = np.column_stack([
            np.ones(len(tire_ages)),
            tire_ages,
            tire_ages ** 2
        ])
        
        self.coefficients = self._robust_least_squares(X, lap_deltas)
        
        # Calculate metrics
        y_pred = X @ self.coefficients
        ss_res = np.sum((lap_deltas - y_pred) ** 2)
        ss_tot = np.sum((lap_deltas - np.mean(lap_deltas)) ** 2)
        
        if ss_tot > 0:
            self.r_squared = 1 - (ss_res / ss_tot)
        else:
            self.r_squared = 0.0
            
        self.rmse = np.sqrt(np.mean((lap_deltas - y_pred) ** 2))
        self.n_samples = len(df_clean)
        self.fitted = True
        
        logger.info(f"Degradation model fitted with R² = {self.r_squared:.3f}")
        return self
        
    def predict(self, age: float) -> float:
        """
        Predict lap time delta for a given tire age.
        
        Args:
            age: Tire age in laps (can be fractional)
            
        Returns:
            Predicted lap time delta in seconds
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before making predictions")
            
        if age < 0:
            age = 0
            
        # Apply quadratic model: delta = c + b*age + a*age²
        delta = (
            self.coefficients[0] +
            self.coefficients[1] * age +
            self.coefficients[2] * age * age
        )
        
        return max(0.0, delta)
        
    def predict_batch(self, ages: np.ndarray) -> np.ndarray:
        """
        Predict lap time deltas for multiple tire ages.
        
        Args:
            ages: Array of tire ages in laps
            
        Returns:
            Array of predicted lap time deltas in seconds
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before making predictions")
            
        ages = np.asarray(ages)
        ages = np.maximum(ages, 0)  # Ensure non-negative ages
        
        # Vectorized quadratic prediction
        deltas = (
            self.coefficients[0] +
            self.coefficients[1] * ages +
            self.coefficients[2] * ages * ages
        )
        
        return np.maximum(deltas, 0.0)  # Ensure non-negative degradation
        
    def get_fresh_tire_advantage(self, old_age: float, new_age: float = 1.0) -> float:
        """
        Calculate expected advantage of fresh tires vs old tires.
        
        Args:
            old_age: Age of old tires
            new_age: Age of new tires (typically 1-3 laps)
            
        Returns:
            Expected time advantage in seconds
        """
        if not self.fitted:
            return 0.0  # No advantage if no model
            
        old_delta = self.predict(old_age)
        new_delta = self.predict(new_age)
        
        return max(0.0, old_delta - new_delta)
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the fitted model."""
        if not self.fitted:
            return {
                "fitted": False,
                "error": "Model has not been fitted yet"
            }
            
        return {
            "fitted": True,
            "r_squared": float(self.r_squared) if self.r_squared is not None else None,
            "rmse": float(self.rmse) if self.rmse is not None else None,
            "n_samples": self.n_samples,
            "circuit": self.circuit,
            "compound": self.compound,
            "scope": self.scope,
            "coefficients": {
                "constant": float(self.coefficients[0]) if self.coefficients is not None else None,
                "linear": float(self.coefficients[1]) if self.coefficients is not None else None,
                "quadratic": float(self.coefficients[2]) if self.coefficients is not None else None
            }
        }
        
    def plot_degradation_curve(self, max_age: int = 40) -> Dict[str, Any]:
        """
        Generate data for plotting the degradation curve.
        
        Args:
            max_age: Maximum tire age for the curve
            
        Returns:
            Dictionary with age and delta arrays for plotting
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before plotting")
            
        ages = np.linspace(0, max_age, 100)
        deltas = self.predict_batch(ages)
        
        return {
            "ages": ages.tolist(),
            "deltas": deltas.tolist(),
            "baseline_time": float(self.baseline_time) if self.baseline_time else 0.0,
            "max_degradation": float(np.max(deltas))
        }
        
    def _find_column(self, df: pd.DataFrame, candidates: List[str]) -> str:
        """Find the first matching column from candidates."""
        for col in candidates:
            if col in df.columns:
                return col
        raise ValueError(f"None of the required columns found: {candidates}")
        
    def _remove_outliers(self, df: pd.DataFrame, lap_time_col: str) -> pd.DataFrame:
        """Remove obvious outliers from lap time data."""
        lap_times = df[lap_time_col]
        
        # Remove times outside reasonable F1 range
        df = df[(lap_times >= 60) & (lap_times <= 200)]
        
        if df.empty:
            return df
            
        # Remove statistical outliers (beyond 3 MAD)
        lap_times = df[lap_time_col]
        median_time = lap_times.median()
        mad = np.median(np.abs(lap_times - median_time))
        
        if mad > 0:
            outlier_threshold = 3 * mad
            outlier_mask = np.abs(lap_times - median_time) <= outlier_threshold
            df = df[outlier_mask]
            
        return df
        
    def fit(self, df_laps: pd.DataFrame) -> 'DegModel':
        """
        Fit the degradation model to lap time data.
        
        Expected DataFrame columns:
        - 'lap_time' or 'lap_duration': Lap time in seconds
        - 'tire_age' or 'stint_lap': Age of tire in laps (starting from 1)
        
        Args:
            df_laps: DataFrame with lap time and tire age data
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If required columns are missing or data is insufficient
        """
        if df_laps.empty:
            raise ValueError("Cannot fit model with empty DataFrame")
        
        # Determine column names (flexible naming)
        lap_time_col = None
        tire_age_col = None
        
        # Check for lap time column
        for col in ['lap_time', 'lap_duration', 'laptime']:
            if col in df_laps.columns:
                lap_time_col = col
                break
        
        # Check for tire age column  
        for col in ['tire_age', 'stint_lap', 'tyre_age']:
            if col in df_laps.columns:
                tire_age_col = col
                break
        
        if not lap_time_col:
            raise ValueError("No lap time column found. Expected 'lap_time', 'lap_duration', or 'laptime'")
        
        if not tire_age_col:
            raise ValueError("No tire age column found. Expected 'tire_age', 'stint_lap', or 'tyre_age'")
        
        # Clean and prepare data
        df_clean = df_laps[[lap_time_col, tire_age_col]].copy()
        df_clean = df_clean.dropna()
        
        # Convert to numeric and filter outliers
        df_clean[lap_time_col] = pd.to_numeric(df_clean[lap_time_col], errors='coerce')
        df_clean[tire_age_col] = pd.to_numeric(df_clean[tire_age_col], errors='coerce')
        df_clean = df_clean.dropna()
        
        if len(df_clean) < 5:
            raise ValueError(f"Insufficient data for fitting. Need at least 5 valid points, got {len(df_clean)}")
        
        # Remove obvious outliers (beyond 3 standard deviations)
        lap_times = df_clean[lap_time_col]
        mean_time = lap_times.mean()
        std_time = lap_times.std()
        
        outlier_mask = np.abs(lap_times - mean_time) <= 3 * std_time
        df_clean = df_clean[outlier_mask]
        
        if len(df_clean) < 5:
            raise ValueError("Insufficient data after outlier removal")
        
        # Extract features and target
        tire_ages = df_clean[tire_age_col].values
        lap_times = df_clean[lap_time_col].values
        
        # Use baseline as the minimum lap time (fresh tire performance)
        self.baseline_time = np.percentile(lap_times, 5)  # Use 5th percentile as baseline
        
        # Calculate lap delta (degradation) relative to baseline
        lap_deltas = lap_times - self.baseline_time
        
        # Fit quadratic model: delta = a*age^2 + b*age + c
        # Use polynomial features: [1, age, age^2]
        X = np.column_stack([
            np.ones(len(tire_ages)),           # constant term
            tire_ages,                         # linear term  
            tire_ages ** 2                     # quadratic term
        ])
        
        # Use least squares to fit coefficients
        try:
            self.coefficients = np.linalg.lstsq(X, lap_deltas, rcond=None)[0]
        except np.linalg.LinAlgError:
            raise ValueError("Failed to fit model due to singular matrix")
        
        # Calculate R-squared for goodness of fit
        y_pred = X @ self.coefficients
        ss_res = np.sum((lap_deltas - y_pred) ** 2)
        ss_tot = np.sum((lap_deltas - np.mean(lap_deltas)) ** 2)
        
        if ss_tot > 0:
            self.r_squared = 1 - (ss_res / ss_tot)
        else:
            self.r_squared = 0.0
        
        self.fitted = True
        
        logger.info(f"Degradation model fitted with R² = {self.r_squared:.3f}")
        logger.info(f"Coefficients: c={self.coefficients[0]:.4f}, b={self.coefficients[1]:.4f}, a={self.coefficients[2]:.4f}")
        
        return self
    
    def predict(self, age: float) -> float:
        """
        Predict lap time delta for a given tire age.
        
        Args:
            age: Tire age in laps (can be fractional)
            
        Returns:
            Predicted lap time delta in seconds (additional time vs baseline)
            
        Raises:
            RuntimeError: If model hasn't been fitted
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before making predictions")
        
        if age < 0:
            age = 0
        
        # Apply quadratic model: delta = c + b*age + a*age^2
        delta = (self.coefficients[0] + 
                self.coefficients[1] * age + 
                self.coefficients[2] * age * age)
        
        # Ensure non-negative degradation
        return max(0.0, delta)
    
    def predict_batch(self, ages: np.ndarray) -> np.ndarray:
        """
        Predict lap time deltas for multiple tire ages.
        
        Args:
            ages: Array of tire ages in laps
            
        Returns:
            Array of predicted lap time deltas in seconds
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before making predictions")
        
        ages = np.asarray(ages)
        ages = np.maximum(ages, 0)  # Ensure non-negative ages
        
        # Vectorized quadratic prediction
        deltas = (self.coefficients[0] + 
                 self.coefficients[1] * ages + 
                 self.coefficients[2] * ages * ages)
        
        return np.maximum(deltas, 0.0)  # Ensure non-negative degradation
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the fitted model.
        
        Returns:
            Dictionary with model statistics and parameters
        """
        if not self.fitted:
            return {"fitted": False, "error": "Model not fitted"}
        
        return {
            "fitted": True,
            "coefficients": {
                "constant": float(self.coefficients[0]),
                "linear": float(self.coefficients[1]), 
                "quadratic": float(self.coefficients[2])
            },
            "baseline_time": float(self.baseline_time),
            "r_squared": float(self.r_squared),
            "model_type": "quadratic",
            "formula": "lap_delta = {:.4f} + {:.4f}*age + {:.4f}*age²".format(
                self.coefficients[0], self.coefficients[1], self.coefficients[2]
            )
        }
    
    def plot_degradation_curve(self, max_age: int = 40) -> Dict[str, Any]:
        """
        Generate data for plotting the degradation curve.
        
        Args:
            max_age: Maximum tire age for the curve
            
        Returns:
            Dictionary with age and delta arrays for plotting
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before plotting")
        
        ages = np.linspace(0, max_age, 100)
        deltas = self.predict_batch(ages)
        
        return {
            "ages": ages.tolist(),
            "deltas": deltas.tolist(),
            "baseline_time": float(self.baseline_time),
            "max_degradation": float(np.max(deltas))
        }