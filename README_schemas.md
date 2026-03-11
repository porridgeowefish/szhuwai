# API Contracts & Schemas Documentation

## Overview

This document describes the API contracts and schemas for the Outdoor Agent Planner system. All API communications and LLM outputs use these strongly-typed Pydantic models to ensure data consistency and prevent hallucinations.

## Architecture

### 1. Data Contract Philosophy

The system follows a **data contract-driven** approach:
- All LLM communications use structured JSON
- External API responses are validated and parsed
- No raw text or unstructured data is passed between components

### 2. Directory Structure

```
schemas/
├── __init__.py          # Export all models
├── base.py             # Base models (Point3D)
├── track.py            # Track analysis schemas
├── weather.py          # Weather API schemas
├── transport.py        # Map/Transport schemas
├── search.py           # Web search schemas
├── output.py           # Final delivery schemas
└── test_schemas.py     # Unit tests

api/
├── __init__.py          # Export utilities
├── config.py           # API configuration
├── utils.py            # Base classes and utilities
├── weather_client.py   # Weather API client
├── map_client.py       # Map API client
└── search_client.py    # Search API client
```

## Models Reference

### Base Models

#### Point3D
Three-dimensional coordinate point for geographical data.

```python
from schemas.base import Point3D

point = Point3D(
    lat=39.9042,      # Latitude (-90 to 90)
    lon=116.4074,     # Longitude (-180 to 180)
    elevation=50,     # Elevation in meters (-500 to 9000)
    timestamp=None    # Optional datetime
)
```

### Track Analysis

#### TrackAnalysisResult
Comprehensive track analysis including difficulty assessment and safety evaluation.

```python
from schemas.track import TrackAnalysisResult

track = TrackAnalysisResult(
    total_distance_km=10.5,        # Total distance in km
    total_ascent_m=250,            # Total ascent in meters
    total_descent_m=50,            # Total descent in meters
    max_elevation_m=350,           # Maximum elevation
    min_elevation_m=100,           # Minimum elevation
    avg_elevation_m=200,           # Average elevation
    start_point=Point3D(...),      # Starting point
    end_point=Point3D(...),        # Ending point
    max_elev_point=Point3D(...),   # Highest point
    min_elev_point=Point3D(...),   # Lowest point
    difficulty_score=65,            # Score 0-100
    difficulty_level="困难",       # "简单", "中等", "困难", "极难"
    estimated_duration_hours=3.5,   # Estimated time in hours
    safety_risk="中等风险",         # Risk level
    track_points_count=1000         # Number of track points
)
```

#### TerrainChange
Analysis of significant elevation changes.

```python
from schemas.track import TerrainChange

terrain = TerrainChange(
    change_type="大爬升",           # "大爬升" or "大下降"
    start_point=Point3D(...),      # Start of segment
    end_point=Point3D(...),        # End of segment
    elevation_diff=200,            # Elevation change
    distance_m=1000,               # Horizontal distance
    gradient_percent=20.0          # Gradient percentage
)
```

### Weather Models

#### WeatherDaily
Daily weather forecast data.

```python
from schemas.weather import WeatherDaily

weather = WeatherDaily(
    fxDate="2024-03-15",           # Date in YYYY-MM-DD
    tempMax=25.5,                  # Max temperature
    tempMin=15.2,                  # Min temperature
    icon="100",                    # Weather icon code
    textDay="晴",                  # Day description
    textNight="晴",                # Night description
    windScaleDay="3",              # Day wind scale
    windScaleNight="2",            # Night wind scale
    humidity=65,                  # Humidity percentage
    precipitation=0,               # Precipitation in mm
    pop=10,                       # Precipitation probability
    uvIndex=6,                    # UV index
    cloudSea=None                 # Cloud sea analysis
)
```

#### WeatherSummary
Weather summary for trip planning.

```python
from schemas.weather import WeatherSummary

weather_summary = WeatherSummary(
    trip_date="2024-03-15",        # Trip date
    forecast_days=3,               # Number of forecast days
    use_grid=True,                # Use grid weather
    max_temp=25,                  # Max temperature
    min_temp=15,                  # Min temperature
    safe_for_outdoor=True         # Safety assessment
)
```

