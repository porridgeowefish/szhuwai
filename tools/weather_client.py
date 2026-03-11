"""
Weather API Client
==================

Client for integrating with 和风天气 (QWeather) API.
"""

from typing import Dict, Optional, List
from datetime import datetime

from . import BaseAPIClient, handle_api_errors, APIError
from .config import api_config
from schemas.weather import (
    WeatherGridPoint,
    WeatherDaily,
    WeatherGridResponse,
    WeatherCloudSeaAnalysis,
    WeatherSummary
)


class WeatherClient(BaseAPIClient):
    """和风天气API客户端"""

    def __init__(self, config=None):
        super().__init__(config or api_config)
        self.base_url = self.config.WEATHER_BASE_URL
        self.location_cache = {}

    def validate_response(self, response: Dict) -> bool:
        """验证API响应格式"""
        if "code" not in response:
            return False
        return response["code"] == "200"

    def parse_error(self, response: Dict) -> str:
        """解析错误信息"""
        error_codes = {
            "200": "OK",
            "204": "No Content",
            "400": "Bad Request",
            "401": "Unauthorized",
            "402": "Payment Required",
            "403": "Forbidden",
            "404": "Not Found",
            "429": "Too Many Requests",
            "500": "Internal Server Error",
            "502": "Bad Gateway",
            "503": "Service Unavailable"
        }

        code = response.get("code", "Unknown")
        return error_codes.get(code, f"Unknown error: {code}")

    @handle_api_errors
    def get_weather_now(self, location: str, lang: str = "zh") -> Dict:
        """获取实时天气"""
        endpoint = "weather/now"
        params = {
            "location": location,
            "key": self.config.WEATHER_API_KEY,
            "lang": lang
        }
        return self._make_request("GET", endpoint, params=params)

    @handle_api_errors
    def get_weather_3d(self, location: str, lang: str = "zh") -> WeatherGridResponse:
        """获取3天天气预报"""
        endpoint = "weather/3d"
        params = {
            "location": location,
            "key": self.config.WEATHER_API_KEY,
            "lang": lang
        }

        response = self._make_request("GET", endpoint, params=params)

        # 转换为模型
        daily_data = []
        for day_data in response.get("daily", []):
            daily = WeatherDaily(
                fxDate=day_data["fxDate"],
                tempMax=day_data["tempMax"],
                tempMin=day_data["tempMin"],
                icon=day_data["icon"],
                textDay=day_data["textDay"],
                textNight=day_data["textNight"],
                windScaleDay=day_data["windScaleDay"],
                windScaleNight=day_data["windScaleNight"],
                humidity=day_data["humidity"],
                precipitation=day_data["precip"],
                pop=day_data.get("pop", 0),
                uvIndex=day_data.get("uvIndex", 0),
                cloudSea=day_data.get("cloudSea")
            )
            daily_data.append(daily)

        return WeatherGridResponse(
            location=location,
            updateTime=response.get("updateTime", ""),
            daily=daily_data
        )

    @handle_api_errors
    def get_weather_7d(self, location: str, lang: str = "zh") -> WeatherGridResponse:
        """获取7天天气预报"""
        endpoint = "weather/7d"
        params = {
            "location": location,
            "key": self.config.WEATHER_API_KEY,
            "lang": lang
        }

        response = self._make_request("GET", endpoint, params=params)

        # 转换为模型
        daily_data = []
        for day_data in response.get("daily", []):
            daily = WeatherDaily(
                fxDate=day_data["fxDate"],
                tempMax=day_data["tempMax"],
                tempMin=day_data["tempMin"],
                icon=day_data["icon"],
                textDay=day_data["textDay"],
                textNight=day_data["textNight"],
                windScaleDay=day_data["windScaleDay"],
                windScaleNight=day_data["windScaleNight"],
                humidity=day_data["humidity"],
                precipitation=day_data.get("precip", 0),
                pop=day_data.get("pop", 0),
                uvIndex=day_data.get("uvIndex", 0),
                cloudSea=day_data.get("cloudSea")
            )
            daily_data.append(daily)

        return WeatherGridResponse(
            location=location,
            updateTime=response.get("updateTime", ""),
            daily=daily_data
        )

    @handle_api_errors
    def get_grid_weather(self, grid_id: str, lang: str = "zh") -> WeatherGridResponse:
        """获取格点天气"""
        endpoint = "gridWeather/3d"
        params = {
            "gridId": grid_id,
            "key": self.config.WEATHER_API_KEY,
            "lang": lang
        }

        response = self._make_request("GET", endpoint, params=params)

        # 转换为模型
        daily_data = []
        for day_data in response.get("daily", []):
            daily = WeatherDaily(
                fxDate=day_data["fxDate"],
                tempMax=day_data["tempMax"],
                tempMin=day_data["tempMin"],
                icon=day_data["icon"],
                textDay=day_data["textDay"],
                textNight=day_data["textNight"],
                windScaleDay=day_data["windScaleDay"],
                windScaleNight=day_data["windScaleNight"],
                humidity=day_data["humidity"],
                precipitation=day_data.get("precip", 0),
                pop=day_data.get("pop", 0),
                uvIndex=day_data.get("uvIndex", 0),
                cloudSea=day_data.get("cloudSea")
            )
            daily_data.append(daily)

        return WeatherGridResponse(
            location=grid_id,
            updateTime=response.get("updateTime", ""),
            daily=daily_data
        )

    @handle_api_errors
    def get_grid_weather_now(self, grid_id: str, lang: str = "zh") -> Dict:
        """获取格点实时天气"""
        endpoint = "gridWeather/now"
        params = {
            "gridId": grid_id,
            "key": self.config.WEATHER_API_KEY,
            "lang": lang
        }
        return self._make_request("GET", endpoint, params=params)

    @handle_api_errors
    def get_cloud_sea(self, location: str, lang: str = "zh") -> WeatherCloudSeaAnalysis:
        """获取云海指数"""
        endpoint = "cloudSea"
        params = {
            "location": location,
            "key": self.config.WEATHER_API_KEY,
            "lang": lang
        }

        response = self._make_request("GET", endpoint, params=params)

        # 转换为模型
        return WeatherCloudSeaAnalysis(
            score=response.get("score", 0),
            factors=response.get("factors", []),
            conditions=response.get("conditions", {})
        )

    def get_location_coords(self, location: str) -> Optional[str]:
        """获取位置的坐标ID"""
        if location in self.location_cache:
            return self.location_cache[location]

        try:
            # 这里简化处理，实际应该先调用地理编码API
            # 假设location已经是坐标ID或城市名
            self.location_cache[location] = location
            return location
        except Exception:
            return None

    def get_weather_summary(self, locations: List[str], trip_date: str,
                          forecast_days: int = 3) -> WeatherSummary:
        """获取天气汇总"""
        weather_summary = WeatherSummary(
            trip_date=trip_date,
            forecast_days=forecast_days,
            use_grid=False
        )

        for location in locations:
            # 获取3天预报
            forecast = self.get_weather_3d(location)
            if weather_summary.forecast_3d is None:
                weather_summary.forecast_3d = forecast
            else:
                # 合并预报数据
                weather_summary.forecast_3d.daily.extend(forecast.daily)

        # 计算汇总信息
        if weather_summary.forecast_3d:
            all_temps = []
            for day in weather_summary.forecast_3d.daily:
                all_temps.extend([day.tempMax, day.tempMin])

            if all_temps:
                weather_summary.max_temp = max(all_temps)
                weather_summary.min_temp = min(all_temps)

        return weather_summary

    def check_weather_safety(self, location: str, trip_date: str) -> Dict:
        """检查天气安全性"""
        try:
            # 获取3天天气预报
            forecast = self.get_weather_3d(location)

            safety_issues = []

            for day in forecast.daily:
                # 检查温度
                if day.tempMax > 35:
                    safety_issues.append(f"{day.fxDate}: 最高温度{day.tempMax}°C，有中暑风险")
                elif day.tempMin < -10:
                    safety_issues.append(f"{day.fxDate}: 最低温度{day.tempMin}°C，有冻伤风险")

                # 检查降水
                if day.precipitation > 50:
                    safety_issues.append(f"{day.fxDate}: 预计降水{day.precipitation}mm，有山洪风险")

                # 检查风力
                wind_scale_day = int(day.windScaleDay[0]) if day.windScaleDay.isdigit() else 0
                wind_scale_night = int(day.windScaleNight[0]) if day.windScaleNight.isdigit() else 0
                max_wind = max(wind_scale_day, wind_scale_night)

                if max_wind > 6:
                    safety_issues.append(f"{day.fxDate}: 风力{max_wind}级，不适合户外活动")

            return {
                "location": location,
                "trip_date": trip_date,
                "is_safe": len(safety_issues) == 0,
                "safety_issues": safety_issues,
                "risk_level": "低风险" if len(safety_issues) == 0 else "高风险"
            }

        except APIError as e:
            return {
                "location": location,
                "trip_date": trip_date,
                "is_safe": False,
                "safety_issues": [f"无法获取天气信息: {str(e)}"],
                "risk_level": "未知"
            }