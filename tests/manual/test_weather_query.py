"""
天气查询测试 - 真实 API
=====================

测试和风天气 API：城市天气、格点天气、逐小时预报

运行方式：
    cd D:/2_Study/Outdoor-Agent-Planner/03_Code
    python -m tests.manual.test_weather_query
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.weather_client import WeatherClient
from src.api import APIError


def test_city_weather():
    """测试城市天气预报"""
    print("\n" + "=" * 60)
    print("[1] 测试城市天气预报 (3天)")
    print("=" * 60)

    client = WeatherClient()

    # 测试城市（使用经纬度，更可靠）
    # 北京: 116.41,39.92  上海: 121.47,31.23
    test_locations = [
        ("北京", "116.41,39.92"),
        ("上海", "121.47,31.23"),
    ]

    for name, location in test_locations:
        print(f"\n[*] 查询: {name} ({location})")
        try:
            forecast = client.get_weather_3d(location)
            print(f"    更新时间: {forecast.updateTime}")

            for day in forecast.daily:
                print(f"\n    [{day.fxDate}]")
                print(f"        天气: {day.textDay}")
                print(f"        温度: {day.tempMin}°C ~ {day.tempMax}°C")
                print(f"        风力: {day.windScaleDay} 级")
                print(f"        湿度: {day.humidity}%")
                if day.uvIndex:
                    print(f"        紫外线: {day.uvIndex}")
                if day.sunrise and day.sunset:
                    print(f"        日出日落: {day.sunrise} - {day.sunset}")

        except APIError as e:
            print(f"    [!] 失败: {e}")


def test_grid_weather():
    """测试格点天气预报（经纬度）"""
    print("\n" + "=" * 60)
    print("[2] 测试格点天气预报 (3天)")
    print("=" * 60)

    client = WeatherClient()

    # 峨眉山顶坐标
    lon, lat = 103.48, 29.53

    print(f"\n[*] 查询坐标: {lon}, {lat}")
    try:
        forecast = client.get_grid_weather_3d(lon, lat)
        print(f"    更新时间: {forecast.updateTime}")

        for day in forecast.daily:
            print(f"\n    [{day.fxDate}]")
            print(f"        天气: {day.textDay}")
            print(f"        温度: {day.tempMin}°C ~ {day.tempMax}°C")
            print(f"        风力: {day.windScaleDay} 级")
            print(f"        湿度: {day.humidity}%")
            print(f"        降水: {day.precip}mm")

    except APIError as e:
        print(f"    [!] 失败: {e}")


def test_hourly_weather():
    """测试逐小时天气预报"""
    print("\n" + "=" * 60)
    print("[3] 测试逐小时天气预报 (24小时)")
    print("=" * 60)

    client = WeatherClient()

    # 使用经纬度
    location = "116.41,39.92"  # 北京
    print(f"\n[*] 查询: 北京 ({location})")

    try:
        forecast = client.get_hourly_weather(location, hours=24)
        print(f"    更新时间: {forecast.updateTime}")
        print(f"    小时数: {len(forecast.hourly)}")

        # 显示前 8 小时
        print(f"\n    [未来 8 小时]:")
        for hour in forecast.hourly[:8]:
            time_str = hour.fxTime.split("T")[1][:5] if "T" in hour.fxTime else hour.fxTime
            print(f"        {time_str} | {hour.temp}°C | 降水概率 {hour.pop}% | 风力 {hour.windScale}级")

    except APIError as e:
        print(f"    [!] 失败: {e}")


def test_geo_lookup():
    """测试地理编码（位置查询）- 跳过"""
    print("\n" + "=" * 60)
    print("[4] 测试地理编码 - 跳过")
    print("=" * 60)
    print("\n[*] 说明: 和风天气 geo/lookup API 不支持经纬度输入")
    print("    推荐直接使用经纬度查询天气（如 test_grid_weather）")


def test_weather_safety():
    """测试天气安全检查"""
    print("\n" + "=" * 60)
    print("[5] 测试天气安全检查")
    print("=" * 60)

    client = WeatherClient()

    # 使用经纬度
    location = "116.41,39.92"  # 北京
    trip_date = "2026-03-15"

    print(f"\n[*] 检查: 北京 ({location}) - {trip_date}")

    try:
        result = client.check_weather_safety(location, trip_date)
        print(f"    安全: {result.get('is_safe', False)}")
        print(f"    风险等级: {result.get('risk_level', '未知')}")

        issues = result.get('safety_issues', [])
        if issues:
            print(f"    注意事项:")
            for issue in issues:
                print(f"        - {issue}")

    except APIError as e:
        print(f"    [!] 失败: {e}")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("和风天气 API 测试 - 真实调用")
    print("=" * 60)

    # 1. 城市天气
    test_city_weather()

    # 2. 格点天气
    test_grid_weather()

    # 3. 逐小时天气
    test_hourly_weather()

    # 4. 地理编码
    test_geo_lookup()

    # 5. 安全检查
    test_weather_safety()

    print("\n" + "=" * 60)
    print("[OK] 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
