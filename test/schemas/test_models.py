"""
Schema Tests
=============

Tests for all Pydantic schemas to ensure data validation.
"""

import pytest
from datetime import datetime, timedelta
from schemas.base import Point3D
from schemas.track import TrackAnalysisResult, TerrainChange
from schemas.weather import CityWeatherDaily, WeatherSummary
from schemas.transport import RouteStep, DrivingRoute, GeocodeResult
from schemas.search import SearchResult, WebSearchResponse
from schemas.output import OutdoorActivityPlan, EquipmentItem, SafetyIssue


class TestPoint3D:
    """测试Point3D模型"""

    def test_valid_point(self):
        """测试有效坐标点"""
        point = Point3D(
            lat=39.9042,
            lon=116.4074,
            elevation=50
        )
        assert point.lat == 39.9042
        assert point.lon == 116.4074
        assert point.elevation == 50
        assert point.timestamp is None

    def test_invalid_lat(self):
        """测试无效纬度"""
        with pytest.raises(ValueError):
            Point3D(lat=91, lon=116, elevation=50)

    def test_invalid_lon(self):
        """测试无效经度"""
        with pytest.raises(ValueError):
            Point3D(lat=39.9, lon=181, elevation=50)

    def test_invalid_elevation(self):
        """测试无效海拔"""
        with pytest.raises(ValueError):
            Point3D(lat=39.9, lon=116, elevation=10000)


class TestTerrainChange:
    """测试TerrainChange模型"""

    def test_terrain_change(self):
        """测试地形变化"""
        start = Point3D(lat=39.9, lon=116.4, elevation=100)
        end = Point3D(lat=39.91, lon=116.41, elevation=300)

        terrain = TerrainChange(
            change_type="大爬升",
            start_point=start,
            end_point=end,
            elevation_diff=200,
            distance_m=1000
        )

        assert terrain.elevation_diff == 200
        assert terrain.distance_m == 1000
        assert terrain.gradient_percent == 20.0  # (200/1000)*100


class TestTrackAnalysis:
    """测试轨迹分析模型"""

    def test_track_analysis(self):
        """测试轨迹分析结果"""
        start = Point3D(lat=39.9, lon=116.4, elevation=100)
        end = Point3D(lat=39.91, lon=116.41, elevation=300)
        max_elev = Point3D(lat=39.905, lon=116.405, elevation=350)
        min_elev = start

        track = TrackAnalysisResult(
            total_distance_km=10.5,
            total_ascent_m=250,
            total_descent_m=50,
            max_elevation_m=350,
            min_elevation_m=100,
            avg_elevation_m=200,
            start_point=start,
            end_point=end,
            max_elev_point=max_elev,
            min_elev_point=min_elev,
            difficulty_score=65,
            difficulty_level="困难",
            estimated_duration_hours=3.5,
            safety_risk="中等风险",
            track_points_count=1000
        )

        assert track.total_distance_km == 10.5
        assert track.elevation_range == 250
        assert track.difficulty_level == "困难"
        assert track.safety_risk == "中等风险"


class TestWeatherDaily:
    """测试天气模型"""

    def test_weather_daily(self):
        """测试每日天气"""
        weather = CityWeatherDaily(
            fxDate="2024-03-15",
            tempMax=26,  # 使用整数而不是浮点数
            tempMin=15,
            textDay="晴",
            windScaleDay="3",
            windSpeedDay=10,
            humidity=65,
            precip=0.0,
            pressure=1013,
            uvIndex=6,
            vis=20
        )

        assert weather.fxDate == "2024-03-15"
        assert weather.tempMax == 26
        assert weather.tempMin == 15
        assert weather.windSpeedDay == 10


class TestTransport:
    """测试交通模型"""

    def test_route_step(self):
        """测试路线步骤"""
        step = RouteStep(
            instruction="向右转",
            distance=50,
            duration=30,
            action="turn"
        )

        assert step.distance == 50
        assert step.duration_minutes == 0.5

    def test_driving_route(self):
        """测试驾车路线"""
        steps = [
            RouteStep(
                instruction="出发",
                distance=100,
                duration=60,
                action="start"
            )
        ]

        route = DrivingRoute(
            available=True,
            duration_min=30,
            distance_km=15.5,
            tolls_yuan=10,
            traffic_lights=5,
            steps=steps
        )

        assert route.available
        assert route.cost_per_km == 10 / 15.5
        assert route.duration_min == 30


class TestGeocode:
    """测试地理编码模型"""

    def test_geocode_result(self):
        """测试地理编码结果"""
        geo = GeocodeResult(
            address="北京市朝阳区",
            province="北京市",
            city="北京市",
            district="朝阳区",
            adcode="110105",
            lon=116.487,
            lat=39.982
        )

        assert geo.adcode == "110105"
        assert geo.lon == 116.487
        assert geo.lat == 39.982

        # 测试转换为3D点
        point3d = geo.to_point3d(elevation=50)
        assert point3d.lat == geo.lat
        assert point3d.lon == geo.lon
        assert point3d.elevation == 50


