#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all module imports"""
    print("=== Testing Imports ===")

    try:
        # Test config import
        from api.config import APIConfig
        print("[OK] api.config imported")

        # Test weather client import
        from api.weather_client import WeatherClient
        print("[OK] api.weather_client imported")

        # Test weather schemas import
        from schemas.weather import (
            WeatherBaseDaily,
            CityWeatherDaily,
            GridWeatherDaily,
            HourlyWeather,
            CityWeatherResponse,
            GridWeatherResponse,
            HourlyWeatherResponse
        )
        print("[OK] schemas.weather imported")

        # Test base schemas import
        from schemas.base import Point3D
        print("[OK] schemas.base imported")

        # Test utils import
        from api.utils import BaseAPIClient, APIError
        print("[OK] api.utils imported")

        print("\n=== All Imports Successful ===")
        return True

    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)