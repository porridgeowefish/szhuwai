"""
Pytest Configuration and Fixtures
=================================

This module provides pytest configuration and shared fixtures for all tests.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_path():
    """Return the project root directory path."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_path):
    """Return the test data directory path."""
    data_path = project_path / "test_data"
    data_path.mkdir(exist_ok=True)
    return data_path


@pytest.fixture
def sample_point():
    """Return a sample Point3D object for testing."""
    from schemas.base import Point3D
    return Point3D(lat=39.9042, lon=116.4074, elevation=50)


@pytest.fixture
def sample_track_data(sample_point):
    """Return sample track analysis data."""
    from schemas.track import TrackAnalysisResult
    return TrackAnalysisResult(
        total_distance_km=10.5,
        total_ascent_m=250,
        total_descent_m=50,
        max_elevation_m=350,
        min_elevation_m=100,
        avg_elevation_m=200,
        start_point=sample_point,
        end_point=Point3D(lat=39.91, lon=116.41, elevation=300),
        max_elev_point=Point3D(lat=39.905, lon=116.405, elevation=350),
        min_elev_point=sample_point,
        difficulty_score=65,
        difficulty_level="困难",
        estimated_duration_hours=3.5,
        safety_risk="中等风险",
        track_points_count=1000
    )


@pytest.fixture
def sample_weather_data():
    """Return sample weather data."""
    from schemas.weather import WeatherDaily
    return WeatherDaily(
        fxDate="2024-03-15",
        tempMax=25.5,
        tempMin=15.2,
        textDay="晴",
        textNight="晴",
        windScaleDay="3",
        windScaleNight="2",
        humidity=65,
        precipitation=0,
        pop=10,
        uvIndex=6,
        visibility=20
    )


@pytest.fixture
def mock_api_response():
    """Return a mock API response for testing."""
    return {
        "code": "200",
        "status": "1",
        "updateTime": "2024-03-10 12:00:00"
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests that require API keys"
    )