class TestSearch:
    """测试搜索模型"""

    def test_search_result(self):
        """测试搜索结果"""
        result = SearchResult(
            title="测试标题",
            url="https://example.com",
            content="这是一个测试内容摘要",
            score=0.85,
            source="test.com",
            relevance_tags=["户外", "徒步"]
        )

        assert result.title == "测试标题"
        assert result.is_trusted_source == False
        assert result.content_preview == "这是一个测试内容摘要"

    def test_web_search_response(self):
        """测试搜索响应"""
        results = [
            SearchResult(
                title="结果1",
                url="https://test1.com",
                content="内容1",
                score=0.9,
                source="test1.com"
            ),
            SearchResult(
                title="结果2",
                url="https://test2.com",
                content="内容2",
                score=0.8,
                source="test2.com"
            )
        ]

        response = WebSearchResponse(
            query="测试查询",
            results=results,
            total_results=2,
            search_time=0.5,
            sources=["tavily"]
        )

        assert response.query == "测试查询"
        assert abs(response.avg_score - 0.85) < 0.0001  # 浮点数精度比较
        assert response.trusted_results_count == 0


class TestOutput:
    """测试输出模型"""

    def test_safety_issue(self):
        """测试安全问题"""
        issue = SafetyIssue(
            type="天气风险",
            severity="高",
            description="可能有雷暴",
            mitigation="避免在山顶逗留"
        )

        assert issue.type == "天气风险"
        assert issue.severity == "高"
        assert issue.mitigation == "避免在山顶逗留"

    def test_equipment_item(self):
        """测试装备项"""
        item = EquipmentItem(
            name="登山杖",
            category="导航工具",
            priority="推荐",
            quantity=1,
            weight_kg=0.3,
            description="减轻膝盖压力"
        )

        assert item.name == "登山杖"
        assert item.category.value == "导航工具"
        assert item.priority == "推荐"
        assert item.weight_kg == 0.3

    def test_outdoor_activity_plan(self):
        """测试户外活动计划"""
        from schemas.track import TrackAnalysisResult
        from schemas.weather import WeatherSummary, CityWeatherDaily, HourlyWeather
        from schemas.transport import TransportRoutes, LocationInfo, RouteSummary
        from datetime import datetime

        # 创建简单的轨迹分析
        start = Point3D(lat=39.9, lon=116.4, elevation=100)
        track = TrackAnalysisResult(
            total_distance_km=5,
            total_ascent_m=200,
            total_descent_m=100,
            max_elevation_m=300,
            min_elevation_m=100,
            avg_elevation_m=200,
            start_point=start,
            end_point=start,
            max_elev_point=start,
            min_elev_point=start,
            difficulty_score=40,
            difficulty_level="中等",
            estimated_duration_hours=2,
            safety_risk="低风险",
            track_points_count=500
        )

        # 创建天气摘要
        weather = WeatherSummary(
            trip_date="2024-03-15",
            forecast_days=3,
            use_grid=True,
            max_temp=25,
            min_temp=15,
            safe_for_outdoor=True
        )

        # 创建交通路线
        transport = TransportRoutes(
            origin=LocationInfo(address="北京"),
            destination=LocationInfo(address="香山"),
            outbound={"driving": {"available": True, "duration_min": 30}},
            summary=RouteSummary()
        )

        # 创建当天详细天气
        daily_weather = CityWeatherDaily(
            fxDate="2024-03-15",
            tempMax=25,
            tempMin=15,
            textDay="晴",
            windScaleDay="3",
            windSpeedDay=10,
            humidity=65,
            precip=0.0,
            pressure=1013,
            uvIndex=6,
            vis=20
        )

        # 创建计划
        plan = OutdoorActivityPlan(
            plan_id="test-001",
            plan_name="北京香山徒步",
            overall_rating="推荐",
            track_overview="5km/爬升200m/中等",
            weather_overview="晴天，最高25度，无降水风险",
            transport_overview="建议驾车，约30分钟",
            trip_date_weather=daily_weather,
            itinerary=[],
            equipment_recommendations=[],
            scenic_spots=[],
            precautions=[],
            safety_assessment={},
            safety_issues=[],
            risk_factors=[],
            emergency_rescue_contacts=[]
        )

        assert plan.plan_id == "test-001"
        assert plan.plan_name == "北京香山徒步"
        assert plan.overall_rating == "推荐"
        assert plan.track_overview == "5km/爬升200m/中等"
        assert plan.weather_overview == "晴天，最高25度，无降水风险"
        assert plan.transport_overview == "建议驾车，约30分钟"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])