# Quick Start Guide: Outdoor Agent Planner Schemas

## Getting Started in 5 Minutes

### 1. Install Dependencies

```bash
cd 03_Code
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the environment template and add your keys:

```bash
cp .env.example .env
```

Edit `.env` file:
```env
QWEATHER_API_KEY=your_qweather_key
AMAP_API_KEY=your_amap_key
LLM_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
```

### 3. Basic Usage

#### Create a Location Point

```python
from schemas.base import Point3D

# Beijing coordinates
point = Point3D(
    lat=39.9042,
    lon=116.4074,
    elevation=50
)
print(point)  # Point3D(lat=39.9042, lon=116.4074, elev=50m)
```

#### Analyze a Track

```python
from schemas.track import TrackAnalysisResult, Point3D

track = TrackAnalysisResult(
    total_distance_km=10.5,
    total_ascent_m=250,
    total_descent_m=50,
    max_elevation_m=350,
    min_elevation_m=100,
    avg_elevation_m=200,
    start_point=Point3D(lat=39.9, lon=116.4, elev=100),
    end_point=Point3D(lat=39.91, lon=116.41, elev=300),
    max_elev_point=Point3D(lat=39.905, lon=116.405, elev=350),
    min_elev_point=Point3D(lat=39.895, lon=116.395, elev=100),
    difficulty_score=65,
    difficulty_level="困难",
    estimated_duration_hours=3.5,
    safety_risk="中等风险",
    track_points_count=1000
)

print(f"难度等级: {track.difficulty_level}")
print(f"预计用时: {track.estimated_duration_hours} 小时")
```

#### Get Weather Information

```python
from api.weather_client import WeatherClient
from schemas.weather import WeatherSummary

# Initialize client
weather_client = WeatherClient()

# Get 3-day forecast
forecast = weather_client.get_weather_3d("Beijing")
print(f"预报天数: {len(forecast.daily)}")

# Check weather safety
safety = weather_client.check_weather_safety("Beijing", "2024-03-15")
print(f"是否安全: {safety['is_safe']}")
```

#### Plan Transportation

```python
from api.map_client import MapClient

map_client = MapClient()

# Geocode address
location = map_client.geocode("北京市朝阳区")
print(f"坐标: {location.lat}, {location.lon}")

# Get driving route
route = map_client.driving_route(
    "116.404,39.915",
    "116.196,39.917"
)
print(f"距离: {route.distance_km} km")
print(f"时间: {route.duration_min} 分钟")
```

#### Search for Information

```python
from api.search_client import SearchClient

search_client = SearchClient()

# Search hiking info
results = search_client.search("北京 徒步 路线 推荐", max_results=5)
print(f"找到 {results.total_results} 条结果")

# Context-aware search
context = {"locations": ["北京"], "activities": ["徒步"]}
results = search_client.search_with_context("最佳路线", context)
```

#### Generate Complete Plan

```python
from schemas.output import OutdoorActivityPlan, EquipmentItem

# Create equipment recommendations
equipment = [
    EquipmentItem(
        name="登山鞋",
        category=" footwear",
        priority="必需",
        quantity=1,
        weight_kg=0.8
    ),
    EquipmentItem(
        name="水壶",
        category=" misc",
        priority="必需",
        quantity=1,
        weight_kg=0.3
    )
]

# Create final plan
plan = OutdoorActivityPlan(
    plan_id="hiking-001",
    user_request="周末去香山徒步",
    plan_name="香山徒步计划",
    track_analysis=track,  # from earlier example
    weather_info=weather_summary,
    transport_info=transport_routes,
    overall_rating="推荐",
    confidence_score=0.85,
    equipment_recommendations=equipment
)

# Export to JSON
json_plan = plan.to_json()
with open("plan.json", "w", encoding="utf-8") as f:
    f.write(json_plan)
```

### 4. Run Examples

```bash
# Run comprehensive example
python example_usage.py

# Run schema tests
python test_schemas.py
```

### 5. Key Classes

| Class | Purpose | Key Methods |
|-------|---------|-------------|
| `Point3D` | 3D coordinate point | `__str__`, `__hash__` |
| `TrackAnalysisResult` | Track analysis | `get_segment_warnings()` |
| `WeatherSummary` | Weather forecast | `safe_for_outdoor`, `has_warning` |
| `TransportRoutes` | Multi-modal transport | `recommended_mode`, `fastest_mode` |
| `OutdoorActivityPlan` | Final plan | `is_safe_plan`, `total_equipment_weight` |

### 6. Common Patterns

#### Error Handling
```python
from api.utils import APIError

try:
    weather = weather_client.get_weather_3d("Beijing")
except APIError as e:
    print(f"API Error: {e.message}")
    # Handle error gracefully
```

#### Caching
```python
# API responses are automatically cached
# Cache key is generated from endpoint and parameters
# TTL is set in configuration (default: 1 hour)
```

#### Rate Limiting
```python
# Rate limiting is automatic
# No need to implement manually
# Rate is configurable in APIConfig
```

### 7. Troubleshooting

#### Common Issues

1. **API Key Not Found**
   ```bash
   # Check .env file
   cat .env
   ```

2. **Import Errors**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Validation Errors**
   - Check all required fields
   - Verify data types
   - Use `model_validate()` for manual validation

4. **Network Issues**
   - Check proxy settings in `.env`
   - Verify internet connection
   - Check API service status

#### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific client
weather_client.logger.setLevel(logging.DEBUG)
```

### 8. Next Steps

1. Read `README_schemas.md` for full documentation
2. Explore `IMPLEMENTATION_SUMMARY.md` for architecture details
3. Integrate schemas into your existing agents
4. Add custom validation rules as needed
5. Implement monitoring for API usage

### Need Help?

- Check the examples in `example_usage.py`
- Run the test suite with `python test_schemas.py -v`
- Review the full documentation in `README_schemas.md`