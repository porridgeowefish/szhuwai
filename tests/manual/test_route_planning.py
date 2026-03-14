"""
路线规划测试 - 真实 API
======================

测试高德地图 API：地理编码、公交路线、驾车路线

运行方式：
    cd D:/2_Study/Outdoor-Agent-Planner/03_Code
    python -m tests.manual.test_route_planning
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.map_client import MapClient
from src.api import APIError


def test_geocode():
    """测试地理编码"""
    print("\n" + "=" * 60)
    print("[1] 测试地理编码")
    print("=" * 60)

    client = MapClient()

    # 测试地址
    test_addresses = [
        "北京西站",
        "天安门",
    ]

    results = []
    for address in test_addresses:
        print(f"\n[*] 解析: {address}")
        try:
            geo = client.geocode(address)
            print(f"    地址: {geo.address}")
            print(f"    坐标: {geo.lon}, {geo.lat}")
            print(f"    城市: {geo.city}")
            results.append((address, f"{geo.lon},{geo.lat}"))
        except APIError as e:
            print(f"    [!] 失败: {e}")

    return results


def test_transit_route(origin_coord: str, dest_coord: str, city: str):
    """测试公交路线规划"""
    print("\n" + "=" * 60)
    print("[2] 测试公交路线规划")
    print("=" * 60)

    client = MapClient()

    print(f"\n[*] 路线: {origin_coord} -> {dest_coord} (城市: {city})")

    try:
        routes = client.transit_route(origin_coord, dest_coord, city)
        print(f"    找到 {len(routes)} 条公交路线")

        for i, route in enumerate(routes, 1):
            print(f"\n    [方案 {i}]")
            print(f"        时长: {route.duration_min} 分钟")
            print(f"        距离: {route.distance_km:.1f} 公里")
            print(f"        费用: {route.cost_yuan} 元")
            print(f"        步行: {route.walking_distance} 米")

            if route.segments:
                print(f"        路线段:")
                for seg in route.segments[:3]:
                    print(f"            - {seg.type}: {seg.line_name}")
                    print(f"              {seg.departure_stop} -> {seg.arrival_stop}")

        return routes
    except APIError as e:
        print(f"    [!] 失败: {e}")
        return []


def test_driving_route(origin_coord: str, dest_coord: str):
    """测试驾车路线规划"""
    print("\n" + "=" * 60)
    print("[3] 测试驾车路线规划")
    print("=" * 60)

    client = MapClient()

    print(f"\n[*] 路线: {origin_coord} -> {dest_coord}")

    try:
        route = client.driving_route(origin_coord, dest_coord)
        print(f"    时长: {route.duration_min} 分钟")
        print(f"        距离: {route.distance_km:.1f} 公里")
        print(f"        过路费: {route.tolls_yuan} 元")
        if route.taxi_cost_yuan:
            print(f"        出租车预估: {route.taxi_cost_yuan} 元")

        return route
    except APIError as e:
        print(f"    [!] 失败: {e}")
        return None


def test_reverse_geocode(coord: str):
    """测试逆地理编码"""
    print("\n" + "=" * 60)
    print("[4] 测试逆地理编码")
    print("=" * 60)

    client = MapClient()

    print(f"\n[*] 坐标: {coord}")

    try:
        result = client.reverse_geocode(coord)
        print(f"    地址: {result.address}")
        print(f"    省: {result.province}")
        print(f"    市: {result.city}")
        print(f"    区: {result.district}")

        if result.pois:
            print(f"    周边 POI ({len(result.pois)} 个):")
            for poi in result.pois[:3]:
                print(f"        - {poi.name} ({poi.distance}m)")

        return result
    except APIError as e:
        print(f"    [!] 失败: {e}")
        return None


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("高德地图 API 测试 - 真实调用")
    print("=" * 60)

    # 1. 测试地理编码
    geocode_results = test_geocode()

    if len(geocode_results) >= 2:
        origin_coord = geocode_results[0][1]
        dest_coord = geocode_results[1][1]

        # 2. 测试公交路线
        test_transit_route(origin_coord, dest_coord, "北京")

        # 3. 测试驾车路线
        test_driving_route(origin_coord, dest_coord)

    # 4. 测试逆地理编码
    test_reverse_geocode("116.397428,39.90923")  # 天安门坐标

    print("\n" + "=" * 60)
    print("[OK] 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
