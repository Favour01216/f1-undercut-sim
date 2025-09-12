"""
Tests for the F1 Undercut Simulation Backend

This module contains unit tests for the FastAPI application and models.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Import the FastAPI app
from backend.app import app
from backend.models.deg import TireDegradationModel
from backend.models.pit import PitStopModel
from backend.models.outlap import OutlapModel


# Create test client
client = TestClient(app)


class TestApp:
    """Test the main FastAPI application."""
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "F1 Undercut Simulator API" in data["message"]
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "f1-undercut-sim-backend"
    
    @patch('backend.services.openf1.OpenF1Service.get_sessions')
    def test_get_sessions(self, mock_get_sessions):
        """Test the sessions endpoint."""
        # Mock the service response
        mock_get_sessions.return_value = [
            {
                "session_key": "9158",
                "session_name": "Race",
                "date_start": "2024-03-02T15:00:00+00:00",
                "session_type": "Race",
                "location": "Bahrain",
                "year": 2024
            }
        ]
        
        response = client.get("/api/v1/sessions?year=2024")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "year" in data
        assert data["year"] == 2024


class TestTireDegradationModel:
    """Test the tire degradation model."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.model = TireDegradationModel()
    
    def test_initialization(self):
        """Test model initialization."""
        assert self.model is not None
        assert "SOFT" in self.model.compounds
        assert "MEDIUM" in self.model.compounds
        assert "HARD" in self.model.compounds
    
    def test_analyze_empty_data(self):
        """Test analysis with empty data."""
        result = self.model.analyze({})
        assert "error" in result
    
    def test_analyze_with_data(self):
        """Test analysis with sample data."""
        session_data = {
            "lap_times": [90.5, 90.7, 90.9, 91.1],
            "tire_compounds": ["SOFT", "MEDIUM"],
            "track_temperature": 25.0
        }
        
        result = self.model.analyze(session_data)
        assert "track_temperature" in result
        assert "analyses" in result
        assert "recommendations" in result
        assert result["track_temperature"] == 25.0
    
    def test_temperature_factor_calculation(self):
        """Test temperature factor calculation."""
        soft_compound = self.model.compounds["SOFT"]
        
        # Test optimal temperature
        factor = self.model._calculate_temperature_factor(25.0, soft_compound)
        assert factor >= 1.0
        
        # Test cold temperature
        factor = self.model._calculate_temperature_factor(10.0, soft_compound)
        assert factor > 1.0
        
        # Test hot temperature
        factor = self.model._calculate_temperature_factor(50.0, soft_compound)
        assert factor > 1.0
    
    def test_performance_curve_prediction(self):
        """Test performance curve prediction."""
        curve = self.model._predict_performance_curve(20, 0.1)
        assert len(curve) == 20
        assert all(isinstance(x, float) for x in curve)
        assert curve[0] > curve[-1]  # Performance should degrade


class TestPitStopModel:
    """Test the pit stop strategy model."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.model = PitStopModel()
    
    def test_initialization(self):
        """Test model initialization."""
        assert self.model is not None
        assert self.model.pit_loss_time > 0
        assert self.model.undercut_window > 0
    
    def test_optimize_with_valid_request(self):
        """Test strategy optimization with valid request."""
        strategy_request = {
            "current_position": 5,
            "current_lap": 10,
            "total_laps": 50,
            "current_tire": "MEDIUM",
            "tire_age": 8,
            "fuel_load": 60.0,
            "weather": "dry",
            "traffic_density": 0.5
        }
        
        result = self.model.optimize(strategy_request)
        assert "current_conditions" in result
        assert "recommended_strategy" in result
        assert "alternative_strategies" in result
    
    def test_one_stop_strategy_analysis(self):
        """Test one-stop strategy analysis."""
        strategy = self.model._analyze_one_stop_strategy(10, 50, "MEDIUM", 5)
        
        assert strategy["strategy_type"] == "one_stop"
        assert "pit_windows" in strategy
        assert "expected_position_gain" in strategy
        assert "confidence" in strategy
    
    def test_undercut_advantage_calculation(self):
        """Test undercut advantage calculation."""
        advantage = self.model.calculate_undercut_advantage(8, 15, 10)
        
        assert "base_advantage_per_lap" in advantage
        assert "total_advantage" in advantage
        assert "pit_loss" in advantage
        assert "net_advantage" in advantage
        assert "success_probability" in advantage


class TestOutlapModel:
    """Test the outlap performance model."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.model = OutlapModel()
    
    def test_initialization(self):
        """Test model initialization."""
        assert self.model is not None
        assert len(self.model.tire_outlap_penalties) == 3
        assert self.model.fuel_effect_per_kg > 0
    
    def test_predict_with_valid_data(self):
        """Test outlap prediction with valid data."""
        result = self.model.predict("9158", "SOFT", 50.0)
        
        assert "prediction" in result
        assert "factors" in result
        prediction = result["prediction"]
        assert "predicted_lap_time" in prediction
        assert "confidence_interval" in prediction
        assert "tire_warm_up_laps" in prediction
    
    def test_predict_with_invalid_compound(self):
        """Test prediction with invalid tire compound."""
        result = self.model.predict("9158", "INVALID", 50.0)
        assert "error" in result
    
    def test_temperature_factor_calculation(self):
        """Test temperature factor calculation for outlaps."""
        from backend.models.outlap import TireCompound
        
        # Test with soft compound
        factor = self.model._calculate_temperature_factor(TireCompound.SOFT, 30.0)
        assert factor >= 1.0
        
        # Test with extreme temperatures
        cold_factor = self.model._calculate_temperature_factor(TireCompound.SOFT, 5.0)
        hot_factor = self.model._calculate_temperature_factor(TireCompound.SOFT, 60.0)
        assert cold_factor > 1.0
        assert hot_factor > 1.0
    
    def test_warm_up_laps_estimation(self):
        """Test tire warm-up laps estimation."""
        from backend.models.outlap import TireCompound
        
        soft_laps = self.model._estimate_warm_up_laps(TireCompound.SOFT, 25.0)
        medium_laps = self.model._estimate_warm_up_laps(TireCompound.MEDIUM, 25.0)
        hard_laps = self.model._estimate_warm_up_laps(TireCompound.HARD, 25.0)
        
        assert soft_laps <= medium_laps <= hard_laps
        assert all(laps >= 1 for laps in [soft_laps, medium_laps, hard_laps])
    
    def test_compare_compounds(self):
        """Test compound comparison functionality."""
        result = self.model.compare_compounds("9158", 50.0, baseline_lap_time=90.0)
        
        assert "compound_comparison" in result
        assert "ranking" in result
        assert "fastest_compound" in result
        assert len(result["ranking"]) == 3


# Fixtures for async testing
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


class TestAsyncComponents:
    """Test async components of the application."""
    
    @pytest.mark.asyncio
    async def test_app_startup(self):
        """Test that the app can start up properly."""
        # This would test any startup events if we had them
        assert True  # Placeholder
    
    @pytest.mark.asyncio 
    async def test_service_initialization(self):
        """Test that services can be initialized."""
        from backend.services.openf1 import OpenF1Service
        from backend.services.jolpica import JolpicaService
        
        openf1 = OpenF1Service()
        jolpica = JolpicaService()
        
        assert openf1 is not None
        assert jolpica is not None
        
        # Clean up
        await openf1.close()
        await jolpica.close()


if __name__ == "__main__":
    pytest.main([__file__])