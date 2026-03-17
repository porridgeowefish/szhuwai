#!/usr/bin/env python3
"""
Test script for the new weather API implementation
"""

import os
import sys
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.config import APIConfig
from src.api.weather_client import WeatherClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_weather_api():
    """Test the new weather API implementation"""
    logger.info("=== Testing New Weather API Implementation ===")

    try:
        # Load configuration
        config = APIConfig.from_env()
        logger.info("Configuration loaded successfully")

        # Initialize weather client
        weather_client = WeatherClient(config)
        logger.info("Weather client initialized")

        # Test 1: City weather forecast
        logger.info("\n--- Test 1: City Weather Forecast ---")
        try:
            city_forecast = weather_client.get_weather_3d("Beijing")
            logger.info(f"✓ City forecast retrieved for {city_forecast.location}")
            logger.info(f"  Update time: {city_forecast.updateTime}")
            logger.info(f"  Forecast days: {len(city_forecast.daily)}")
            if city_forecast.daily:
                day = city_forecast.daily[0]
                logger.info(f"  Day 1: {day.fxDate}, {day.textDay}, {day.tempMax}°C/{day.tempMin}°C")
                logger.info(f"  UV Index: {day.uvIndex}, Visibility: {day.vis}km")
        except Exception as e:
            logger.error(f"✗ City weather test failed: {e}")

        # Test 2: Grid weather forecast
        logger.info("\n--- Test 2: Grid Weather Forecast ---")
        try:
            grid_forecast = weather_client.get_grid_weather_3d(116.23, 39.54)
            logger.info(f"✓ Grid forecast retrieved for {grid_forecast.location}")
            logger.info(f"  Forecast days: {len(grid_forecast.daily)}")
            if grid_forecast.daily:
                day = grid_forecast.daily[0]
                logger.info(f"  Day 1: {day.fxDate}, {day.textDay}, {day.tempMax}°C/{day.tempMin}°C")
        except Exception as e:
            logger.error(f"✗ Grid weather test failed: {e}")

        # Test 3: Hourly weather
        logger.info("\n--- Test 3: Hourly Weather Forecast ---")
        try:
            hourly_forecast = weather_client.get_hourly_weather("Beijing", hours=12)
            logger.info(f"✓ Hourly forecast retrieved for {hourly_forecast.location}")
            logger.info(f"  Hourly data points: {len(hourly_forecast.hourly)}")
            if hourly_forecast.hourly:
                hour = hourly_forecast.hourly[0]
                logger.info(f"  First hour: {hour.fxTime}, {hour.temp}°C, Pop: {hour.pop}%")
        except Exception as e:
            logger.error(f"✗ Hourly weather test failed: {e}")

        # Test 4: Location coordinate handling
        logger.info("\n--- Test 4: Location Coordinate Handling ---")
        try:
            location_params = weather_client.prepare_location_for_apis("Beijing")
            logger.info(f"✓ Location parameters prepared")
            logger.info(f"  City API: {location_params['city_api']}")
            logger.info(f"  Grid API: {location_params['grid_api']}")
            logger.info(f"  Coordinates: {location_params['coords']}")
        except Exception as e:
            logger.error(f"✗ Location handling test failed: {e}")

        # Test 5: Cloud sea probability calculation
        logger.info("\n--- Test 5: Cloud Sea Probability ---")
        try:
            if 'city_forecast' in locals() and 'grid_forecast' in locals():
                if city_forecast.daily and grid_forecast.daily:
                    cloud_sea = weather_client.calculate_cloud_sea_probability(
                        city_forecast.daily[0],
                        grid_forecast.daily[0]
                    )
                    logger.info(f"✓ Cloud sea probability calculated")
                    logger.info(f"  Probability: {cloud_sea['probability']}%")
                    logger.info(f"  Assessment: {cloud_sea['assessment']}")
        except Exception as e:
            logger.error(f"✗ Cloud sea test failed: {e}")

        # Test 6: Safety check
        logger.info("\n--- Test 6: Weather Safety Check ---")
        try:
            if 'city_forecast' in locals() and 'grid_forecast' in locals():
                safety = weather_client.check_weather_safety(
                    city_forecast.daily,
                    grid_forecast.daily
                )
                logger.info(f"✓ Safety check completed")
                logger.info(f"  Risk level: {safety['risk_level']}")
                if safety['safety_issues']:
                    logger.info(f"  Issues: {len(safety['safety_issues'])}")
                    for issue in safety['safety_issues'][:2]:  # Show first 2
                        logger.info(f"    - {issue['type']}: {issue['risk']}")
        except Exception as e:
            logger.error(f"✗ Safety check test failed: {e}")

        logger.info("\n=== API Test Complete ===")

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        raise


if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists(".env"):
        logger.warning(".env file not found. Please create it from .env.example")
        sys.exit(1)

    # Run tests
    test_weather_api()