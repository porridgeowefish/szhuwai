"""
天气服务
========

封装天气数据获取逻辑。
"""

from typing import List, Optional

from loguru import logger

from src.schemas.weather import WeatherSummary
from src.api.weather_client import WeatherClient
from src.services.weather_analyzer import WeatherAnalyzer


class WeatherService:
    """天气数据服务"""

    def __init__(self):
        """初始化服务"""
        self.client = WeatherClient()
        self.analyzer = WeatherAnalyzer()

    def get_summary(
        self,
        lon: float,
        lat: float,
        trip_date: str,
        include_hourly: bool = True,
        include_multi_point: bool = True,
        additional_points: Optional[List[tuple]] = None
    ) -> WeatherSummary:
        """
        获取天气汇总数据

        Args:
            lon: 经度
            lat: 纬度
            trip_date: 出行日期
            include_hourly: 是否包含24小时逐小时天气
            include_multi_point: 是否包含多抽样点天气
            additional_points: 额外抽样点列表 [(lon, lat, point_name), ...]

        Returns:
            WeatherSummary: 天气汇总数据
        """
        try:
            logger.info(f"获取格点天气: lon={lon}, lat={lat}, 日期={trip_date}")

            # 获取3天格点天气预报
            grid_weather = self.client.get_grid_weather_3d(lon, lat)

            # 获取24小时逐小时天气
            hourly_weather = None
            if include_hourly:
                try:
                    hourly_weather = self.client.get_grid_weather_24h(lon, lat)
                    logger.info(f"获取到24小时逐小时天气数据，共{len(hourly_weather.hourly)}小时")
                except Exception as e:
                    logger.warning(f"获取24小时逐小时天气失败: {e}")

            # 获取多抽样点天气
            grid_points = []
            if include_multi_point:
                grid_points = self._fetch_multi_point_weather(lon, lat, additional_points)
                logger.info(f"获取到{len(grid_points)}个抽样点的天气数据")

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

            return summary

        except Exception as e:
            logger.error(f"获取天气数据失败: {e}")
            raise

    def _fetch_multi_point_weather(
        self,
        start_lon: float,
        start_lat: float,
        additional_points: Optional[List[tuple]] = None
    ) -> List[dict]:
        """获取多抽样点天气数据"""
        grid_points = []

        # 起点
        try:
            start_now = self.client.get_grid_weather_now(start_lon, start_lat)
            if start_now and "now" in start_now:
                now = start_now["now"]
                grid_points.append({
                    "point_type": "起点",
                    "temp": int(float(now.get("temp", 0))),
                    "wind_scale": now.get("windScale", "0"),
                    "humidity": int(float(now.get("humidity", 0)))
                })
        except Exception as e:
            logger.warning(f"获取起点实时天气失败: {e}")

        # 额外抽样点
        if additional_points:
            for lon, lat, point_name in additional_points:
                try:
                    point_now = self.client.get_grid_weather_now(lon, lat)
                    if point_now and "now" in point_now:
                        now = point_now["now"]
                        grid_points.append({
                            "point_type": point_name,
                            "temp": int(float(now.get("temp", 0))),
                            "wind_scale": now.get("windScale", "0"),
                            "humidity": int(float(now.get("humidity", 0)))
                        })
                except Exception as e:
                    logger.warning(f"获取{point_name}实时天气失败: {e}")

        return grid_points
