"""
Weather API Client
==================

Client for integrating with 和风天气 (QWeather) API.
"""

from typing import Dict, List

from . import BaseAPIClient, handle_api_errors, APIError
from .config import api_config
from src.schemas.weather import (
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
        # 使用开发者主机URL格式（注意：主机名已包含.qweatherapi.com）
        # 检查配置中是否已经包含了域名
        host = self.config.WEATHER_DEVELOPER_HOST
        if 'qweatherapi.com' not in host:
            host = f"{host}.qweatherapi.com"
        self.base_url = f"https://{host}/v7"
        self.location_cache = {}
        # 业务分析器（延迟导入避免循环依赖）
        self._analyzer = None

    @property
    def analyzer(self):
        """延迟加载 WeatherAnalyzer 避免循环导入"""
        if self._analyzer is None:
            from src.services.weather_analyzer import WeatherAnalyzer
            self._analyzer = WeatherAnalyzer()
        return self._analyzer

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
            "lang": lang
        }
        return self._make_weather_request("GET", endpoint, params=params)

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
                uvIndex=day_data.get("uvIndex"),  # API不返回时为 None
                vis=day_data.get("vis"),          # API不返回时为 None
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
                uvIndex=day_data.get("uvIndex"),  # API不返回时为 None
                vis=day_data.get("vis"),          # API不返回时为 None
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
    def get_grid_weather_24h(self, lon: float, lat: float, lang: str = "zh") -> HourlyWeatherResponse:
        """获取格点24小时逐小时天气预报（全天）"""
        endpoint = "grid-weather/24h"
        location = f"{lon},{lat}"  # 注意顺序：经度,纬度
        params = {"location": location, "lang": lang}

        response = self._make_weather_request("GET", endpoint, params=params)

        # 转换为HourlyWeather模型
        hourly_data = []
        for hour_data in response.get("hourly", []):
            hourly = HourlyWeather(
                fxTime=hour_data["fxTime"],
                temp=hour_data["temp"],
                pop=hour_data.get("pop", "0"),
                precip=hour_data.get("precip", "0"),
                windScale=hour_data.get("windScale", "0")
            )
            hourly_data.append(hourly)

        return HourlyWeatherResponse(
            location=location,
            updateTime=response.get("updateTime", ""),
            hourly=hourly_data
        )

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

    def get_location_coords(self, location: str) -> Dict[str, float]:
        """获取位置的经纬度坐标"""
        # 首先检查缓存
        if location in self.location_cache:
            return self.location_cache[location]

        # 调用和风天气的地理编码API
        endpoint = "geo/lookup"
        params = {
            "location": location,
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

        # 使用业务分析器计算云海概率和安全检查
        if city_forecast.daily and summit_forecast.daily:
            analysis = self.analyzer.get_comprehensive_analysis(
                city_forecast.daily,
                summit_forecast.daily
            )
            cloud_sea = analysis.get("cloud_sea_probability", {"probability": 0, "assessment": "无法计算"})
            safety = analysis.get("safety_assessment", {"is_safe": False, "safety_issues": [], "risk_level": "未知"})
        else:
            cloud_sea = {"probability": 0, "assessment": "无法计算"}
            safety = {"is_safe": False, "safety_issues": ["数据不完整"], "risk_level": "未知"}

        return {
            "city_forecast": city_forecast,
            "summit_forecast": summit_forecast,
            "hourly_forecast": hourly_forecast,
            "cloud_sea_probability": cloud_sea,
            "safety_assessment": safety
        }

    def check_weather_safety(self, location: str, trip_date: str) -> Dict:
        """检查天气安全性（便捷方法，内部使用 Analyzer）"""
        try:
            forecast = self.get_weather_3d(location)
            return self.analyzer.check_weather_safety_by_location(
                location, trip_date, forecast.daily
            )
        except APIError as e:
            return {
                "location": location,
                "trip_date": trip_date,
                "is_safe": False,
                "safety_issues": [f"无法获取天气信息: {str(e)}"],
                "risk_level": "未知"
            }