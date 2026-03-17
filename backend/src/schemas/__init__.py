"""
API Contracts and Schemas for Outdoor Agent Planner
================================================

This module defines all the data contracts and schemas for the Outdoor Agent Planner system.
All API communications and LLM outputs must use these strongly-typed Pydantic models.
"""

from .base import Point3D
from .track import TrackAnalysisResult, TerrainChange
from .weather import (
    WeatherGridPoint,
    WeatherDaily,
    WeatherGridResponse,
    WeatherCloudSeaAnalysis,
    WeatherSummary,
    # New models
    WeatherBaseDaily,
    CityWeatherDaily,
    GridWeatherDaily,
    HourlyWeather,
    CityWeatherResponse,
    GridWeatherResponse,
    HourlyWeatherResponse,
    CurrentWeather,
    WeatherSummaryInfo
)
from .transport import (
    RouteStep,
    TransitRoute,
    DrivingRoute,
    WalkingRoute,
    TransportRoutes,
    GeocodeResult,
    ReverseGeocodeResult
)
from .search import SearchResult, WebSearchResponse
from .output import (
    OutdoorActivityPlan,
    PlanningContext,
    SafetyAssessment,
    EmergencyRescueContact,
    ItineraryItem,
    EquipmentCategory,
    EquipmentItem,
    SafetyIssueType,
    SafetyIssue,
    GridPointWeather,
    ScenicSpot
)

__all__ = [
    # Base models
    "Point3D",

    # Track analysis
    "TrackAnalysisResult",
    "TerrainChange",

    # Weather models
    "WeatherGridPoint",
    "WeatherDaily",
    "WeatherGridResponse",
    "WeatherCloudSeaAnalysis",
    "WeatherSummary",
    # New weather models
    "WeatherBaseDaily",
    "CityWeatherDaily",
    "GridWeatherDaily",
    "HourlyWeather",
    "CityWeatherResponse",
    "GridWeatherResponse",
    "HourlyWeatherResponse",
    "CurrentWeather",
    "WeatherSummaryInfo",

    # Transport models
    "RouteStep",
    "TransitRoute",
    "DrivingRoute",
    "WalkingRoute",
    "TransportRoutes",
    "GeocodeResult",
    "ReverseGeocodeResult",

    # Search models
    "SearchResult",
    "WebSearchResponse",

    # Output models
    "OutdoorActivityPlan",
    "PlanningContext",
    "SafetyAssessment",
    "EmergencyRescueContact",
    "ItineraryItem",
    "EquipmentCategory",
    "EquipmentItem",
    "SafetyIssueType",
    "SafetyIssue",
    "GridPointWeather",
    "ScenicSpot"
]