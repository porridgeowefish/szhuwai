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
from .user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserInDB
)
from .sms import (
    SmsScene,
    SmsSendRequest,
    SmsSendResponse,
    SmsVerifyRequest
)
from .auth import (
    UsernameRegisterRequest,
    UsernameLoginRequest,
    PhoneRegisterRequest,
    PhoneLoginRequest,
    ResetPasswordRequest,
    BindPhoneRequest,
    ChangePasswordRequest,
    TokenResponse
)
from .quota import QuotaInfo, QuotaResponse

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
    "ScenicSpot",

    # User models
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserInDB",

    # SMS models
    "SmsScene",
    "SmsSendRequest",
    "SmsSendResponse",
    "SmsVerifyRequest",

    # Auth models
    "UsernameRegisterRequest",
    "UsernameLoginRequest",
    "PhoneRegisterRequest",
    "PhoneLoginRequest",
    "ResetPasswordRequest",
    "BindPhoneRequest",
    "ChangePasswordRequest",
    "TokenResponse",

    # Quota models
    "QuotaInfo",
    "QuotaResponse",
]