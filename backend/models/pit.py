"""
Pit Stop Time Model

Simple model for pit stop time loss distribution based on historical data.
Fits a normal distribution and provides sampling for Monte Carlo simulations.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, Union
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class PitModel:
    """
    Pit stop time loss model using normal distribution.
    
    Analyzes historical pit stop data to model the distribution of time lost
    during pit stops, accounting for both the pit stop itself and position loss.
    """
    
    def __init__(self):
        """Initialize the pit stop model."""
        self.mean_loss: Optional[float] = None
        self.std_loss: Optional[float] = None
        self.fitted: bool = False
        self.sample_count: int = 0
        self.distribution: Optional[stats.norm] = None
        
    def fit(self, df_pit_events: pd.DataFrame) -> 'PitModel':
        """
        Fit the pit stop time loss model to historical data.
        
        Expected DataFrame columns:
        - 'pit_duration' or 'duration': Time spent in pit lane (seconds)
        - 'time_loss' or 'pit_loss_time': Total time lost including track position
        
        Alternative: if only pit duration is available, estimates total loss
        
        Args:
            df_pit_events: DataFrame with pit stop event data
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If required columns are missing or data is insufficient
        """
        if df_pit_events.empty:
            raise ValueError("Cannot fit model with empty DataFrame")
        
        # Determine column names (flexible naming)
        pit_duration_col = None
        time_loss_col = None
        
        # Check for pit duration column
        for col in ['pit_duration', 'duration', 'pit_time']:
            if col in df_pit_events.columns:
                pit_duration_col = col
                break
        
        # Check for total time loss column
        for col in ['time_loss', 'pit_loss_time', 'total_loss']:
            if col in df_pit_events.columns:
                time_loss_col = col
                break
        
        if not pit_duration_col and not time_loss_col:
            raise ValueError("No pit time column found. Expected 'pit_duration', 'duration', 'time_loss', or 'pit_loss_time'")
        
        # Prepare data
        if time_loss_col and time_loss_col in df_pit_events.columns:
            # Use total time loss if available
            time_losses = df_pit_events[time_loss_col].copy()
            data_source = "total_time_loss"
        elif pit_duration_col and pit_duration_col in df_pit_events.columns:
            # Estimate total loss from pit duration
            pit_durations = df_pit_events[pit_duration_col].copy()
            
            # Add typical overhead for pit stops (entry/exit, tire change delay)
            # Typical F1 pit stop: ~20-25s stationary + ~5-8s track time loss
            # Use deterministic seed for reproducible estimates
            rng = np.random.default_rng(42)
            time_losses = pit_durations + rng.normal(7, 2, len(pit_durations))
            data_source = "estimated_from_pit_duration"
        else:
            raise ValueError("Required columns not found in DataFrame")
        
        # Clean data
        time_losses = pd.to_numeric(time_losses, errors='coerce')
        time_losses = time_losses.dropna()
        
        if len(time_losses) < 3:
            raise ValueError(f"Insufficient data for fitting. Need at least 3 valid points, got {len(time_losses)}")
        
        # Remove extreme outliers (beyond 3 standard deviations)
        mean_loss = time_losses.mean()
        std_loss = time_losses.std()
        
        outlier_mask = np.abs(time_losses - mean_loss) <= 3 * std_loss
        time_losses_clean = time_losses[outlier_mask]
        
        if len(time_losses_clean) < 3:
            logger.warning("Too many outliers removed, using original data")
            time_losses_clean = time_losses
        
        # Ensure reasonable bounds for F1 pit stops (10-60 seconds total loss)
        time_losses_clean = time_losses_clean[(time_losses_clean >= 10) & (time_losses_clean <= 60)]
        
        if len(time_losses_clean) < 3:
            raise ValueError("Insufficient valid pit stop data after filtering")
        
        # Fit normal distribution
        self.mean_loss = float(time_losses_clean.mean())
        self.std_loss = float(time_losses_clean.std())
        
        # Handle edge case of zero standard deviation
        if self.std_loss < 0.1:
            self.std_loss = 1.0  # Minimum variability
        
        self.sample_count = len(time_losses_clean)
        self.distribution = stats.norm(loc=self.mean_loss, scale=self.std_loss)
        self.fitted = True
        
        logger.info(f"Pit model fitted: μ={self.mean_loss:.2f}s, σ={self.std_loss:.2f}s ({self.sample_count} samples)")
        logger.info(f"Data source: {data_source}")
        
        return self
    
    def sample(self, n: int = 1, rng: Optional[np.random.Generator] = None) -> float | np.ndarray:
        """
        Generate random pit stop time loss samples.
        
        Args:
            n: Number of samples to generate
            rng: Random number generator for reproducible results (default: None)
            
        Returns:
            Array of pit stop time losses in seconds
            
        Raises:
            RuntimeError: If model hasn't been fitted
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before sampling")
        
        if n <= 0:
            raise ValueError("Number of samples must be positive")
        
        # Use provided RNG or create deterministic default
        if rng is None:
            rng = np.random.default_rng(42)
        
        # Sample from normal distribution with deterministic RNG
        samples = rng.normal(self.mean_loss, self.std_loss, size=n)
        
        # Ensure reasonable bounds for F1 pit stops
        samples = np.clip(samples, 10.0, 60.0)
        
        return samples if n > 1 else samples[0]
    
    def probability_faster_than(self, threshold: float) -> float:
        """
        Calculate probability that a pit stop will be faster than threshold.
        
        Args:
            threshold: Time threshold in seconds
            
        Returns:
            Probability (0-1) that pit stop will be under threshold
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before calculating probabilities")
        
        return self.distribution.cdf(threshold)
    
    def get_percentiles(self, percentiles: list = [5, 25, 50, 75, 95]) -> Dict[int, float]:
        """
        Get pit stop time loss at various percentiles.
        
        Args:
            percentiles: List of percentiles to calculate
            
        Returns:
            Dictionary mapping percentiles to time values
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before calculating percentiles")
        
        result = {}
        for p in percentiles:
            if not 0 <= p <= 100:
                continue
            result[p] = float(self.distribution.ppf(p / 100))
        
        return result
    
    def simulate_pit_window(self, n_simulations: int = 1000) -> Dict[str, Any]:
        """
        Simulate a pit stop window with multiple scenarios.
        
        Args:
            n_simulations: Number of Monte Carlo simulations
            
        Returns:
            Dictionary with simulation results and statistics
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before simulation")
        
        samples = self.sample(n_simulations)
        
        return {
            "simulations": n_simulations,
            "mean_loss": float(np.mean(samples)),
            "std_loss": float(np.std(samples)),
            "min_loss": float(np.min(samples)),
            "max_loss": float(np.max(samples)),
            "percentiles": {
                "p5": float(np.percentile(samples, 5)),
                "p25": float(np.percentile(samples, 25)), 
                "p50": float(np.percentile(samples, 50)),
                "p75": float(np.percentile(samples, 75)),
                "p95": float(np.percentile(samples, 95))
            },
            "probability_under_25s": float(np.mean(samples < 25)),
            "probability_over_30s": float(np.mean(samples > 30)),
            "samples": samples.tolist()
        }
    
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
            "distribution": "normal",
            "parameters": {
                "mean_loss": float(self.mean_loss),
                "std_loss": float(self.std_loss)
            },
            "sample_count": self.sample_count,
            "typical_range": {
                "fast_pit": float(self.mean_loss - self.std_loss),
                "average_pit": float(self.mean_loss),
                "slow_pit": float(self.mean_loss + self.std_loss)
            },
            "percentiles": self.get_percentiles()
        }
    
    def compare_scenarios(self, scenarios: Dict[str, float]) -> Dict[str, Any]:
        """
        Compare different pit stop timing scenarios.
        
        Args:
            scenarios: Dict mapping scenario names to target pit times
            
        Returns:
            Dictionary with scenario analysis
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before scenario comparison")
        
        results = {}
        
        for scenario_name, target_time in scenarios.items():
            probability = self.probability_faster_than(target_time)
            results[scenario_name] = {
                "target_time": float(target_time),
                "probability_faster": float(probability),
                "probability_slower": float(1 - probability),
                "expected_advantage": float(self.mean_loss - target_time) if target_time < self.mean_loss else 0,
                "risk_level": "low" if probability > 0.7 else "medium" if probability > 0.3 else "high"
            }
        
        return {
            "scenarios": results,
            "baseline_mean": float(self.mean_loss),
            "recommendation": min(results.keys(), 
                                key=lambda k: abs(results[k]["probability_faster"] - 0.5))
        }