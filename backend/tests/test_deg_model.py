"""
Tests for DegModel (Tire Degradation Model)
"""

import pytest
import numpy as np
import pandas as pd
from backend.models.deg import DegModel


@pytest.fixture
def sample_lap_data():
    """Create sample lap data for testing."""
    # Simulate realistic tire degradation data
    np.random.seed(42)
    n_laps = 50
    
    # Quadratic degradation: base_time + 0.05*age + 0.002*age^2 + noise
    tire_ages = np.arange(1, n_laps + 1)
    base_time = 90.0
    degradation = 0.05 * tire_ages + 0.002 * tire_ages**2
    noise = np.random.normal(0, 0.1, n_laps)
    
    lap_times = base_time + degradation + noise
    
    return pd.DataFrame({
        'lap_time': lap_times,
        'tire_age': tire_ages
    })


@pytest.fixture
def minimal_data():
    """Minimal valid dataset."""
    return pd.DataFrame({
        'lap_time': [90.0, 90.5, 91.2, 92.0, 93.1],
        'tire_age': [1, 2, 3, 4, 5]
    })


class TestDegModel:
    """Test suite for DegModel."""
    
    def test_initialization(self):
        """Test model initialization."""
        model = DegModel()
        assert model.coefficients is None
        assert model.baseline_time is None
        assert not model.fitted
        assert model.r_squared is None
    
    def test_fit_valid_data(self, sample_lap_data):
        """Test fitting with valid data."""
        model = DegModel()
        result = model.fit(sample_lap_data)
        
        # Should return self for chaining
        assert result is model
        
        # Model should be fitted
        assert model.fitted
        assert model.coefficients is not None
        assert len(model.coefficients) == 3  # constant, linear, quadratic
        assert model.baseline_time is not None
        assert model.r_squared is not None
        
        # R-squared should be reasonable for synthetic data
        assert model.r_squared > 0.8
    
    def test_fit_empty_dataframe(self):
        """Test fitting with empty DataFrame."""
        model = DegModel()
        
        with pytest.raises(ValueError, match="empty DataFrame"):
            model.fit(pd.DataFrame())
    
    def test_fit_missing_columns(self):
        """Test fitting with missing required columns."""
        model = DegModel()
        df = pd.DataFrame({'wrong_col': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="No lap time column"):
            model.fit(df)
    
    def test_fit_insufficient_data(self):
        """Test fitting with insufficient data points."""
        model = DegModel()
        df = pd.DataFrame({
            'lap_time': [90.0, 90.5],
            'tire_age': [1, 2]
        })
        
        with pytest.raises(ValueError, match="Insufficient data"):
            model.fit(df)
    
    def test_alternative_column_names(self):
        """Test fitting with alternative column names."""
        model = DegModel()
        df = pd.DataFrame({
            'lap_duration': [90.0, 90.5, 91.0, 91.8, 92.5],
            'stint_lap': [1, 2, 3, 4, 5]
        })
        
        model.fit(df)
        assert model.fitted
    
    def test_predict_before_fitting(self):
        """Test prediction before model is fitted."""
        model = DegModel()
        
        with pytest.raises(RuntimeError, match="must be fitted"):
            model.predict(10)
    
    def test_predict_single_value(self, minimal_data):
        """Test prediction for single tire age."""
        model = DegModel()
        model.fit(minimal_data)
        
        prediction = model.predict(10)
        assert isinstance(prediction, float)
        assert prediction >= 0  # Should never be negative
    
    def test_predict_negative_age(self, minimal_data):
        """Test prediction with negative age (should clamp to 0)."""
        model = DegModel()
        model.fit(minimal_data)
        
        prediction = model.predict(-5)
        zero_prediction = model.predict(0)
        assert prediction == zero_prediction
    
    def test_predict_batch(self, minimal_data):
        """Test batch prediction."""
        model = DegModel()
        model.fit(minimal_data)
        
        ages = np.array([1, 5, 10, 20])
        predictions = model.predict_batch(ages)
        
        assert len(predictions) == len(ages)
        assert all(p >= 0 for p in predictions)  # All non-negative
        assert predictions[0] <= predictions[-1]  # Generally increasing
    
    def test_get_model_info_before_fitting(self):
        """Test getting model info before fitting."""
        model = DegModel()
        info = model.get_model_info()
        
        assert not info['fitted']
        assert 'error' in info
    
    def test_get_model_info_after_fitting(self, minimal_data):
        """Test getting model info after fitting."""
        model = DegModel()
        model.fit(minimal_data)
        info = model.get_model_info()
        
        assert info['fitted']
        assert 'coefficients' in info
        assert 'baseline_time' in info
        assert 'r_squared' in info
        assert 'formula' in info
        assert info['model_type'] == 'quadratic'
    
    def test_plot_data_generation(self, minimal_data):
        """Test plot data generation."""
        model = DegModel()
        model.fit(minimal_data)
        
        plot_data = model.plot_degradation_curve(max_age=30)
        
        assert 'ages' in plot_data
        assert 'deltas' in plot_data
        assert 'baseline_time' in plot_data
        assert 'max_degradation' in plot_data
        assert len(plot_data['ages']) == 100  # Default resolution
        assert len(plot_data['deltas']) == 100
    
    def test_realistic_degradation_pattern(self, sample_lap_data):
        """Test that model captures realistic degradation pattern."""
        model = DegModel()
        model.fit(sample_lap_data)
        
        # Test degradation increases over time
        early_pred = model.predict(5)
        late_pred = model.predict(30)
        
        assert late_pred > early_pred
        
        # Test quadratic nature (acceleration increases)
        mid_pred = model.predict(17.5)  # Midpoint between 5 and 30
        linear_expectation = (early_pred + late_pred) / 2
        
        # Quadratic should show more degradation than linear
        assert mid_pred != linear_expectation
    
    def test_outlier_handling(self):
        """Test that model handles outliers reasonably."""
        # Create data with outliers
        normal_times = [90.0, 90.5, 91.0, 91.5, 92.0]
        outlier_times = [150.0, 20.0]  # Extreme outliers
        
        df = pd.DataFrame({
            'lap_time': normal_times + outlier_times,
            'tire_age': [1, 2, 3, 4, 5, 6, 7]
        })
        
        model = DegModel()
        model.fit(df)
        
        # Should still fit successfully
        assert model.fitted
        assert model.r_squared is not None
    
    def test_data_types_handling(self):
        """Test handling of different data types."""
        df = pd.DataFrame({
            'lap_time': ['90.0', '90.5', '91.0', '91.5', '92.0'],  # String numbers
            'tire_age': [1.0, 2.0, 3.0, 4.0, 5.0]  # Floats
        })
        
        model = DegModel()
        model.fit(df)
        
        assert model.fitted
        
    def test_method_chaining(self, minimal_data):
        """Test that fit() returns self for method chaining."""
        model = DegModel()
        
        # Should be able to chain fit() -> predict()
        prediction = model.fit(minimal_data).predict(10)
        assert isinstance(prediction, float)
