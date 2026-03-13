"""
Track Parser Tests
==================

测试轨迹文件解析功能，包括 GPX 和 KML 文件的解析、异常处理以及边界条件。
"""

import pytest

from services.track_parser import TrackParser, TrackParseError
from schemas.track import TrackAnalysisResult
from schemas.base import Point3D


class TestTrackParser:
    """测试 TrackParser 类"""

    @pytest.fixture
    def parser(self):
        """返回 TrackParser 实例"""
        return TrackParser()

    @pytest.fixture
    def sample_gpx_content(self) -> str:
        """示例 GPX 文件内容"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>测试轨迹</name>
    <trkseg>
      <trkpt lat="39.9042" lon="116.4074">
        <ele>100</ele>
        <time>2024-03-15T08:00:00Z</time>
      </trkpt>
      <trkpt lat="39.9050" lon="116.4080">
        <ele>150</ele>
        <time>2024-03-15T08:10:00Z</time>
      </trkpt>
      <trkpt lat="39.9060" lon="116.4090">
        <ele>250</ele>
        <time>2024-03-15T08:20:00Z</time>
      </trkpt>
      <trkpt lat="39.9070" lon="116.4100">
        <ele>300</ele>
        <time>2024-03-15T08:30:00Z</time>
      </trkpt>
      <trkpt lat="39.9080" lon="116.4110">
        <ele>200</ele>
        <time>2024-03-15T08:40:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

    @pytest.fixture
    def sample_kml_content(self) -> str:
        """示例 KML 文件内容"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>测试轨迹</name>
    <Placemark>
      <LineString>
        <coordinates>
          116.4074,39.9042,100
          116.4080,39.9050,150
          116.4090,39.9060,250
          116.4100,39.9070,300
          116.4110,39.9080,200
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>"""

    def test_parse_nonexistent_file(self, parser, data_dir):
        """测试解析不存在的文件"""
        nonexistent = data_dir / "nonexistent.gpx"
        with pytest.raises(FileNotFoundError):
            parser.parse_file(nonexistent)

    def test_parse_unsupported_format(self, parser, data_dir):
        """测试解析不支持的文件格式"""
        txt_file = data_dir / "test.txt"
        txt_file.write_text("not a track file")

        with pytest.raises(TrackParseError, match="不支持的文件格式"):
            parser.parse_file(txt_file)

    def test_parse_empty_gpx(self, parser, data_dir):
        """测试解析空的 GPX 文件"""
        gpx_file = data_dir / "empty.gpx"
        gpx_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
</gpx>""")

        with pytest.raises(TrackParseError, match="未找到轨迹点"):
            parser.parse_file(gpx_file)

    def test_parse_gpx_single_point(self, parser, data_dir):
        """测试只有一个点的 GPX 文件"""
        gpx_file = data_dir / "single_point.gpx"
        gpx_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <trkseg>
      <trkpt lat="39.9042" lon="116.4074">
        <ele>100</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>""")

        with pytest.raises(TrackParseError, match="轨迹点数量不足"):
            parser.parse_file(gpx_file)

    def test_parse_gpx_success(self, parser, data_dir, sample_gpx_content):
        """测试成功解析 GPX 文件"""
        gpx_file = data_dir / "test_track.gpx"
        gpx_file.write_text(sample_gpx_content, encoding='utf-8')

        result = parser.parse_file(gpx_file)

        assert isinstance(result, TrackAnalysisResult)
        assert result.track_name == "test_track"
        assert result.track_points_count == 5
        assert result.total_distance_km > 0
        assert result.total_ascent_m > 0
        assert result.total_descent_m > 0
        assert result.max_elevation_m > result.min_elevation_m
        assert result.start_point.elevation == 100
        assert result.end_point.elevation == 200

    def test_parse_kml_success(self, parser, data_dir, sample_kml_content):
        """测试成功解析 KML 文件"""
        kml_file = data_dir / "test_track.kml"
        kml_file.write_text(sample_kml_content, encoding='utf-8')

        result = parser.parse_file(kml_file)

        assert isinstance(result, TrackAnalysisResult)
        assert result.track_name == "test_track"
        assert result.track_points_count == 5
        assert result.total_distance_km > 0
        assert result.start_point.elevation == 100
        assert result.end_point.elevation == 200

    def test_custom_track_name(self, parser, data_dir, sample_gpx_content):
        """测试自定义轨迹名称"""
        gpx_file = data_dir / "test.gpx"
        gpx_file.write_text(sample_gpx_content, encoding='utf-8')

        result = parser.parse_file(gpx_file, track_name="自定义轨迹")

        assert result.track_name == "自定义轨迹"

    def test_large_ascent_detection(self, parser, data_dir):
        """测试大爬升路段检测"""
        # 创建包含大爬升（>200m）的 GPX 文件
        gpx_file = data_dir / "large_ascent.gpx"
        gpx_content = self._create_gpx_with_elevation_profile(
            [100, 150, 200, 300, 320, 330, 340]  # 累计爬升 > 200m
        )
        gpx_file.write_text(gpx_content, encoding='utf-8')

        result = parser.parse_file(gpx_file)

        # 应该识别出至少一个大爬升段
        large_ascents = [t for t in result.terrain_analysis if t.change_type == "大爬升"]
        assert len(large_ascents) >= 1
        # 爬升量应大于 200m
        assert large_ascents[0].elevation_diff >= 200

    def test_large_descent_detection(self, parser, data_dir):
        """测试大下降路段检测"""
        # 创建包含大下降（>300m）的 GPX 文件
        gpx_file = data_dir / "large_descent.gpx"
        gpx_content = self._create_gpx_with_elevation_profile(
            [500, 400, 300, 200, 100]  # 累计下降 > 300m
        )
        gpx_file.write_text(gpx_content, encoding='utf-8')

        result = parser.parse_file(gpx_file)

        # 应该识别出大下降段
        large_descents = [t for t in result.terrain_analysis if t.change_type == "大下降"]
        assert len(large_descents) >= 1
        # 下降量应大于 300m
        assert large_descents[0].elevation_diff >= 300

    def test_elevation_stats(self, parser, data_dir, sample_gpx_content):
        """测试海拔统计"""
        gpx_file = data_dir / "elevation_test.gpx"
        gpx_file.write_text(sample_gpx_content, encoding='utf-8')

        result = parser.parse_file(gpx_file)

        assert result.max_elevation_m == 300
        assert result.min_elevation_m == 100
        assert result.elevation_range == 200
        assert 100 < result.avg_elevation_m < 300

    def test_difficulty_score_calculation(self, parser, data_dir):
        """测试难度评分计算"""
        gpx_file = data_dir / "difficulty_test.gpx"
        gpx_content = self._create_gpx_with_elevation_profile(
            [100, 110, 120, 130, 140, 150] * 20  # 长距离
        )
        gpx_file.write_text(gpx_content, encoding='utf-8')

        result = parser.parse_file(gpx_file)

        assert 0 <= result.difficulty_score <= 100
        assert result.difficulty_level in ["简单", "中等", "困难", "极难"]

    def test_duration_estimation(self, parser, data_dir):
        """测试用时估算"""
        gpx_file = data_dir / "duration_test.gpx"
        gpx_content = self._create_gpx_with_elevation_profile(
            [100, 105, 110, 115] * 10
        )
        gpx_file.write_text(gpx_content, encoding='utf-8')

        result = parser.parse_file(gpx_file)

        assert result.estimated_duration_hours > 0
        # 用时应与距离相关
        assert result.estimated_duration_hours < result.total_distance_km * 2

    def test_safety_risk_assessment(self, parser, data_dir):
        """测试安全风险评估"""
        # 低风险轨迹
        gpx_file = data_dir / "low_risk.gpx"
        gpx_content = self._create_gpx_with_elevation_profile(
            [100, 105, 110, 115, 120]  # 平缓
        )
        gpx_file.write_text(gpx_content, encoding='utf-8')

        result = parser.parse_file(gpx_file)

        assert result.safety_risk in ["低风险", "中等风险", "高风险", "极高风险"]

    def test_haversine_distance(self, parser):
        """测试距离计算（Haversine 公式）"""
        # 北京天安门到故宫的实际距离约 1.6km
        distance1 = parser._haversine_distance(
            39.9042, 116.4074,  # 天安门
            39.9163, 116.3972   # 故宫
        )
        assert 1500 < distance1 < 1700  # 约 1.6km

        # 同一点距离应为 0
        distance2 = parser._haversine_distance(39.9042, 116.4074, 39.9042, 116.4074)
        assert distance2 < 0.01

    def test_terrain_change_gradient_calculation(self, parser, data_dir):
        """测试坡度计算"""
        gpx_file = data_dir / "gradient_test.gpx"
        gpx_content = self._create_gpx_with_elevation_profile(
            [100, 150, 200, 250, 300]  # 持续爬升
        )
        gpx_file.write_text(gpx_content, encoding='utf-8')

        result = parser.parse_file(gpx_file)

        # 检查地形变化段的坡度计算
        for terrain in result.terrain_analysis:
            # 坡度百分比 = (海拔差 / 水平距离) * 100
            expected_gradient = (terrain.elevation_diff / terrain.distance_m) * 100
            assert abs(terrain.gradient_percent - expected_gradient) < 0.01

    def test_track_point_properties(self, parser, data_dir):
        """测试轨迹点属性"""
        gpx_file = data_dir / "properties_test.gpx"
        gpx_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <trkseg>
      <trkpt lat="39.9042" lon="116.4074">
        <ele>100</ele>
        <time>2024-03-15T08:00:00Z</time>
      </trkpt>
      <trkpt lat="39.9052" lon="116.4084">
        <ele>120</ele>
        <time>2024-03-15T08:10:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>""", encoding='utf-8')

        result = parser.parse_file(gpx_file)

        # 检查起点和终点
        assert isinstance(result.start_point, Point3D)
        assert isinstance(result.end_point, Point3D)
        assert result.start_point.lat == 39.9042
        assert result.end_point.lat == 39.9052

        # 检查极值点
        assert isinstance(result.max_elev_point, Point3D)
        assert isinstance(result.min_elev_point, Point3D)
        assert result.max_elev_point.elevation == 120
        assert result.min_elev_point.elevation == 100

    def _create_gpx_with_elevation_profile(self, elevations: list) -> str:
        """辅助方法：创建指定海拔轮廓的 GPX 文件"""
        points_xml = ""
        base_lat = 39.9042
        base_lon = 116.4074

        for i, elev in enumerate(elevations):
            lat = base_lat + i * 0.001
            lon = base_lon + i * 0.001
            time = f"2024-03-15T{8 + i // 6:02d}:{i % 6 * 10:02d}:00Z"
            points_xml += f"""      <trkpt lat="{lat:.4f}" lon="{lon:.4f}">
        <ele>{elev}</ele>
        <time>{time}</time>
      </trkpt>
"""

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <trkseg>
{points_xml}
    </trkseg>
  </trk>
</gpx>"""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
