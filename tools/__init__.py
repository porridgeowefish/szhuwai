"""
Tools Package
=============

This package contains all external API integration tools for the
Outdoor Agent Planner system.

Modules:
---------
- config: API configuration management
- utils: Utility functions and base API client
- weather_client: Weather API integration (QWeather)
- map_client: Map API integration (Amap/Gaode)
- search_client: Web search API integration (Tavily)
"""

# Configuration
from .config import APIConfig, api_config

# Utilities
from .utils import (
    BaseAPIClient,
    RateLimiter,
    APICache,
    APIError,
    RateLimitError,
    AuthenticationError,
    NetworkError,
    NotFoundError,
    TimeoutError,
    handle_api_errors,
    setup_logging
)

# API Clients
from .weather_client import WeatherClient
from .map_client import MapClient
from .search_client import SearchClient

__all__ = [
    # Configuration
    "APIConfig",
    "api_config",
    # Utilities
    "BaseAPIClient",
    "RateLimiter",
    "APICache",
    "APIError",
    "RateLimitError",
    "AuthenticationError",
    "NetworkError",
    "NotFoundError",
    "TimeoutError",
    "handle_api_errors",
    "setup_logging",
    # API Clients
    "WeatherClient",
    "MapClient",
    "SearchClient"
]
