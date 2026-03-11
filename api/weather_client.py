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
    WeatherBaseDaily,
    CityWeatherDaily,
    GridWeatherDaily,
    HourlyWeather,
    CityWeatherResponse,
    GridWeatherResponse,
    HourlyWeatherResponse,
    WeatherCloudSeaAnalysis,
    WeatherSummary
)


class WeatherClient(BaseAPIClient):
    """和风天气API客户端"""

    def __init__(self, config=None):
        super().__init__(config or api_config)
        # 使用开发者主机URL格式
        self.base_url = f"https://{self.config.WEATHER_DEVELOPER_HOST}.qweatherapi.com/v7"
        self.location_cache = {}

    def validate_response(self, response: Dict) -> bool:
        """验证API响应格式"""
        if "code" not in response:
            return False
        return response["code"] == "200"

    def _make_weather_request(self, method: str, endpoint: str, params: Dict = None,
                              data: Dict = None, timeout: int = None) -> Dict:
        """发送天气API请求（使用X-QW-Api-Key认证头）"""
        weather_headers = {
            "X-QW-Api-Key": self.config.WEATHER_API_KEY,
            "User-Agent": "Outdoor-Agent-Planner/1.0",
            "Accept-Encoding": "gzip"
        }

        return self._make_request(method, endpoint, params, data, weather_headers, timeout)

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
    def get_weather_3d(self, location: str, lang: str = "zh") -> CityWeatherResponse:
        """获取城市3天天气预报"""
        endpoint = "weather/3d"
        params = {"location": location, "lang": lang}

        response = self._make_weather_request("GET", endpoint, params=params)

        # 转换为CityWeatherDaily模型
        daily_data = []
        for day_data in response.get("daily", []):
            daily = CityWeatherDaily(
                fxDate=day_data["fxDate"],
                tempMax=day_data["tempMax"],
                tempMin=day_data["tempMin"],
                textDay=day_data["textDay"],
                windScaleDay=day_data["windScaleDay"],
                windSpeedDay=day_data.get("windSpeedDay", 0),
                humidity=day_data["humidity"],
                precip=day_data.get("precip", 0),
                pressure=day_data.get("pressure", 0),
                uvIndex=day_data.get("uvIndex", 0),
                vis=day_data.get("vis", 0),
                cloud=day_data.get("cloud"),
                sunrise=day_data.get("sunrise"),
                sunset=day_data.get("sunset")
            )
            daily_data.append(daily)

        return CityWeatherResponse(
            location=location,
            updateTime=response.get("updateTime", ""),
            daily=daily_data
        )

    @handle_api_errors
    def get_weather_7d(self, location: str, lang: str = "zh") -> CityWeatherResponse:
        """获取7天天气预报"""
        endpoint = "weather/7d"
        params = {"location": location, "lang": lang}

        response = self._make_weather_request("GET", endpoint, params=params)

        # 转换为CityWeatherDaily模型
        daily_data = []
        for day_data in response.get("daily", []):
            daily = CityWeatherDaily(
                fxDate=day_data["fxDate"],
                tempMax=day_data["tempMax"],
                tempMin=day_data["tempMin"],
                textDay=day_data["textDay"],
                windScaleDay=day_data["windScaleDay"],
                windSpeedDay=day_data.get("windSpeedDay", 0),
                humidity=day_data["humidity"],
                precip=day_data.get("precip", 0),
                pressure=day_data.get("pressure", 0),
                uvIndex=day_data.get("uvIndex", 0),
                vis=day_data.get("vis", 0),
                cloud=day_data.get("cloud"),
                sunrise=day_data.get("sunrise"),
                sunset=day_data.get("sunset")
            )
            daily_data.append(daily)

        return CityWeatherResponse(
            location=location,
            updateTime=response.get("updateTime", ""),
            daily=daily_data
        )

    @handle_api_errors
    def get_grid_weather_3d(self, lon: float, lat: float, lang: str = "zh") -> GridWeatherResponse:
        """获取格点3天天气预报（仅支持经纬度）"""
        endpoint = "grid-weather/3d"
        location = f"{lon},{lat}"  # 注意顺序：经度,纬度
        params = {"location": location, "lang": lang}

        response = self._make_weather_request("GET", endpoint, params=params)

        # 转换为GridWeatherDaily模型
        daily_data = []
        for day_data in response.get("daily", []):
            daily = GridWeatherDaily(
                fxDate=day_data["fxDate"],
                tempMax=day_data["tempMax"],
                tempMin=day_data["tempMin"],
                textDay=day_data["textDay"],
                windScaleDay=day_data["windScaleDay"],
                windSpeedDay=day_data.get("windSpeedDay", 0),
                humidity=day_data["humidity"],
                precip=day_data.get("precip", 0),
                pressure=day_data.get("pressure", 0)
            )
            daily_data.append(daily)

        return GridWeatherResponse(
            location=location,
            updateTime=response.get("updateTime", ""),
            daily=daily_data
        )

    @handle_api_errors
    def get_grid_weather_now(self, lon: float, lat: float, lang: str = "zh") -> Dict:
        """获取格点实时天气"""
        endpoint = "grid-weather/now"
        location = f"{lon},{lat}"
        params = {"location": location, "lang": lang}
        return self._make_weather_request("GET", endpoint, params=params)

    @handle_api_errors
    def get_cloud_sea(self, location: str, lang: str = "zh") -> WeatherCloudSeaAnalysis:
        """获取云海指数"""
        endpoint = "cloudSea"
        params = {"location": location, "lang": lang}

        response = self._make_weather_request("GET", endpoint, params=params)

        # 转换为模型
        return WeatherCloudSeaAnalysis(
            score=response.get("score", 0),
            factors=response.get("factors", []),
            conditions=response.get("conditions", {})
        )

    @handle_api_errors
    def get_hourly_weather(self, location: str, hours: int = 24) -> HourlyWeatherResponse:
        """获取逐小时天气预报"""
        endpoint = f"weather/{hours}h"
        params = {"location": location}

        response = self._make_weather_request("GET", endpoint, params=params)

        # 转换为HourlyWeather模型
        hourly_data = []
        for hour_data in response.get("hourly", []):
            hourly = HourlyWeather(
                fxTime=hour_data["fxTime"],
                temp=hour_data["temp"],
                pop=hour_data["pop"],
                precip=hour_data["precip"],
                windScale=hour_data["windScale"]
            )
            hourly_data.append(hourly)

        return HourlyWeatherResponse(
            location=location,
            updateTime=response.get("updateTime", ""),
            hourly=hourly_data
        )

    def calculate_cloud_sea_probability(self, city_weather: CityWeatherDaily,
                                       summit_weather: GridWeatherDaily) -> Dict:
        """计算云海生成概率"""
        conditions = {
            "high_humidity": city_weather.humidity > 95,
            "low_wind": city_weather.windSpeedDay < 12,
            "inversion_layer": summit_weather.tempMin > city_weather.tempMin
        }

        probability = 0
        if conditions["high_humidity"]:
            probability += 40
        if conditions["low_wind"]:
            probability += 30
        if conditions["inversion_layer"]:
            probability += 30

        return {
            "probability": probability,
            "conditions": conditions,
            "assessment": "极佳" if probability >= 80 else
                         "良好" if probability >= 60 else
                         "一般" if probability >= 40 else "不佳"
        }

    def check_weather_safety(self, city_forecast: List[CityWeatherDaily],
                           summit_forecast: List[GridWeatherDaily]) -> Dict:
        """硬性安全熔断检查"""
        safety_issues = []

        # 极端温度检查
        for day in city_forecast:
            if day.tempMax > 35:
                safety_issues.append({
                    "type": "极端高温",
                    "date": day.fxDate,
                    "value": day.tempMax,
                    "risk": "中暑风险"
                })
            elif day.tempMin < -10:
                safety_issues.append({
                    "type": "极端低温",
                    "date": day.fxDate,
                    "value": day.tempMin,
                    "risk": "冻伤风险"
                })

        # 暴雨预警
        for day in city_forecast:
            if day.precip > 50.0:
                safety_issues.append({
                    "type": "暴雨预警",
                    "date": day.fxDate,
                    "value": day.precip,
                    "risk": "山洪风险"
                })

        # 失温风险
        for day in city_forecast:
            if (day.tempMax < 15 and
                day.precip > 5.0 and
                int(day.windScaleDay[0]) > 5):
                safety_issues.append({
                    "type": "失温风险",
                    "date": day.fxDate,
                    "risk": "冷雨+风寒"
                })

        return {
            "is_safe": len(safety_issues) == 0,
            "safety_issues": safety_issues,
            "risk_level": "低风险" if len(safety_issues) == 0 else "高风险"
        }

    def get_location_coords(self, location: str) -> Dict[str, float]:
        """获取位置的经纬度坐标"""
        # 首先检查缓存
        if location in self.location_cache:
            return self.location_cache[location]

        # 调用和风天气的地理编码API
        endpoint = "geo/lookup"
        params = {
            "location": location,
            "key": self.config.WEATHER_API_KEY,
            "lang": "zh"
        }

        response = self._make_weather_request("GET", endpoint, params=params)

        if response.get("location"):
            geo_result = response["location"][0]
            coords = {
                "lon": float(geo_result["lon"]),
                "lat": float(geo_result["lat"])
            }
            self.location_cache[location] = coords
            return coords
        else:
            raise APIError(f"找不到位置: {location}")

    def prepare_location_for_apis(self, location: str) -> Dict[str, str]:
        """为不同API准备位置参数"""
        # 如果是经纬度格式（如"116.41,39.92"），直接使用
        if ',' in location:
            parts = location.split(',')
            if len(parts) == 2 and all(x.replace('.', '').isdigit() for x in parts):
                return {
                    "city_api": location,  # 城市API也支持坐标
                    "grid_api": location,   # 格点API必须使用坐标
                    "hourly_api": location,
                    "coords": {"lon": float(parts[0]), "lat": float(parts[1])}
                }

        # 否则进行地理编码
        coords = self.get_location_coords(location)
        coords_str = f"{coords['lon']},{coords['lat']}"

        return {
            "city_api": location,  # 城市API使用LocationID或地名
            "grid_api": coords_str,  # 格点API使用坐标
            "hourly_api": location,  # 小时预报使用LocationID
            "coords": coords
        }

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

    def get_comprehensive_weather(self, city_name: str,
                               summit_coords: Dict[str, float]) -> Dict:
        """获取综合天气数据（城市+山顶+时间轴）"""
        # 准备位置参数
        city_params = self.prepare_location_for_apis(city_name)

        # 获取城市预报（包含紫外线、能见度）
        city_forecast = self.get_weather_3d(city_params["city_api"])

        # 获取山顶格点预报
        summit_forecast = self.get_grid_weather_3d(
            summit_coords['lon'],
            summit_coords['lat']
        )

        # 获取逐小时预报（用于时间轴规划）
        hourly_forecast = self.get_hourly_weather(city_params["hourly_api"])

        # 计算云海概率
        if city_forecast.daily and summit_forecast.daily:
            cloud_sea = self.calculate_cloud_sea_probability(
                city_forecast.daily[0],
                summit_forecast.daily[0]
            )
        else:
            cloud_sea = {"probability": 0, "assessment": "无法计算"}

        # 安全检查
        safety = self.check_weather_safety(city_forecast.daily, summit_forecast.daily)

        return {
            "city_forecast": city_forecast,
            "summit_forecast": summit_forecast,
            "hourly_forecast": hourly_forecast,
            "cloud_sea_probability": cloud_sea,
            "safety_assessment": safety
        }

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