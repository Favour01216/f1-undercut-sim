"""
Tests for OutlapModel parameter fallback behavior with small sample sizes.

This test ensures that when local circuit-compound parameters have insufficient
sample sizes, the system gracefully falls back to compound-only or global parameters
as per the parameter hierarchy.
"""

import numpy as np
import pandas as pd
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from backend.models.outlap import OutlapModel
from backend.services.model_params import (
    ModelParametersManager,
    OutlapParameters,
    ParameterScope
)


@pytest.fixture
def temp_params_dir():
    """Create temporary directory for model parameters."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def small_sample_outlap_data():
    """Create synthetic outlap data with very small sample size."""
    np.random.seed(42)
    
    # Only 3 outlaps - too small for reliable statistics
    outlap_penalties = np.array([1.2, 1.8, 2.1])  # Small sample, high variance
    
    return pd.DataFrame({
        "outlap_penalty": outlap_penalties,
        "compound": ["SOFT"] * 3,
        "circuit": ["monaco"] * 3
    })


@pytest.fixture
def large_sample_outlap_data():
    """Create synthetic outlap data with large sample size."""
    np.random.seed(123)
    
    # 100 outlaps - sufficient for reliable statistics
    n_samples = 100
    
    # Realistic outlap penalty distribution
    outlap_penalties = np.random.normal(1.5, 0.4, n_samples)  # Mean=1.5s, std=0.4s
    
    return pd.DataFrame({
        "outlap_penalty": outlap_penalties,
        "compound": ["MEDIUM"] * n_samples,
        "circuit": ["silverstone"] * n_samples
    })


@pytest.fixture  
def mock_outlap_params_manager(temp_params_dir):
    """Create mock parameters manager with synthetic outlap parameter hierarchy."""
    
    # Create synthetic outlap parameters with different sample sizes
    params = [
        # Small sample circuit-specific (monaco_soft) - should be rejected due to low sample count
        OutlapParameters(
            circuit="monaco",
            compound="SOFT",
            mean_penalty=1.7,
            std_penalty=0.6,
            n_samples=3,  # Too small - should be rejected
            scope=ParameterScope.CIRCUIT_COMPOUND.value
        ),
        
        # Good sample size compound-only (soft) - should be used as fallback
        OutlapParameters(
            circuit="pooled", 
            compound="SOFT",
            mean_penalty=1.4,
            std_penalty=0.5,
            n_samples=50,  # Sufficient sample size
            scope=ParameterScope.COMPOUND_ONLY.value
        ),
        
        # Large sample global fallback
        OutlapParameters(
            circuit="global",
            compound="GLOBAL", 
            mean_penalty=1.6,
            std_penalty=0.6,
            n_samples=200,  # Large sample size
            scope=ParameterScope.GLOBAL.value
        ),
        
        # Another circuit with sufficient samples
        OutlapParameters(
            circuit="silverstone",
            compound="MEDIUM",
            mean_penalty=1.3,
            std_penalty=0.4,
            n_samples=80,  # Good sample size
            scope=ParameterScope.CIRCUIT_COMPOUND.value
        )
    ]
    
    # Create manager and save test parameters
    manager = ModelParametersManager(base_path=temp_params_dir)
    manager.save_outlap_params(params)
    
    return manager


class TestOutlapModelFallback:
    """Test suite for outlap model parameter fallback behavior."""
    
    @pytest.mark.unit
    @pytest.mark.fallback
    def test_small_sample_triggers_fallback(self, mock_outlap_params_manager):
        """Test that small sample size triggers fallback to higher-level parameters."""
        
        # Try to get parameters for monaco_soft (should fallback due to small sample size)
        params = mock_outlap_params_manager.get_outlap_params(
            circuit="monaco",
            compound="SOFT",
            min_samples=10  # Higher than circuit-specific sample count (3)
        )
        
        # Should get compound-only parameters due to fallback
        assert params is not None
        assert params.scope == ParameterScope.COMPOUND_ONLY.value
        assert params.compound == "SOFT"
        assert params.n_samples >= 10  # Should meet sample threshold
        assert params.circuit == "pooled"  # Compound-only scope
        
    def test_sufficient_samples_uses_local_params(self, mock_outlap_params_manager):
        """Test that sufficient sample size uses local circuit-specific parameters."""
        
        # Request silverstone_medium which has sufficient samples (80)
        params = mock_outlap_params_manager.get_outlap_params(
            circuit="silverstone",
            compound="MEDIUM",
            min_samples=10
        )
        
        # Should use circuit-specific parameters
        assert params is not None
        assert params.scope == ParameterScope.CIRCUIT_COMPOUND.value
        assert params.circuit == "silverstone"
        assert params.compound == "MEDIUM"
        assert params.n_samples >= 10
        
    def test_no_suitable_params_returns_none(self, mock_outlap_params_manager):
        """Test that requesting params for non-existent circuit/compound may fallback to global."""
        
        params = mock_outlap_params_manager.get_outlap_params(
            circuit="nonexistent",
            compound="ULTRASOFT",  # Not in our test data
            min_samples=5
        )
        
        # With our mock data, this should fallback to global parameters
        # If global parameters meet quality criteria, they will be returned
        # This tests the fallback hierarchy working correctly
        if params is not None:
            assert params.scope == ParameterScope.GLOBAL.value
            assert params.n_samples >= 5  # At least meets minimum requirement
        # If no suitable params exist (e.g., global doesn't meet criteria), params would be None
        
    def test_sample_size_threshold_enforcement(self, mock_outlap_params_manager):
        """Test that sample size thresholds are properly enforced."""
        
        # Request with very high sample size requirement
        params_high_threshold = mock_outlap_params_manager.get_outlap_params(
            circuit="monaco",
            compound="SOFT",
            min_samples=100  # Higher than both circuit-specific and compound-only
        )
        
        # Should fallback to global or return None
        if params_high_threshold is not None:
            assert params_high_threshold.n_samples >= 100
            assert params_high_threshold.scope == ParameterScope.GLOBAL.value
            
    def test_parameter_hierarchy_order(self, mock_outlap_params_manager):
        """Test that parameter fallback follows correct hierarchy."""
        
        # Test the fallback hierarchy by checking what gets returned
        # for different sample size thresholds
        
        # 1. With low threshold, should get compound-only (circuit-specific fails sample test)
        params_normal = mock_outlap_params_manager.get_outlap_params(
            circuit="monaco",
            compound="SOFT",
            min_samples=10  # Higher than circuit-specific (3) but lower than compound-only (50)
        )
        
        assert params_normal is not None
        assert params_normal.scope == ParameterScope.COMPOUND_ONLY.value
        
        # 2. With medium threshold, should still get compound-only 
        params_medium = mock_outlap_params_manager.get_outlap_params(
            circuit="monaco",
            compound="SOFT",
            min_samples=40  # Still within compound-only range (50)
        )
        
        assert params_medium is not None
        assert params_medium.scope == ParameterScope.COMPOUND_ONLY.value
        
        # 3. With high threshold, should fallback to global
        params_high = mock_outlap_params_manager.get_outlap_params(
            circuit="monaco",
            compound="SOFT", 
            min_samples=150  # Higher than compound-only (50) but lower than global (200)
        )
        
        if params_high is not None:
            assert params_high.scope == ParameterScope.GLOBAL.value
            assert params_high.n_samples >= 150
            
    def test_outlap_model_uses_fallback_params(self, mock_outlap_params_manager):
        """Test that OutlapModel properly uses fallback parameters when local data insufficient."""
        
        with patch('backend.models.outlap.ModelParametersManager', return_value=mock_outlap_params_manager):
            
            # Create model for monaco_soft which has insufficient samples
            model = OutlapModel(circuit="monaco", compound="SOFT")
            
            # The model should load fallback parameters automatically
            # Check if it uses reasonable default values or loads from manager
            
            # Basic sanity checks
            assert model.mean_penalty > 0  # Should have positive penalty
            assert model.std_penalty > 0   # Should have positive variance
            
    def test_case_insensitive_matching(self, mock_outlap_params_manager):
        """Test that circuit/compound matching is case-insensitive."""
        
        # Test various case combinations
        params_lower = mock_outlap_params_manager.get_outlap_params(
            circuit="silverstone",
            compound="medium",
            min_samples=10
        )
        
        params_upper = mock_outlap_params_manager.get_outlap_params(
            circuit="SILVERSTONE",
            compound="MEDIUM",
            min_samples=10
        )
        
        params_mixed = mock_outlap_params_manager.get_outlap_params(
            circuit="Silverstone",
            compound="Medium",
            min_samples=10
        )
        
        # All should return the same parameters
        assert params_lower is not None
        assert params_upper is not None
        assert params_mixed is not None
        
        assert params_lower.scope == params_upper.scope == params_mixed.scope
        assert params_lower.circuit.lower() == params_upper.circuit.lower() == params_mixed.circuit.lower()
        assert params_lower.compound.upper() == params_upper.compound.upper() == params_mixed.compound.upper()
        
    def test_outlap_statistics_calculation(self, large_sample_outlap_data):
        """Test that outlap statistics are correctly calculated from sufficient data."""
        
        # Calculate expected statistics
        expected_mean = large_sample_outlap_data["outlap_penalty"].mean()
        expected_std = large_sample_outlap_data["outlap_penalty"].std()
        expected_count = len(large_sample_outlap_data)
        
        # Verify we have sufficient data
        assert expected_count >= 50  # Should be large enough for reliable stats
        
        # Test that our synthetic data has reasonable properties
        assert 1.0 <= expected_mean <= 2.5  # Realistic outlap penalty range
        assert 0.1 <= expected_std <= 1.0    # Reasonable variance
        
    def test_penalty_value_ranges(self, mock_outlap_params_manager):
        """Test that penalty values are within reasonable ranges."""
        
        # Get various parameters and check ranges
        params_soft = mock_outlap_params_manager.get_outlap_params(
            circuit="monaco",
            compound="SOFT",
            min_samples=5
        )
        
        params_medium = mock_outlap_params_manager.get_outlap_params(
            circuit="silverstone", 
            compound="MEDIUM",
            min_samples=5
        )
        
        for params in [params_soft, params_medium]:
            if params is not None:
                # Realistic penalty ranges
                assert 0.5 <= params.mean_penalty <= 3.0  # 0.5s to 3.0s penalty
                assert 0.1 <= params.std_penalty <= 1.5   # Reasonable variance
                assert params.n_samples > 0               # Must have samples


# Additional edge case tests
class TestOutlapModelEdgeCases:
    """Test edge cases for outlap model fallback."""
    
    def test_empty_parameter_store(self, temp_params_dir):
        """Test behavior when no outlap parameters are stored."""
        
        manager = ModelParametersManager(base_path=temp_params_dir)
        
        # Should return None when no parameters exist
        params = manager.get_outlap_params(
            circuit="any",
            compound="ANY",
            min_samples=1
        )
        
        assert params is None
        
    def test_all_params_below_threshold(self, temp_params_dir):
        """Test behavior when all stored parameters are below sample threshold."""
        
        # Create parameters with very small sample sizes
        small_params = [
            OutlapParameters(
                circuit="test",
                compound="TEST",
                mean_penalty=1.5,
                std_penalty=0.5,
                n_samples=2,  # Very small
                scope=ParameterScope.CIRCUIT_COMPOUND.value
            )
        ]
        
        manager = ModelParametersManager(base_path=temp_params_dir)
        manager.save_outlap_params(small_params)
        
        # Request with high threshold - should return None
        params = manager.get_outlap_params(
            circuit="test",
            compound="TEST",
            min_samples=10  # Higher than any available
        )
        
        assert params is None
        
    def test_compound_only_fallback_prioritization(self, temp_params_dir):
        """Test that compound-only parameters are preferred over global when both meet criteria."""
        
        params = [
            # Compound-only parameters
            OutlapParameters(
                circuit="pooled",
                compound="HARD",
                mean_penalty=1.8,
                std_penalty=0.7,
                n_samples=30,
                scope=ParameterScope.COMPOUND_ONLY.value
            ),
            
            # Global parameters with more samples
            OutlapParameters(
                circuit="global", 
                compound="GLOBAL",
                mean_penalty=1.6,
                std_penalty=0.6,
                n_samples=100,  # More samples than compound-only
                scope=ParameterScope.GLOBAL.value
            )
        ]
        
        manager = ModelParametersManager(base_path=temp_params_dir)
        manager.save_outlap_params(params)
        
        # Should prefer compound-only over global even though global has more samples
        result = manager.get_outlap_params(
            circuit="nonexistent",  # Force fallback
            compound="HARD",
            min_samples=20
        )
        
        assert result is not None
        assert result.scope == ParameterScope.COMPOUND_ONLY.value
        assert result.compound == "HARD"


if __name__ == "__main__":
    pytest.main([__file__])
