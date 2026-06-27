"""极速策划生成服务测试。"""

from datetime import datetime

from src.schemas.base import Point3D
from src.schemas.track import TrackAnalysisResult
from src.schemas.weather import HourlyWeather, HourlyWeatherResponse, WeatherSummary
from src.services.fast_plan_service import FastPlanService


def test_fast_plan_generates_conservative_plan_without_external_data() -> None:
    track = TrackAnalysisResult(
        track_name="社团拉练线",
        total_distance_km=16,
        total_ascent_m=900,
        total_descent_m=850,
        max_elevation_m=1200,
        min_elevation_m=300,
        avg_elevation_m=700,
        start_point=Point3D(lon=116.4, lat=39.9, elevation=300),
        end_point=Point3D(lon=116.5, lat=40.0, elevation=300),
        max_elev_point=Point3D(lon=116.45, lat=39.95, elevation=1200),
        min_elev_point=Point3D(lon=116.42, lat=39.92, elevation=300),
        terrain_analysis=[],
        difficulty_score=65,
        difficulty_level="困难",
        estimated_duration_hours=7.5,
        safety_risk="中等风险",
        track_points_count=100,
        track_created_at=datetime.now(),
    )

    plan = FastPlanService().generate(
        track=track,
        trip_date="2026-07-01",
        weather=None,
        transport=None,
        rescue_points=[],
        plan_title="",
        warnings=["未配置天气 API Key，已跳过真实天气查询。"],
    )

    assert plan.plan_name == "社团拉练线"
    assert plan.overall_rating in {"谨慎推荐", "不推荐"}
    assert plan.track_detail is not None
    assert plan.track_detail.total_distance_km == 16
    assert plan.safety_issues
    assert any(issue.type == "天气风险" for issue in plan.safety_issues)
    assert {contact.phone for contact in plan.emergency_rescue_contacts} >= {"110", "120", "119"}


def test_hourly_weather_uses_trip_daytime_window() -> None:
    weather = WeatherSummary(
        trip_date="2026-06-28",
        forecast_days=3,
        use_grid=True,
        hourly_24h=HourlyWeatherResponse(
            location="test",
            updateTime="2026-06-28 02:00:00",
            hourly=[
                HourlyWeather(fxTime="2026-06-28T04:00+08:00", temp=30, pop=0, precip=0, windScale="1"),
                HourlyWeather(fxTime="2026-06-28T06:00+08:00", temp=27, pop=0, precip=0, windScale="1"),
                HourlyWeather(fxTime="2026-06-28T12:00+08:00", temp=29, pop=0, precip=0, windScale="1"),
                HourlyWeather(fxTime="2026-06-28T21:00+08:00", temp=28, pop=0, precip=0, windScale="1"),
            ],
        ),
    )

    selected = FastPlanService()._select_daytime_hourly_weather("2026-06-28", weather)

    assert [item.fxTime for item in selected] == [
        "2026-06-28T06:00+08:00",
        "2026-06-28T12:00+08:00",
    ]


def test_hourly_weather_hides_trip_day_night_only_window() -> None:
    weather = WeatherSummary(
        trip_date="2026-06-28",
        forecast_days=3,
        use_grid=True,
        hourly_24h=HourlyWeatherResponse(
            location="test",
            updateTime="2026-06-28 00:00:00",
            hourly=[
                HourlyWeather(fxTime="2026-06-28T01:00+08:00", temp=29, pop=0, precip=0, windScale="1"),
                HourlyWeather(fxTime="2026-06-28T04:00+08:00", temp=30, pop=0, precip=0, windScale="1"),
            ],
        ),
    )

    selected = FastPlanService()._select_daytime_hourly_weather("2026-06-28", weather)

    assert selected == []
