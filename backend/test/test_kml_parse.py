"""
KML 解析测试脚本
================

测试两种 KML 格式的解析能力：
1. 标准 KML 格式（LineString + coordinates）
2. Google Earth 扩展格式（gx:Track + gx:coord）

验证点：
- 能否正确解析所有轨迹点
- 能否正确提取经纬度和海拔
- 能否识别大爬升/大下降路段
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.track_parser import TrackParser
from src.schemas.track import TrackAnalysisResult


def test_parse_kml(file_path: str, expected_points: int, description: str):
    """测试 KML 文件解析"""
    print(f"\n{'='*60}")
    print(f"测试文件: {Path(file_path).name}")
    print(f"描述: {description}")
    print(f"{'='*60}")

    parser = TrackParser()

    try:
        result: TrackAnalysisResult = parser.parse_file(file_path)

        print("[OK] 解析成功！")
        print(f"   轨迹点数量: {result.track_points_count} (预期: {expected_points})")
        print(f"   总距离: {result.total_distance_km:.2f} km")
        print(f"   总爬升: {result.total_ascent_m:.1f} m")
        print(f"   总下降: {result.total_descent_m:.1f} m")
        print(f"   最高海拔: {result.max_elevation_m:.1f} m")
        print(f"   最低海拔: {result.min_elevation_m:.1f} m")
        print(f"   难度等级: {result.difficulty_level}")
        print(f"   预计用时: {result.estimated_duration_hours:.1f} 小时")

        # 检查轨迹点数量
        if result.track_points_count == expected_points:
            print("   [OK] 轨迹点数量匹配")
        else:
            print(f"   [ERROR] 轨迹点数量不匹配！实际: {result.track_points_count}, 预期: {expected_points}")

        # 检查地形变化识别
        print(f"\n   地形变化段（共 {len(result.terrain_analysis)} 段）:")
        for i, terrain in enumerate(result.terrain_analysis, 1):
            print(f"      {i}. {terrain.change_type}:")
            print(f"         海拔变化: {terrain.elevation_diff:.1f}m")
            print(f"         距离: {terrain.distance_m:.1f}m")
            print(f"         坡度: {terrain.gradient_percent:.2f}%")

        # 验证大爬升/大下降识别
        large_ascents = [t for t in result.terrain_analysis if t.change_type == "大爬升"]
        large_descents = [t for t in result.terrain_analysis if t.change_type == "大下降"]

        print(f"\n   大爬升段: {len(large_ascents)} 段")
        print(f"   大下降段: {len(large_descents)} 段")

        # 预期：应该识别出 1 个大爬升（580->1200m，620m爬升）
        # 和 1 个大下降（1250->600m，650m下降）
        if len(large_ascents) >= 1:
            print("   [OK] 成功识别大爬升段")
        else:
            print("   [WARN] 未识别到大爬升段（预期至少1段）")

        if len(large_descents) >= 1:
            print("   [OK] 成功识别大下降段")
        else:
            print("   [WARN] 未识别到大下降段（预期至少1段）")

        return True

    except Exception as e:
        print(f"[ERROR] 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("="*60)
    print("KML 解析能力测试")
    print("="*60)

    test_dir = Path(__file__).parent.parent / "test_data"

    tests = [
        {
            "file": test_dir / "test_track_gx.kml",
            "expected_points": 27,
            "description": "Google Earth 扩展格式（gx:Track + gx:coord）"
        },
        {
            "file": test_dir / "test_track_standard.kml",
            "expected_points": 27,
            "description": "标准 KML 格式（LineString + coordinates）"
        },
        {
            "file": test_dir / "test_track.kml",
            "expected_points": 5,
            "description": "原有简单测试文件"
        }
    ]

    success_count = 0
    for test in tests:
        if test["file"].exists():
            if test_parse_kml(str(test["file"]), test["expected_points"], test["description"]):
                success_count += 1
        else:
            print(f"\n[WARN] 文件不存在: {test['file']}")

    print(f"\n{'='*60}")
    print(f"测试结果: {success_count}/{len(tests)} 通过")
    print(f"{'='*60}")

    # 测试实际的大 KML 文件
    real_kml = Path(__file__).parent.parent / "2026-01-02重装南风面酃峰.kml"
    if real_kml.exists():
        print(f"\n{'='*60}")
        print(f"实际文件测试: {real_kml.name}")
        print(f"{'='*60}")

        parser = TrackParser()
        try:
            result = parser.parse_file(str(real_kml))
            print("[OK] 实际文件解析成功！")
            print(f"   轨迹点数量: {result.track_points_count}")
            print(f"   总距离: {result.total_distance_km:.2f} km")
            print(f"   总爬升: {result.total_ascent_m:.1f} m")
            print(f"   总下降: {result.total_descent_m:.1f} m")
            print(f"   最高海拔: {result.max_elevation_m:.1f} m")
            print(f"   最低海拔: {result.min_elevation_m:.1f} m")
            print(f"   大爬升段数: {len([t for t in result.terrain_analysis if t.change_type == '大爬升'])}")
            print(f"   大下降段数: {len([t for t in result.terrain_analysis if t.change_type == '大下降'])}")
        except Exception as e:
            print(f"[ERROR] 实际文件解析失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
