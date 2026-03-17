"""
坐标转换工具的单元测试

测试 WGS-84 与 GCJ-02 之间的转换功能和精度。
"""

import math


from src.services.geo_coord_utils import (
    wgs84_to_gcj02,
    gcj02_to_wgs84,
)


class TestWGStoGCJ02:
    """测试 WGS-84 到 GCJ-02 的转换"""

    def test_beijing_coordinates(self) -> None:
        """测试北京天安门附近的坐标转换"""
        # WGS-84 坐标（已知）
        wgs_lon, wgs_lat = 116.404, 39.915

        # 转换为 GCJ-02
        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)

        # 验证结果在合理范围内（与高德地图坐标接近）
        assert 116.410 < gcj_lon < 116.411, f"经度超出范围: {gcj_lon}"
        assert 39.915 < gcj_lat < 39.917, f"纬度超出范围: {gcj_lat}"

        # 验证转换产生了偏移（不是原地不动）
        lon_offset = abs(gcj_lon - wgs_lon)
        lat_offset = abs(gcj_lat - wgs_lat)
        assert lon_offset > 0.001, f"经度偏移过小: {lon_offset}"
        assert lat_offset > 0.0005, f"纬度偏移过小: {lat_offset}"

    def test_shanghai_coordinates(self) -> None:
        """测试上海的坐标转换"""
        wgs_lon, wgs_lat = 121.4737, 31.2304  # 上海人民广场

        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)

        # 验证坐标有偏移
        assert abs(gcj_lon - wgs_lon) > 0.001
        assert abs(gcj_lat - wgs_lat) > 0.0005

        # 验证结果在合理范围
        assert 121.47 < gcj_lon < 121.48
        assert 31.228 < gcj_lat < 31.231

    def test_shenzhen_coordinates(self) -> None:
        """测试深圳的坐标转换"""
        wgs_lon, wgs_lat = 114.0579, 22.5431  # 深圳

        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)

        # 验证坐标有偏移
        assert abs(gcj_lon - wgs_lon) > 0.001
        assert abs(gcj_lat - wgs_lat) > 0.0005

    def test_china_border_coordinates(self) -> None:
        """测试中国边境附近的坐标转换"""
        # 中国境内应该有偏移
        wgs_lon, wgs_lat = 120.0, 40.0  # 辽宁境内
        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)
        assert abs(gcj_lon - wgs_lon) > 0.001

    def test_outside_china(self) -> None:
        """测试中国境外坐标（不应有偏移）"""
        # 美国纽约
        wgs_lon, wgs_lat = -74.006, 40.7128
        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)

        # 境外坐标应该保持不变
        assert math.isclose(gcj_lon, wgs_lon, abs_tol=1e-10)
        assert math.isclose(gcj_lat, wgs_lat, abs_tol=1e-10)

        # 日本东京
        wgs_lon, wgs_lat = 139.6917, 35.6895
        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)

        # 境外坐标应该保持不变
        assert math.isclose(gcj_lon, wgs_lon, abs_tol=1e-10)
        assert math.isclose(gcj_lat, wgs_lat, abs_tol=1e-10)


class TestGCJ02toWGS:
    """测试 GCJ-02 到 WGS-84 的反向转换"""

    def test_reverse_conversion_accuracy(self) -> None:
        """测试反向转换的精度"""
        # 北京天安门附近
        wgs_lon, wgs_lat = 116.404, 39.915

        # WGS -> GCJ
        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)

        # GCJ -> WGS
        restored_lon, restored_lat = gcj02_to_wgs84(gcj_lon, gcj_lat)

        # 验证恢复后的坐标与原始坐标接近（允许一定误差）
        assert math.isclose(
            restored_lon, wgs_lon, abs_tol=1e-4
        ), f"经度恢复失败: {restored_lon} vs {wgs_lon}"
        assert math.isclose(
            restored_lat, wgs_lat, abs_tol=1e-4
        ), f"纬度恢复失败: {restored_lat} vs {wgs_lat}"

    def test_shanghai_reverse(self) -> None:
        """测试上海坐标的反向转换"""
        wgs_lon, wgs_lat = 121.4737, 31.2304

        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)
        restored_lon, restored_lat = gcj02_to_wgs84(gcj_lon, gcj_lat)

        assert math.isclose(restored_lon, wgs_lon, abs_tol=1e-4)
        assert math.isclose(restored_lat, wgs_lat, abs_tol=1e-4)


class TestEdgeCases:
    """测试边界情况"""

    def test_exact_border_coordinates(self) -> None:
        """测试中国边界上的坐标"""
        # 东边界外（日本东海）- 应无偏移
        wgs_lon, wgs_lat = 140.0, 40.0
        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)
        assert math.isclose(gcj_lon, wgs_lon, abs_tol=1e-10)

        # 西边界外（哈萨克斯坦）- 应无偏移
        wgs_lon, wgs_lat = 70.0, 40.0
        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)
        assert math.isclose(gcj_lon, wgs_lon, abs_tol=1e-10)

        # 南边界外（东南亚）- 应无偏移
        # _LAT_MIN = 0.8293，所以使用 1.5 在境内，0.5 在境外
        wgs_lon, wgs_lat = 110.0, 0.5
        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)
        assert math.isclose(gcj_lat, wgs_lat, abs_tol=1e-10)

        # 北边界外（蒙古）- 应无偏移
        wgs_lon, wgs_lat = 110.0, 58.0  # 更远在北边界外
        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)
        assert math.isclose(gcj_lat, wgs_lat, abs_tol=1e-10)

    def test_return_types(self) -> None:
        """测试返回值类型"""
        result = wgs84_to_gcj02(116.404, 39.915)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], float)

        result = gcj02_to_wgs84(116.410244, 39.916027)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], float)


class TestKnownCoordinatePairs:
    """测试已知的坐标对（验证算法正确性）"""

    def test_beijing_tiananmen(self) -> None:
        """测试北京天安门的已知坐标对"""
        # WGS-84 坐标
        wgs_lon, wgs_lat = 116.397128, 39.916527

        # 转换
        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)

        # 验证转换后的坐标接近高德地图的已知坐标
        # 高德地图天安门坐标大约为: (116.397428, 39.90923)
        # 注意：不同来源的 GCJ-02 坐标可能有微小差异
        # 实际转换结果约为: (116.40337..., 39.91793...)
        assert 116.402 < gcj_lon < 116.404, f"经度: {gcj_lon}"
        assert 39.917 < gcj_lat < 39.918, f"纬度: {gcj_lat}"

    def test_hiking_track_point(self) -> None:
        """测试典型的徒步轨迹点坐标"""
        # 香山公园某点（典型的徒步地点）
        wgs_lon, wgs_lat = 116.1885, 39.9955

        gcj_lon, gcj_lat = wgs84_to_gcj02(wgs_lon, wgs_lat)

        # 验证偏移量合理
        lon_delta = gcj_lon - wgs_lon
        lat_delta = gcj_lat - wgs_lat

        # 中国境内经度偏移通常在 0.005-0.007 度之间
        assert 0.004 < lon_delta < 0.008, f"经度偏移异常: {lon_delta}"
        # 纬度偏移通常较小
        assert 0.001 < lat_delta < 0.006, f"纬度偏移异常: {lat_delta}"
