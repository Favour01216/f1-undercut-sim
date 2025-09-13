"""
Tire Degradation Model

Simple tire degradation model that fits lap time vs tire age data
and predicts performance degradation over a stint.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DegModel:
    """
    Tire degradation model for predicting lap time increases due to tire wear.

    Fits a quadratic relationship between lap time and tire age:
    lap_delta = a * age^2 + b * age + c

    Where:
    - lap_delta is the time penalty compared to optimal performance
    - age is the tire age in laps
    - a, b, c are fitted coefficients
    """

    def __init__(self):
        """Initialize the degradation model."""
        self.coefficients: np.ndarray | None = None
        self.baseline_time: float | None = None
        self.fitted: bool = False
        self.r_squared: float | None = None

    def fit(self, df_laps: pd.DataFrame) -> "DegModel":
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
        for col in ["lap_time", "lap_duration", "laptime"]:
            if col in df_laps.columns:
                lap_time_col = col
                break

        # Check for tire age column
        for col in ["tire_age", "stint_lap", "tyre_age"]:
            if col in df_laps.columns:
                tire_age_col = col
                break

        if not lap_time_col:
            raise ValueError(
                "No lap time column found. Expected 'lap_time', 'lap_duration', or 'laptime'"
            )

        if not tire_age_col:
            raise ValueError(
                "No tire age column found. Expected 'tire_age', 'stint_lap', or 'tyre_age'"
            )

        # Clean and prepare data
        df_clean = df_laps[[lap_time_col, tire_age_col]].copy()
        df_clean = df_clean.dropna()

        # Convert to numeric and filter outliers
        df_clean[lap_time_col] = pd.to_numeric(df_clean[lap_time_col], errors="coerce")
        df_clean[tire_age_col] = pd.to_numeric(df_clean[tire_age_col], errors="coerce")
        df_clean = df_clean.dropna()

        if len(df_clean) < 5:
            raise ValueError(
                f"Insufficient data for fitting. Need at least 5 valid points, got {len(df_clean)}"
            )

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
        self.baseline_time = np.percentile(
            lap_times, 5
        )  # Use 5th percentile as baseline

        # Calculate lap delta (degradation) relative to baseline
        lap_deltas = lap_times - self.baseline_time

        # Fit quadratic model: delta = a*age^2 + b*age + c
        # Use polynomial features: [1, age, age^2]
        X = np.column_stack(
            [
                np.ones(len(tire_ages)),  # constant term
                tire_ages,  # linear term
                tire_ages**2,  # quadratic term
            ]
        )

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
        logger.info(
            f"Coefficients: c={self.coefficients[0]:.4f}, b={self.coefficients[1]:.4f}, a={self.coefficients[2]:.4f}"
        )

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
        delta = (
            self.coefficients[0]
            + self.coefficients[1] * age
            + self.coefficients[2] * age * age
        )

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
        deltas = (
            self.coefficients[0]
            + self.coefficients[1] * ages
            + self.coefficients[2] * ages * ages
        )

        return np.maximum(deltas, 0.0)  # Ensure non-negative degradation

    def get_model_info(self) -> dict[str, Any]:
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
                "quadratic": float(self.coefficients[2]),
            },
            "baseline_time": float(self.baseline_time),
            "r_squared": float(self.r_squared),
            "model_type": "quadratic",
            "formula": f"lap_delta = {self.coefficients[0]:.4f} + {self.coefficients[1]:.4f}*age + {self.coefficients[2]:.4f}*age²",
        }

    def plot_degradation_curve(self, max_age: int = 40) -> dict[str, Any]:
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
            "max_degradation": float(np.max(deltas)),
        }
