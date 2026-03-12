"""
Weather Analyzer
================

天气业务分析服务，将纯业务逻辑从 API Client 中抽离。

职责：
- 计算云海生成概率
- 安全熔断检查
- 天气风险评估
"""

from typing import List, Dict, Any, Optional
from schemas.weather import CityWeatherDaily, GridWeatherDaily


class WeatherAnalyzer:
    """天气业务分析器"""

    def calculate_cloud_sea_probability(
        self,
        city_weather: CityWeatherDaily,
        summit_weather: GridWeatherDaily
    ) -> Dict[str, Any]:
        """
        计算云海生成概率

        云海形成条件：
        1. 高湿度：城市湿度 > 95%
        2. 低风速：风速 < 12 km/h
        3. 逆温层：山顶最低温度 > 城市最低温度
        """
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
            "assessment": self._get_cloud_sea_assessment(probability)
        }

    def _get_cloud_sea_assessment(self, probability: int) -> str:
        """根据概率获取评估等级"""
        if probability >= 80:
            return "极佳"
        elif probability >= 60:
            return "良好"
        elif probability >= 40:
            return "一般"
        else:
            return "不佳"

    def check_weather_safety(
        self,
        city_forecast: List[CityWeatherDaily],
        summit_forecast: Optional[List[GridWeatherDaily]] = None
    ) -> Dict[str, Any]:
        """
        硬性安全熔断检查

        检查项：
        1. 极端温度：高温 > 35°C，低温 < -10°C
        2. 暴雨预警：降水量 > 50mm
        3. 失温风险：低温 + 高降水 + 大风
        """
        safety_issues: List[Dict[str, Any]] = []

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
            wind_scale_value = self._parse_wind_scale(day.windScaleDay)
            if (day.tempMax < 15 and
                day.precip > 5.0 and
                wind_scale_value > 5):
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

    def check_weather_safety_by_location(
        self,
        location: str,
        trip_date: str,
        forecast: List[CityWeatherDaily]
    ) -> Dict[str, Any]:
        """
        检查天气安全性（基于城市预报）

        用于直接接收 API 返回的预报数据进行安全检查。
        """
        safety_issues: List[str] = []

        for day in forecast:
            # 检查温度
            if day.tempMax > 35:
                safety_issues.append(
                    f"{day.fxDate}: 最高温度{day.tempMax}°C，有中暑风险"
                )
            elif day.tempMin < -10:
                safety_issues.append(
                    f"{day.fxDate}: 最低温度{day.tempMin}°C，有冻伤风险"
                )

            # 检查降水
            if day.precip > 50:
                safety_issues.append(
                    f"{day.fxDate}: 预计降水{day.precip}mm，有山洪风险"
                )

            # 检查风力
            wind_scale = self._parse_wind_scale(day.windScaleDay)
            if wind_scale > 6:
                safety_issues.append(
                    f"{day.fxDate}: 风力{wind_scale}级，不适合户外活动"
                )

        return {
            "location": location,
            "trip_date": trip_date,
            "is_safe": len(safety_issues) == 0,
            "safety_issues": safety_issues,
            "risk_level": "低风险" if len(safety_issues) == 0 else "高风险"
        }

    def _parse_wind_scale(self, wind_scale_str: str) -> int:
        """解析风力等级字符串"""
        if wind_scale_str.isdigit():
            return int(wind_scale_str[0])
        elif wind_scale_str and wind_scale_str[0].isdigit():
            return int(wind_scale_str[0])
        return 0

    def get_comprehensive_analysis(
        self,
        city_forecast: List[CityWeatherDaily],
        summit_forecast: Optional[List[GridWeatherDaily]] = None
    ) -> Dict[str, Any]:
        """
        获取综合天气分析

        整合云海概率计算和安全检查
        """
        result = {
            "cloud_sea_probability": None,
            "safety_assessment": None
        }

        # 计算云海概率（需要山顶数据）
        if summit_forecast and city_forecast:
            result["cloud_sea_probability"] = self.calculate_cloud_sea_probability(
                city_forecast[0],
                summit_forecast[0]
            )

        # 安全检查
        result["safety_assessment"] = self.check_weather_safety(
            city_forecast,
            summit_forecast
        )

        return result