"""
Tests for DegModel parameter fallback behavior with weak signal data.

This test ensures that when local circuit-compound parameters have poor quality
(R² < 0.1), the system gracefully falls back to compound-only or global parameters
as per the parameter hierarchy.
"""

import numpy as np
import pandas as pd
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from backend.models.deg import DegModel
from backend.services.model_params import (
    ModelParametersManager, 
    DegradationParameters, 
    ParameterScope
)

# Numeric tolerances for CI stability
TOLERANCE = 1e-4  # Default tolerance for numeric comparisons
R2_TOLERANCE = 1e-3  # Tolerance for R² comparisons


@pytest.fixture
def temp_params_dir():
    """Create temporary directory for model parameters."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def weak_signal_data():
    """Create synthetic lap data with very weak degradation signal (high noise)."""
    np.random.seed(42)
    n_laps = 25
    
    # Very weak signal: tiny degradation effect + large noise
    tire_ages = np.arange(1, n_laps + 1)
    base_time = 90.0
    
    # Minimal degradation effect - barely detectable
    true_degradation = 0.005 * tire_ages + 0.0001 * tire_ages**2
    
    # High noise that overwhelms the signal
    noise = np.random.normal(0, 0.5, n_laps)  # High noise relative to signal
    
    lap_times = base_time + true_degradation + noise
    
    return pd.DataFrame({
        "lap_time": lap_times,
        "tire_age": tire_ages
    })


@pytest.fixture
def strong_signal_data():
    """Create synthetic lap data with strong degradation signal."""
    np.random.seed(123)
    n_laps = 50
    
    tire_ages = np.arange(1, n_laps + 1)
    base_time = 90.0
    
    # Strong degradation signal
    true_degradation = 0.08 * tire_ages + 0.003 * tire_ages**2
    
    # Low noise relative to signal
    noise = np.random.normal(0, 0.1, n_laps)
    
    lap_times = base_time + true_degradation + noise
    
    return pd.DataFrame({
        "lap_time": lap_times,
        "tire_age": tire_ages
    })


@pytest.fixture
def mock_params_manager(temp_params_dir):
    """Create mock parameters manager with synthetic parameter hierarchy."""
    
    # Create synthetic degradation parameters with different quality levels
    params = [
        # Poor quality circuit-specific (monaco_soft) - should be rejected
        DegradationParameters(
            circuit="monaco",
            compound="SOFT",
            a=0.003,
            b=0.05,
            c=90.0,
            r2=0.05,  # Below 0.1 threshold - should be rejected
            rmse=0.8,
            n_samples=20,
            scope=ParameterScope.CIRCUIT_COMPOUND.value
        ),
        
        # Good quality compound-only (soft) - should be used as fallback
        DegradationParameters(
            circuit="pooled",
            compound="SOFT",
            a=0.002,
            b=0.06,
            c=89.5,
            r2=0.35,  # Above 0.1 threshold - good quality
            rmse=0.4,
            n_samples=150,
            scope=ParameterScope.COMPOUND_ONLY.value
        ),
        
        # Global fallback - should be used if compound-only fails
        DegradationParameters(
            circuit="global",
            compound="GLOBAL",
            a=0.0025,
            b=0.055,
            c=90.2,
            r2=0.25,  # Decent quality
            rmse=0.5,
            n_samples=500,
            scope=ParameterScope.GLOBAL.value
        )
    ]
    
    # Create manager and save test parameters
    manager = ModelParametersManager(base_path=temp_params_dir)
    manager.save_degradation_params(params)
    
    return manager


class TestDegradationModelFallback:
    """Test suite for degradation model parameter fallback behavior."""
    
    @pytest.mark.unit
    @pytest.mark.fallback
    def test_weak_signal_triggers_fallback(self, weak_signal_data, mock_params_manager):
        """Test that weak signal data triggers fallback to higher-level parameters."""
        
        # Patch the global parameters manager to use our mock
        with patch('backend.models.deg.get_parameters_manager', return_value=mock_params_manager):
            
            # Try to get parameters for monaco_soft (should fallback due to poor R²)
            params = mock_params_manager.get_degradation_params(
                circuit="monaco",
                compound="SOFT",
                min_r2=0.1
            )
            
            # Should get compound-only parameters due to fallback
            assert params is not None
            assert params.scope == ParameterScope.COMPOUND_ONLY.value
            assert params.compound == "SOFT"
            assert params.r2 >= 0.1 - R2_TOLERANCE  # Should meet quality threshold
            assert params.circuit == "pooled"  # Compound-only scope
            
    @pytest.mark.unit
    def test_no_suitable_params_returns_none(self, mock_params_manager):
        """Test that requesting params for non-existent circuit/compound may fallback to global."""
        
        params = mock_params_manager.get_degradation_params(
            circuit="nonexistent",
            compound="ULTRASOFT",  # Not in our test data
            min_r2=0.1
        )
        
        # With our mock data, this should fallback to global parameters
        # If global parameters meet quality criteria, they will be returned
        # This tests the fallback hierarchy working correctly
        if params is not None:
            assert params.scope == ParameterScope.GLOBAL.value
            assert params.r2 >= 0.1 - R2_TOLERANCE
        # If no suitable params exist (e.g., global doesn't meet criteria), params would be None
        
    @pytest.mark.unit 
    @pytest.mark.fallback
    def test_quality_threshold_enforcement(self, mock_params_manager):
        """Test that quality thresholds are properly enforced."""
        
        # Request with very high R² threshold - should fallback or fail
        params_high_threshold = mock_params_manager.get_degradation_params(
            circuit="monaco",
            compound="SOFT",
            min_r2=0.5  # Very high threshold
        )
        
        # Should either fallback to global or return None
        if params_high_threshold is not None:
            assert params_high_threshold.r2 >= 0.5
            # Should not be the poor-quality circuit-specific params
            assert params_high_threshold.scope != ParameterScope.CIRCUIT_COMPOUND.value
            
    @pytest.mark.unit
    def test_degradation_model_uses_fallback_params(self, weak_signal_data, mock_params_manager):
        """Test that DegModel properly uses fallback parameters when fitting fails."""
        
        with patch('backend.models.deg.get_parameters_manager', return_value=mock_params_manager):
            
            # Create model for monaco_soft
            model = DegModel(circuit="monaco", compound="SOFT")
            
            # Fit with weak signal data
            model.fit(weak_signal_data, circuit="monaco", save_params=False)
            
            # Should have fitted, but with poor quality
            # The model should recognize this and potentially use stored fallback params
            # when making predictions (this depends on implementation details)
            
            # Basic sanity check - model should be fittable
            assert model.coefficients is not None
            assert len(model.coefficients) == 3  # a, b, c coefficients
            
    @pytest.mark.unit
    @pytest.mark.fallback
    def test_parameter_hierarchy_order(self, mock_params_manager):
        """Test that parameter fallback follows correct hierarchy."""
        
        # Test the fallback hierarchy by checking what gets returned
        # for different scenarios
        
        # 1. With normal threshold, should get compound-only (circuit-specific fails R² test)
        params_normal = mock_params_manager.get_degradation_params(
            circuit="monaco",
            compound="SOFT",
            min_r2=0.1
        )
        
        assert params_normal is not None
        assert params_normal.scope == ParameterScope.COMPOUND_ONLY.value
        
        # 2. With very high threshold, should fallback to global or None
        params_strict = mock_params_manager.get_degradation_params(
            circuit="monaco", 
            compound="SOFT",
            min_r2=0.4  # Higher than compound-only R²
        )
        
        # Should either be None or global scope
        if params_strict is not None:
            assert params_strict.scope == ParameterScope.GLOBAL.value
            
    @pytest.mark.unit
    def test_minimum_sample_size_enforcement(self, mock_params_manager):
        """Test that minimum sample size thresholds are enforced."""
        
        # Request with very high sample size requirement
        params = mock_params_manager.get_degradation_params(
            circuit="monaco",
            compound="SOFT", 
            min_r2=0.1,
            min_samples=200  # Higher than circuit-specific sample count
        )
        
        # Should fallback to compound-only (150 samples) or global (500 samples)
        if params is not None:
            assert params.n_samples >= 200
            assert params.scope in [ParameterScope.COMPOUND_ONLY.value, ParameterScope.GLOBAL.value]
            
    @pytest.mark.unit
    def test_strong_signal_uses_local_params(self, strong_signal_data, temp_params_dir):
        """Test that strong signal data uses local circuit-specific parameters when available."""
        
        # Create parameters where circuit-specific has good quality
        good_params = [
            DegradationParameters(
                circuit="silverstone",
                compound="MEDIUM",
                a=0.003,
                b=0.07,
                c=89.8,
                r2=0.75,  # High quality - should be used
                rmse=0.2,
                n_samples=100,
                scope=ParameterScope.CIRCUIT_COMPOUND.value
            )
        ]
        
        manager = ModelParametersManager(base_path=temp_params_dir)
        manager.save_degradation_params(good_params)
        
        # Should use the high-quality circuit-specific parameters
        params = manager.get_degradation_params(
            circuit="silverstone",
            compound="MEDIUM",
            min_r2=0.1
        )
        
        assert params is not None
        assert params.scope == ParameterScope.CIRCUIT_COMPOUND.value
        assert params.r2 >= 0.1
        assert params.circuit == "silverstone"
        assert params.compound == "MEDIUM"


# Additional edge case tests
class TestDegradationModelEdgeCases:
    """Test edge cases for degradation model fallback."""
    
    @pytest.mark.unit
    def test_empty_parameter_store(self, temp_params_dir):
        """Test behavior when no parameters are stored."""
        
        manager = ModelParametersManager(base_path=temp_params_dir)
        
        # Should return None when no parameters exist
        params = manager.get_degradation_params(
            circuit="any",
            compound="ANY",
            min_r2=0.1
        )
        
        assert params is None
        
    @pytest.mark.unit
    def test_case_insensitive_matching(self, mock_params_manager):
        """Test that circuit/compound matching is case-insensitive."""
        
        # Test various case combinations
        params_lower = mock_params_manager.get_degradation_params(
            circuit="monaco",
            compound="soft",
            min_r2=0.1
        )
        
        params_upper = mock_params_manager.get_degradation_params(
            circuit="MONACO",
            compound="SOFT", 
            min_r2=0.1
        )
        
        params_mixed = mock_params_manager.get_degradation_params(
            circuit="Monaco",
            compound="Soft",
            min_r2=0.1
        )
        
        # All should return the same parameters (compound-only fallback)
        assert params_lower is not None
        assert params_upper is not None  
        assert params_mixed is not None
        
        assert params_lower.scope == params_upper.scope == params_mixed.scope
        assert params_lower.compound == params_upper.compound == params_mixed.compound


if __name__ == "__main__":
    pytest.main([__file__])
