"""
API Client Package
==================

Unified API client for all external service integrations.
"""

from .config import APIConfig, api_config
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

__all__ = [
    "APIConfig",
    "api_config",
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
    "setup_logging"
]