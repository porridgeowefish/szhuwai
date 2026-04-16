"""
天气查询工具
============

提供格点天气查询功能。
"""

from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.services.weather_service import WeatherService


class WeatherQueryInput(BaseModel):
    """天气查询输入参数"""
    lon: float = Field(..., description="经度，例如：116.407526")
    lat: float = Field(..., description="纬度，例如：39.904030")
    trip_date: str = Field(
        ...,
        description="出行日期，格式：YYYY-MM-DD，例如：2025-05-01"
    )


@tool("weather_query", args_schema=WeatherQueryInput)
def weather_query(lon: float, lat: float, trip_date: str) -> str:
    """
    查询指定位置的格点天气预报。

    该工具会获取指定位置的详细天气预报，包括：
    - 3天格点天气预报
    - 24小时逐小时天气
    - 多抽样点天气（起点、终点、最高点等）
    - 温度、降水、风力、湿度等信息

    Args:
        lon: 经度
        lat: 纬度
        trip_date: 出行日期 (YYYY-MM-DD)

    Returns:
        str: 格式化的天气信息字符串
    """
    try:
        # 创建服务实例
        service = WeatherService()

        # 获取天气汇总
        summary = service.get_summary(
            lon=lon,
            lat=lat,
            trip_date=trip_date,
            include_hourly=True,
            include_multi_point=True
        )

        # 格式化输出
        output_parts = [
            "=== 天气预报信息 ===",
            f"查询位置: ({lon:.6f}, {lat:.6f})",
            f"出行日期: {trip_date}",
            f"预报天数: {summary.forecast_days} 天",
            f"数据源: 格点天气 ({'高精度' if summary.use_grid else '城市天气'})",
            f""
        ]

        # 添加警告信息
        if summary.warning:
            output_parts.append(f"⚠️ 天气警告: {summary.warning}")
            output_parts.append("")

        # 添加3天预报
        if summary.forecast_3d and summary.forecast_3d.daily:
            output_parts.append("=== 3天天气预报 ===")
            for i, day in enumerate(summary.forecast_3d.daily, 1):
                output_parts.extend([
                    f"第 {i} 天 ({day.fxDate}):",
                    f"  天气: {day.textDay}",
                    f"  温度: {day.tempMin}°C ~ {day.tempMax}°C",
                    f"  风力: {day.windScaleDay}级",
                    f"  风速: {day.windSpeedDay} km/h",
                    f"  湿度: {day.humidity}%",
                    f"  降水: {day.precip}mm",
                    f"  气压: {day.pressure} hPa",
                    f""
                ])

        # 添加24小时逐小时天气（仅显示前6小时作为示例）
        if summary.hourly_24h and summary.hourly_24h.hourly:
            output_parts.append("=== 24小时逐小时天气 (前6小时) ===")
            for hour in summary.hourly_24h.hourly[:6]:
                output_parts.append(
                    f"{hour.fxTime}: {hour.temp}°C, "
                    f"降水概率 {hour.pop}%, "
                    f"降水 {hour.precip}mm, "
                    f"风力 {hour.windScale}"
                )
            output_parts.append("")

        # 添加多抽样点天气
        if summary.grid_points:
            output_parts.append("=== 多抽样点实时天气 ===")
            for point in summary.grid_points:
                point_type = point.get("point_type", "未知")
                temp = point.get("temp", "N/A")
                wind = point.get("wind_scale", "N/A")
                humidity = point.get("humidity", "N/A")
                output_parts.append(
                    f"{point_type}: 温度 {temp}°C, 风力 {wind}级, 湿度 {humidity}%"
                )
            output_parts.append("")

        # 添加汇总信息
        if summary.summary:
            output_parts.append("=== 天气汇总 ===")
            if summary.summary.conditions:
                output_parts.append(f"天气条件: {summary.summary.conditions}")
            if summary.summary.recommendation:
                output_parts.append(f"建议: {summary.summary.recommendation}")
            if summary.summary.risk_level:
                output_parts.append(f"风险等级: {summary.summary.risk_level}")

        return "\n".join(output_parts)

    except Exception as e:
        return f"错误: 天气查询失败 - {str(e)}"
