"""
Test fixtures for synthetic model parameters.

This module provides test fixtures that generate synthetic model parameters
for use in CI environments where network access is disabled.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List
import tempfile
import shutil

from backend.services.model_params import (
    ModelParametersManager,
    DegradationParameters,
    OutlapParameters,
    ParameterScope
)


def create_synthetic_degradation_params() -> List[DegradationParameters]:
    """
    Create synthetic degradation parameters for testing.
    
    Returns realistic parameter distributions across different circuits
    and compounds with varying quality levels to test fallback behavior.
    """
    params = []
    
    # Define test circuits and compounds
    circuits = ["monaco", "silverstone", "monza", "spa", "suzuka"]
    compounds = ["SOFT", "MEDIUM", "HARD"]
    
    # Set seed for reproducible test data
    np.random.seed(42)
    
    for circuit in circuits:
        for compound in compounds:
            # Circuit-specific parameters (some good, some poor quality)
            r2 = np.random.uniform(0.02, 0.85)  # Wide range of R² values
            
            # Realistic degradation coefficients
            a = np.random.uniform(0.001, 0.005)  # Quadratic term
            b = np.random.uniform(0.03, 0.08)    # Linear term  
            c = np.random.uniform(89.0, 91.0)    # Baseline time
            
            rmse = np.random.uniform(0.2, 1.0)
            n_samples = np.random.randint(15, 200)
            
            params.append(DegradationParameters(
                circuit=circuit,
                compound=compound,
                a=a,
                b=b,
                c=c,
                r2=r2,
                rmse=rmse,
                n_samples=n_samples,
                scope=ParameterScope.CIRCUIT_COMPOUND.value
            ))
    
    # Add compound-only parameters (pooled across circuits)
    for compound in compounds:
        params.append(DegradationParameters(
            circuit="pooled",
            compound=compound,
            a=np.random.uniform(0.002, 0.004),
            b=np.random.uniform(0.04, 0.06),
            c=np.random.uniform(89.5, 90.5),
            r2=np.random.uniform(0.15, 0.45),  # Generally decent quality
            rmse=np.random.uniform(0.3, 0.7),
            n_samples=np.random.randint(80, 300),
            scope=ParameterScope.COMPOUND_ONLY.value
        ))
    
    # Add global parameters (fallback)
    params.append(DegradationParameters(
        circuit="global",
        compound="GLOBAL",
        a=0.003,
        b=0.05,
        c=90.0,
        r2=0.25,  # Moderate quality
        rmse=0.5,
        n_samples=500,
        scope=ParameterScope.GLOBAL.value
    ))
    
    return params


def create_synthetic_outlap_params() -> List[OutlapParameters]:
    """
    Create synthetic outlap parameters for testing.
    
    Returns realistic outlap penalty distributions across different circuits
    and compounds with varying sample sizes to test fallback behavior.
    """
    params = []
    
    circuits = ["monaco", "silverstone", "monza", "spa", "suzuka"]
    compounds = ["SOFT", "MEDIUM", "HARD"]
    
    np.random.seed(123)  # Different seed from degradation
    
    for circuit in circuits:
        for compound in compounds:
            # Circuit-specific parameters with varying sample sizes
            n_samples = np.random.randint(3, 150)  # Some too small, some adequate
            
            # Realistic outlap penalties by compound
            if compound == "SOFT":
                mean_penalty = np.random.uniform(0.8, 1.2)
                std_penalty = np.random.uniform(0.3, 0.5)
            elif compound == "MEDIUM":
                mean_penalty = np.random.uniform(1.2, 1.6)
                std_penalty = np.random.uniform(0.4, 0.6)
            else:  # HARD
                mean_penalty = np.random.uniform(1.8, 2.4)
                std_penalty = np.random.uniform(0.5, 0.8)
            
            params.append(OutlapParameters(
                circuit=circuit,
                compound=compound,
                mean_penalty=mean_penalty,
                std_penalty=std_penalty,
                n_samples=n_samples,
                scope=ParameterScope.CIRCUIT_COMPOUND.value
            ))
    
    # Add compound-only parameters (larger sample sizes)
    for compound in compounds:
        if compound == "SOFT":
            mean_penalty = 1.0
            std_penalty = 0.4
        elif compound == "MEDIUM":
            mean_penalty = 1.4
            std_penalty = 0.5
        else:  # HARD
            mean_penalty = 2.1
            std_penalty = 0.7
            
        params.append(OutlapParameters(
            circuit="pooled",
            compound=compound,
            mean_penalty=mean_penalty,
            std_penalty=std_penalty,
            n_samples=np.random.randint(50, 200),
            scope=ParameterScope.COMPOUND_ONLY.value
        ))
    
    # Add global parameters
    params.append(OutlapParameters(
        circuit="global",
        compound="GLOBAL",
        mean_penalty=1.5,
        std_penalty=0.6,
        n_samples=300,
        scope=ParameterScope.GLOBAL.value
    ))
    
    return params


def setup_test_model_params(test_dir: Path) -> ModelParametersManager:
    """
    Set up synthetic model parameters for testing.
    
    Args:
        test_dir: Directory to store test parameter files
        
    Returns:
        Configured ModelParametersManager with synthetic data
    """
    # Create model_params subdirectory
    params_dir = test_dir / "model_params"
    params_dir.mkdir(parents=True, exist_ok=True)
    
    # Create manager
    manager = ModelParametersManager(base_dir=test_dir)
    
    # Generate and save synthetic parameters
    deg_params = create_synthetic_degradation_params()
    outlap_params = create_synthetic_outlap_params()
    
    manager.save_degradation_params(deg_params)
    manager.save_outlap_params(outlap_params)
    
    return manager


def setup_minimal_model_params(test_dir: Path) -> ModelParametersManager:
    """
    Set up minimal model parameters for lightweight testing.
    
    Creates just enough parameters to test basic functionality without
    overwhelming the test environment.
    """
    params_dir = test_dir / "model_params"
    params_dir.mkdir(parents=True, exist_ok=True)
    
    manager = ModelParametersManager(base_dir=test_dir)
    
    # Minimal degradation parameters
    deg_params = [
        # One poor quality circuit-specific
        DegradationParameters(
            circuit="monaco",
            compound="SOFT",
            a=0.003,
            b=0.05,
            c=90.0,
            r2=0.05,  # Poor quality
            rmse=0.8,
            n_samples=10,
            scope=ParameterScope.CIRCUIT_COMPOUND.value
        ),
        
        # One good quality compound-only
        DegradationParameters(
            circuit="pooled",
            compound="SOFT",
            a=0.002,
            b=0.06,
            c=89.5,
            r2=0.35,  # Good quality
            rmse=0.4,
            n_samples=100,
            scope=ParameterScope.COMPOUND_ONLY.value
        ),
        
        # Global fallback
        DegradationParameters(
            circuit="global",
            compound="GLOBAL",
            a=0.0025,
            b=0.055,
            c=90.2,
            r2=0.25,
            rmse=0.5,
            n_samples=200,
            scope=ParameterScope.GLOBAL.value
        )
    ]
    
    # Minimal outlap parameters
    outlap_params = [
        # Small sample circuit-specific
        OutlapParameters(
            circuit="monaco",
            compound="SOFT",
            mean_penalty=1.2,
            std_penalty=0.4,
            n_samples=3,  # Too small
            scope=ParameterScope.CIRCUIT_COMPOUND.value
        ),
        
        # Good sample compound-only
        OutlapParameters(
            circuit="pooled",
            compound="SOFT",
            mean_penalty=1.0,
            std_penalty=0.3,
            n_samples=50,
            scope=ParameterScope.COMPOUND_ONLY.value
        ),
        
        # Global fallback
        OutlapParameters(
            circuit="global",
            compound="GLOBAL",
            mean_penalty=1.4,
            std_penalty=0.5,
            n_samples=150,
            scope=ParameterScope.GLOBAL.value
        )
    ]
    
    manager.save_degradation_params(deg_params)
    manager.save_outlap_params(outlap_params)
    
    return manager


# Test utilities for CI
def validate_test_environment():
    """
    Validate that the test environment is properly configured.
    
    Checks for required environment variables and offline mode.
    """
    import os
    
    # Check that OFFLINE mode is enabled
    offline = os.getenv("OFFLINE", "0")
    if offline != "1":
        raise EnvironmentError(
            "Tests should run in OFFLINE=1 mode in CI environment. "
            "Set OFFLINE=1 environment variable."
        )
    
    # Check for test-specific environment
    env = os.getenv("ENV", "")
    if env.lower() not in ["test", "ci"]:
        print(f"Warning: ENV={env} may not be appropriate for testing")
    
    return True


if __name__ == "__main__":
    # Demo script to generate test parameters
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        
        print("Creating synthetic degradation parameters...")
        deg_params = create_synthetic_degradation_params()
        print(f"Created {len(deg_params)} degradation parameter sets")
        
        print("Creating synthetic outlap parameters...")
        outlap_params = create_synthetic_outlap_params()
        print(f"Created {len(outlap_params)} outlap parameter sets")
        
        print("Setting up test model manager...")
        manager = setup_test_model_params(test_path)
        
        print("Parameter summary:")
        summary = manager.get_parameter_summary()
        print(f"  Degradation: {summary['degradation']}")
        print(f"  Outlap: {summary['outlap']}")
        
        print(f"Test parameters created in: {test_path}")