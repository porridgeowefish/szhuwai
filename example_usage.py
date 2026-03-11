"""
Usage Example
=============

Comprehensive example of how to use the Outdoor Agent Planner schemas and API clients.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict

# Import schemas
from schemas.base import Point3D
from schemas.track import TrackAnalysisResult, TerrainChange
from schemas.weather import (
    WeatherSummary, WeatherDaily, WeatherSummaryInfo,
    CityWeatherDaily, GridWeatherDaily, HourlyWeather,
    CityWeatherResponse, GridWeatherResponse, HourlyWeatherResponse
)
from schemas.transport import TransportRoutes, DrivingRoute, GeocodeResult, LocationInfo, RouteSummary
from schemas.search import SearchResult, WebSearchResponse
from schemas.output import (
    OutdoorActivityPlan, EquipmentItem, SafetyIssue,
    SafetyAssessment, EmergencyContact, ItineraryItem
)

# Import API clients
from api import WeatherClient, MapClient, SearchClient, APIConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_environment():
    """Setup environment and API clients"""
    # Load configuration from .env file
    config = APIConfig.from_env()

    # Initialize clients
    weather_client = WeatherClient(config)
    map_client = MapClient(config)
    search_client = SearchClient(config)

    return weather_client, map_client, search_client


def create_sample_track_analysis() -> TrackAnalysisResult:
    """Create sample track analysis data"""
    # Define key points
    start_point = Point3D(lat=39.9042, lon=116.4074, elevation=50)
    end_point = Point3D(lat=39.9042, lon=116.4074, elevation=50)  # Loop trail
    max_elev_point = Point3D(lat=39.9200, lon=116.4200, elevation=800)
    min_elev_point = Point3D(lat=39.8900, lon=116.3900, elevation=100)

    # Create terrain changes
    terrain_changes = [
        TerrainChange(
            change_type="大爬升",
            start_point=min_elev_point,
            end_point=max_elev_point,
            elevation_diff=700,
            distance_m=5000,
            gradient_percent=14.0
        ),
        TerrainChange(
            change_type="大下降",
            start_point=max_elev_point,
            end_point=min_elev_point,
            elevation_diff=650,
            distance_m=6000,
            gradient_percent=10.8
        )
    ]

    # Create track analysis
    track = TrackAnalysisResult(
        total_distance_km=11.0,
        total_ascent_m=750,
        total_descent_m=700,
        max_elevation_m=800,
        min_elevation_m=100,
        avg_elevation_m=450,
        start_point=start_point,
        end_point=end_point,
        max_elev_point=max_elev_point,
        min_elev_point=min_elev_point,
        terrain_analysis=terrain_changes,
        difficulty_score=65,
        difficulty_level="困难",
        estimated_duration_hours=4.5,
        safety_risk="中等风险",
        track_name="香山经典徒步环线",
        track_points_count=1200
    )

    return track


def create_sample_weather() -> WeatherSummary:
    """Create sample weather data"""
    # Create sample daily weather
    daily_weather = [
        WeatherDaily(
            fxDate=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            tempMax=22,
            tempMin=12,
            icon="100",
            textDay="晴",
            textNight="晴",
            windScaleDay="2",
            windScaleNight="1",
            humidity=45,
            precipitation=0,
            pop=0,
            uvIndex=5
        ),
        WeatherDaily(
            fxDate=(datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            tempMax=25,
            tempMin=15,
            icon="101",
            textDay="多云",
            textNight="多云",
            windScaleDay="3",
            windScaleNight="2",
            humidity=50,
            precipitation=0,
            pop=10,
            uvIndex=6
        )
    ]

    weather = WeatherSummary(
        trip_date=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        forecast_days=2,
        use_grid=False,
        current=None,  # CurrentWeather would need to be created
        forecast_3d=None,
        forecast_7d=None,
        points_weather=[],
        summary=WeatherSummaryInfo(
            conditions="良好",
            recommendation="适合户外活动"
        ),
        max_temp=25,
        min_temp=12
    )

    return weather


def create_sample_transport() -> TransportRoutes:
    """Create sample transport data"""
    # Get geocoding for locations
    from tools import MapClient, APIConfig
    from schemas.transport import LocationInfo, RouteSummary

    map_client = MapClient(APIConfig.from_env())

    try:
        # Geocode key locations
        origin = map_client.geocode("北京市区")
        destination = map_client.geocode("香山公园")

        # Get driving route
        driving_route = map_client.driving_route(
            f"{origin.lon},{origin.lat}",
            f"{destination.lon},{destination.lat}"
        )

        transport = TransportRoutes(
            origin=LocationInfo(
                address="北京市区",
                lat=origin.lat,
                lon=origin.lon
            ),
            destination=LocationInfo(
                address="香山公园",
                lat=destination.lat,
                lon=destination.lon
            ),
            outbound={
                "driving": driving_route.model_dump()
            },
            summary=RouteSummary(
                total_distance=f"{driving_route.distance_km:.1f}km",
                total_time=f"{driving_route.duration_min}分钟",
                cost=f"过路费{driving_route.tolls_yuan}元"
            ),
            recommended_mode="driving"
        )

        return transport

    except Exception as e:
        logger.error(f"Failed to create transport data: {e}")
        # Return mock data
        return TransportRoutes(
            origin=LocationInfo(address="北京市区"),
            destination=LocationInfo(address="香山公园"),
            outbound={"driving": {"available": True}},
            summary=RouteSummary(),
            recommended_mode="driving"
        )


def create_sample_search() -> List[WebSearchResponse]:
    """Create sample search results"""
    from tools import SearchClient, APIConfig

    search_client = SearchClient(APIConfig.from_env())

    # Search for hiking information
    responses = []

    # General hiking info
    try:
        response = search_client.search("北京 香山 徒步 路线 推荐", max_results=5)
        responses.append(response)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        # Create mock response
        response = WebSearchResponse(
            query="北京 香山 徒步",
            results=[],
            total_results=0,
            search_time=0,
            sources=[]
        )
        responses.append(response)

    return responses


def create_sample_safety_issues() -> List[SafetyIssue]:
    """Create sample safety issues"""
    issues = [
        SafetyIssue(
            type="地形风险",
            severity="中",
            description="部分路段坡度较陡，建议使用登山杖",
            mitigation="携带登山杖，注意休息",
            emergency_contact="拨打120"
        ),
        SafetyIssue(
            type="天气风险",
            severity="低",
            description="紫外线较强",
            mitigation="涂抹防晒霜，戴帽子",
            emergency_contact="无"
        )
    ]
    return issues


def create_sample_equipment() -> List[EquipmentItem]:
    """Create sample equipment recommendations"""
    equipment = [
        EquipmentItem(
            name="登山鞋",
            category="鞋类",
            priority="必需",
            quantity=1,
            weight_kg=0.8,
            description="防滑防水",
            alternatives=["运动鞋"]
        ),
        EquipmentItem(
            name="登山杖",
            category="导航工具",
            priority="推荐",
            quantity=2,
            weight_kg=0.3,
            description="减轻膝盖压力",
            alternatives=["木棍"]
        ),
        EquipmentItem(
            name="背包",
            category="背包",
            priority="必需",
            quantity=1,
            weight_kg=0.5,
            description="20-30L容量",
            alternatives=["双肩包"]
        ),
        EquipmentItem(
            name="水壶",
            category="其他",
            priority="必需",
            quantity=1,
            weight_kg=0.3,
            description="至少1L容量",
            alternatives=["矿泉水瓶"]
        ),
        EquipmentItem(
            name="头灯",
            category="电子产品",
            priority="推荐",
            quantity=1,
            weight_kg=0.2,
            description="备用照明",
            alternatives=["手机手电筒"]
        )
    ]
    return equipment


def create_comprehensive_plan() -> OutdoorActivityPlan:
    """Create a comprehensive outdoor activity plan"""
    # Get all sample data
    track = create_sample_track_analysis()
    weather = create_sample_weather()
    transport = create_sample_transport()
    search_results = create_sample_search()
    safety_issues = create_sample_safety_issues()
    equipment = create_sample_equipment()

    # Create plan
    plan = OutdoorActivityPlan(
        plan_id="hiking-2024-001",
        created_at=datetime.now(),
        user_request="周末去香山徒步一日游",
        plan_name="香山经典徒步路线",
        track_analysis=track,
        weather_info=weather,
        transport_info=transport,
        search_results=search_results,
        safety_assessment=SafetyAssessment(
            overall_risk="中等风险",
            conditions="良好",
            recommendation="谨慎推荐"
        ),
        safety_issues=safety_issues,
        equipment_recommendations=equipment,
        precautions=[
            "提前查看天气预报",
            "携带足够的水和食物",
            "告知家人行程计划",
            "不要单独前往危险区域",
            "携带手机保持电量充足"
        ],
        best_practices=[
            "遵循既定路线，不要擅自偏离",
            "结伴而行，互相照应",
            "尊重自然环境，不乱扔垃圾",
            "遇到紧急情况及时求助"
        ],
        scenic_spots=[
            {
                "name": "香山公园",
                "description": "北京著名赏枫胜地",
                "location": Point3D(lat=39.9934, lon=116.1885, elevation=575),
                "best_view_time": "上午10-11点",
                "difficulty": "简单",
                "estimated_visit_time_min": 60
            }
        ],
        overall_rating="推荐",
        confidence_score=0.85,
        risk_factors=["部分路段坡度较大", "天气变化"],
        emergency_contacts=[
            EmergencyContact(name="急救", phone="120", type="医疗"),
            EmergencyContact(name="旅游投诉", phone="12301", type="其他")
        ],
        itinerary=[
            ItineraryItem(time="08:00", activity="从市区出发", location="北京市区"),
            ItineraryItem(time="09:00", activity="到达香山公园", location="香山公园"),
            ItineraryItem(time="09:30", activity="开始徒步", location="香山步道"),
            ItineraryItem(time="12:00", activity="山顶休息", location="香炉峰"),
            ItineraryItem(time="15:00", activity="返回", location="香山公园")
        ]
    )

    return plan


def demonstrate_new_weather_api():
    """Demonstrate the new weather API functionality"""
    logger.info("\n=== New Weather API Demonstration ===")

    try:
        # Setup environment
        config = APIConfig.from_env()
        weather_client = WeatherClient(config)
        logger.info("Weather client initialized with new API format")

        # 1. Demonstrate city weather forecast (with UV and visibility)
        logger.info("1. Getting city weather forecast...")
        city_forecast = weather_client.get_weather_3d("Beijing")
        logger.info(f"City forecast for {city_forecast.location}")
        logger.info(f"Update time: {city_forecast.updateTime}")
        for day in city_forecast.daily[:2]:  # Show first 2 days
            logger.info(f"  {day.fxDate}: {day.textDay}, {day.tempMax}°C/{day.tempMin}°C, "
                       f"UV: {day.uvIndex}, Vis: {day.vis}km")

        # 2. Demonstrate grid weather forecast (for mountain points)
        logger.info("\n2. Getting grid weather forecast for mountain summit...")
        # Using Beijing coordinates as example
        summit_forecast = weather_client.get_grid_weather_3d(116.23, 39.54)
        logger.info(f"Grid forecast for {summit_forecast.location}")
        for day in summit_forecast.daily[:2]:
            logger.info(f"  {day.fxDate}: {day.textDay}, {day.tempMax}°C/{day.tempMin}°C")

        # 3. Demonstrate hourly weather
        logger.info("\n3. Getting hourly weather forecast...")
        hourly_forecast = weather_client.get_hourly_weather("Beijing", hours=12)
        logger.info(f"Hourly forecast for {hourly_forecast.location}")
        for hour in hourly_forecast.hourly[:6]:  # Show first 6 hours
            logger.info(f"  {hour.fxTime}: {hour.temp}°C, Pop: {hour.pop}%")

        # 4. Demonstrate location coordinate handling
        logger.info("\n4. Testing location coordinate handling...")
        location_params = weather_client.prepare_location_for_apis("Beijing")
        logger.info(f"Location parameters: {location_params}")

        # 5. Demonstrate cloud sea probability calculation
        logger.info("\n5. Calculating cloud sea probability...")
        if city_forecast.daily and summit_forecast.daily:
            cloud_sea = weather_client.calculate_cloud_sea_probability(
                city_forecast.daily[0],
                summit_forecast.daily[0]
            )
            logger.info(f"Cloud sea probability: {cloud_sea['probability']}%")
            logger.info(f"Assessment: {cloud_sea['assessment']}")

        # 6. Demonstrate safety check
        logger.info("\n6. Performing weather safety check...")
        safety = weather_client.check_weather_safety(
            city_forecast.daily,
            summit_forecast.daily
        )
        logger.info(f"Overall safety: {safety['risk_level']}")
        if safety['safety_issues']:
            logger.info("Safety issues:")
            for issue in safety['safety_issues']:
                logger.info(f"  - {issue}")

        # 7. Demonstrate comprehensive weather
        logger.info("\n7. Getting comprehensive weather data...")
        summit_coords = {"lon": 116.23, "lat": 39.54}
        comprehensive = weather_client.get_comprehensive_weather(
            "Beijing",
            summit_coords
        )
        logger.info("Comprehensive weather data retrieved")
        logger.info(f"City forecast: {len(comprehensive['city_forecast'].daily)} days")
        logger.info(f"Summit forecast: {len(comprehensive['summit_forecast'].daily)} days")
        logger.info(f"Hourly forecast: {len(comprehensive['hourly_forecast'].hourly)} hours")

        return comprehensive

    except Exception as e:
        logger.error(f"Error in weather API demonstration: {e}")
        return None


def main():
    """Main function demonstrating usage"""
    logger.info("=== Outdoor Agent Planner Usage Example ===")

    try:
        # Setup environment
        weather_client, map_client, search_client = setup_environment()
        logger.info("Environment setup complete")

        # Create sample data
        logger.info("Creating sample data...")
        track = create_sample_track_analysis()
        weather = create_sample_weather()
        transport = create_sample_transport()
        search_results = create_sample_search()

        logger.info("Sample data created successfully")

        # Create comprehensive plan
        logger.info("Creating comprehensive plan...")
        plan = create_comprehensive_plan()

        # Output results
        logger.info("\n=== Generated Plan ===")
        print(f"Plan ID: {plan.plan_id}")
        print(f"Plan Name: {plan.plan_name}")
        print(f"Overall Rating: {plan.overall_rating}")
        print(f"Confidence Score: {plan.confidence_score}")

        logger.info("\n=== Plan Details ===")
        print(f"Track Distance: {plan.track_analysis.total_distance_km} km")
        print(f"Difficulty: {plan.track_analysis.difficulty_level}")
        print(f"Estimated Duration: {plan.track_analysis.estimated_duration_hours} hours")
        print(f"Weather Conditions: {plan.weather_info.summary.conditions or 'Unknown'}")

        logger.info("\n=== Equipment List ===")
        for item in plan.required_equipment:
            print(f"- {item.name} ({item.priority}): {item.description}")

        logger.info("\n=== Safety Issues ===")
        for issue in plan.safety_issues:
            print(f"- {issue.type}: {issue.description}")

        # Save to JSON
        json_output = plan.to_json()
        with open("sample_plan.json", "w", encoding="utf-8") as f:
            f.write(json_output)

        logger.info("Sample plan saved to sample_plan.json")

        return plan

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    # Run the example
    plan = main()

    # Demonstrate new weather API
    demonstrate_new_weather_api()

    # Additional demonstrations
    logger.info("\n=== Additional Demonstrations ===")

    # 1. Weather safety check
    logger.info("1. Demonstrating weather safety check...")
    try:
        from schemas.weather import analyze_weather_safety
        if plan.weather_info.forecast_3d:
            safety = analyze_weather_safety(plan.weather_info.forecast_3d)
            logger.info(f"Weather safety: {safety}")
    except Exception as e:
        logger.error(f"Weather check failed: {e}")

    # 2. Track warnings
    logger.info("2. Demonstrating track warnings...")
    warnings = plan.track_analysis.get_segment_warnings()
    if warnings:
        logger.info("Track warnings:")
        for warning in warnings:
            logger.info(f"  - {warning}")

    # 3. Equipment weight calculation
    logger.info("3. Equipment weight calculation...")
    total_weight = plan.total_equipment_weight
    logger.info(f"Total equipment weight: {total_weight:.2f} kg")

    logger.info("\n=== Example Complete ===")