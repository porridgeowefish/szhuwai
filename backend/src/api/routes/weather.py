"""
天气查询路由
============

POST /api/v1/weather/query - 天气查询
"""

from typing import Optional

from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel, Field

from src.schemas.weather import WeatherSummary
from src.api.weather_client import WeatherClient

router = APIRouter(prefix="/weather", tags=["天气查询"])


class WeatherQueryRequest(BaseModel):
    """天气查询请求"""
    lon: float = Field(..., description="经度")
    lat: float = Field(..., description="纬度")
    trip_date: str = Field(..., description="出行日期 (YYYY-MM-DD)")


class WeatherQueryResponse(BaseModel):
    """天气查询响应"""
    success: bool = Field(True, description="请求是否成功")
    data: Optional[WeatherSummary] = Field(None, description="天气数据")
    message: Optional[str] = Field(None, description="附加消息")


@router.post("/query", response_model=WeatherQueryResponse)
async def query_weather(
    lon: float = Form(..., description="经度"),
    lat: float = Form(..., description="纬度"),
    trip_date: str = Form(..., description="出行日期 (YYYY-MM-DD)")
) -> WeatherQueryResponse:
    """
    查询指定位置的天气数据

    - **lon**: 经度
    - **lat**: 纬度
    - **trip_date**: 出行日期 (YYYY-MM-DD)
    """
    try:
        client = WeatherClient()

        # 获取3天格点天气预报
        grid_weather = client.get_grid_weather_3d(lon, lat)

        # 获取24小时逐小时天气
        hourly_weather = None
        try:
            hourly_weather = client.get_grid_weather_24h(lon, lat)
        except Exception:
            pass

        # 获取多抽样点天气（起点实时天气）
        grid_points = []
        try:
            now_weather = client.get_grid_weather_now(lon, lat)
            if now_weather and "now" in now_weather:
                now = now_weather["now"]
                grid_points.append({
                    "point_type": "查询点",
                    "temp": int(float(now.get("temp", 0))),
                    "wind_scale": now.get("windScale", "0"),
                    "humidity": int(float(now.get("humidity", 0)))
                })
        except Exception:
            pass

        # 转换为 WeatherSummary
        from src.schemas.weather import WeatherSummary, CityWeatherResponse, CityWeatherDaily

        city_daily = []
        for day in grid_weather.daily:
            city_daily.append(CityWeatherDaily(
                fxDate=day.fxDate,
                tempMax=day.tempMax,
                tempMin=day.tempMin,
                textDay=day.textDay,
                windScaleDay=day.windScaleDay,
                windSpeedDay=day.windSpeedDay,
                humidity=day.humidity,
                precip=day.precip,
                pressure=day.pressure
            ))

        city_weather = CityWeatherResponse(
            location=grid_weather.location,
            updateTime=grid_weather.updateTime,
            daily=city_daily
        )

        summary = WeatherSummary(
            trip_date=trip_date,
            forecast_days=3,
            use_grid=True,
            forecast_3d=city_weather
        )

        # 计算最高最低温度
        if grid_weather and grid_weather.daily:
            temps = []
            for day in grid_weather.daily:
                temps.extend([day.tempMax, day.tempMin])
            if temps:
                summary.max_temp = max(temps)
                summary.min_temp = min(temps)

        # 附加数据
        if hourly_weather:
            summary.hourly_24h = hourly_weather
        summary.grid_points = grid_points

        return WeatherQueryResponse(
            success=True,
            data=summary,
            message="天气查询成功"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"天气查询失败: {str(e)}"
        )