### Transport Models

#### GeocodeResult
Geocoding result (address to coordinates).

```python
from schemas.transport import GeocodeResult

geo = GeocodeResult(
    address="北京市朝阳区",
    province="北京市",
    city="北京市",
    district="朝阳区",
    adcode="110105",              # Administrative code
    lon=116.487,                  # Longitude
    lat=39.982                    # Latitude
)

# Convert to Point3D
point = geo.to_point3d(elevation=50)
```

#### DrivingRoute
Driving route information.

```python
from schemas.transport import DrivingRoute, RouteStep

route = DrivingRoute(
    available=True,
    duration_min=30,             # Duration in minutes
    distance_km=15.5,             # Distance in km
    tolls_yuan=10,               # Toll fee
    traffic_lights=5,            # Number of traffic lights
    steps=[                      # Route steps
        RouteStep(
            instruction="向右转",
            distance=50,         # Distance in meters
            duration=30,         # Duration in seconds
            action="turn"
        )
    ]
)
```

### Search Models

#### SearchResult
Individual search result.

```python
from schemas.search import SearchResult

result = SearchResult(
    title="香山徒步路线",
    url="https://example.com",
    content="香山是北京著名的...",
    score=0.85,                 # Relevance score
    source="hiking.com",
    source_type="web",
    published_date=datetime.now(),
    relevance_tags=["徒步", "香山"]
)
```

#### WebSearchResponse
Search response with multiple results.

```python
from schemas.search import WebSearchResponse

search_response = WebSearchResponse(
    query="北京 徒步 路线",
    results=[SearchResult(...)],  # List of results
    total_results=10,
    search_time=0.5,
    sources=["tavily"]
)
```

### Output Models

#### OutdoorActivityPlan
Final comprehensive activity plan.

```python
from schemas.output import OutdoorActivityPlan, EquipmentItem, SafetyIssue

plan = OutdoorActivityPlan(
    plan_id="trip-001",
    user_request="周末去香山徒步",
    plan_name="北京香山徒步计划",
    track_analysis=TrackAnalysisResult(...),
    weather_info=WeatherSummary(...),
    transport_info=TransportRoutes(...),
    safety_issues=[SafetyIssue(...)],
    equipment_recommendations=[EquipmentItem(...)],
    overall_rating="推荐",        # "推荐", "谨慎推荐", "不推荐"
    confidence_score=0.8,        # Confidence 0-1
    risk_factors=["天气变化"]
)
```

## API Clients

### WeatherClient
和风天气 API client.

```python
from api.weather_client import WeatherClient

client = WeatherClient()
forecast = client.get_weather_3d("Beijing")
safety_check = client.check_weather_safety("Beijing", "2024-03-15")
```

### MapClient
高德地图 API client.

```python
from api.map_client import MapClient

client = MapClient()
geo = client.geocode("北京市朝阳区")
route = client.driving_route("116.404,39.915", "116.196,39.917")
```

### SearchClient
Tavily search API client.

```python
from api.search_client import SearchClient

client = SearchClient()
results = client.search("北京 徒步 路线 推荐")
context_search = client.search_with_context("徒步", {"locations": ["北京"]})
```

## Configuration

### APIConfig
Centralized configuration management.

```python
from api.config import APIConfig, api_config

# Load from .env file
config = APIConfig.from_env()

# Check proxy settings
if config.should_use_proxy():
    print("Using proxy:", config.PROXY)
```

## Best Practices

1. **Always validate data** - Use Pydantic models for all inputs/outputs
2. **Handle API errors** - Use the provided error handling decorators
3. **Implement caching** - The APICache handles TTL-based caching
4. **Rate limiting** - The RateLimiter prevents API quota exhaustion
5. **Logging** - All API requests are logged for debugging

## Testing

Run schema tests:

```bash
python test_schemas.py
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Check `.env` file configuration
   - Verify API keys are valid and not expired

2. **Validation Errors**
   - Ensure all required fields are provided
   - Check data types and value ranges

3. **Rate Limiting**
   - The client automatically handles rate limits
   - Monitor logs for rate limit warnings

4. **Proxy Issues**
   - Verify proxy configuration in `.env`
   - Check proxy server connectivity