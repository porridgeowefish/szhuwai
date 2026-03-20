"""
轨迹服务
========

封装轨迹解析和坐标纠偏逻辑。
"""

from pathlib import Path
from typing import Dict, Optional

from loguru import logger

from src.schemas.base import Point3D
from src.schemas.track import TrackAnalysisResult
from src.services.track_parser import TrackParser
from src.services.geo_coord_utils import wgs84_to_gcj02


class TrackService:
    """轨迹解析服务"""

    def __init__(self):
        """初始化服务"""
        self.parser = TrackParser()
        self.key_points: Dict[str, Point3D] = {}

    def analyze(self, file_path: str) -> TrackAnalysisResult:
        """
        解析轨迹文件

        Args:
            file_path: GPX/KML 轨迹文件路径

        Returns:
            TrackAnalysisResult: 轨迹分析结果

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件解析失败
        """
        if not file_path or not Path(file_path).exists():
            raise FileNotFoundError(f"轨迹文件不存在: {file_path}")

        try:
            logger.info(f"开始解析轨迹文件: {file_path}")
            track_analysis = self.parser.parse_file(file_path)
            logger.info(
                f"轨迹解析完成: 总距离 {track_analysis.total_distance_km:.2f}km, "
                f"爬升 {track_analysis.total_ascent_m}m, 下降 {track_analysis.total_descent_m}m"
            )
            return track_analysis
        except Exception as e:
            logger.error(f"轨迹解析失败: {e}")
            raise ValueError(f"轨迹文件解析失败: {str(e)}")

    def correct_coordinates(self, track_analysis: TrackAnalysisResult) -> Dict[str, Point3D]:
        """
        坐标纠偏（WGS84 -> GCJ02）

        Args:
            track_analysis: 轨迹分析结果

        Returns:
            Dict[str, Point3D]: 纠偏后的关键点坐标
        """
        logger.info("开始坐标纠偏（WGS84 -> GCJ02）")

        # 处理关键点
        if track_analysis and track_analysis.start_point:
            corrected_lon, corrected_lat = wgs84_to_gcj02(
                track_analysis.start_point.lon, track_analysis.start_point.lat
            )
            self.key_points['start'] = Point3D(
                lon=corrected_lon,
                lat=corrected_lat,
                elevation=track_analysis.start_point.elevation
            )

        if track_analysis and track_analysis.end_point:
            corrected_lon, corrected_lat = wgs84_to_gcj02(
                track_analysis.end_point.lon, track_analysis.end_point.lat
            )
            self.key_points['end'] = Point3D(
                lon=corrected_lon,
                lat=corrected_lat,
                elevation=track_analysis.end_point.elevation
            )

        # 纠偏最高点坐标
        if track_analysis and track_analysis.max_elev_point:
            corrected_lon, corrected_lat = wgs84_to_gcj02(
                track_analysis.max_elev_point.lon, track_analysis.max_elev_point.lat
            )
            self.key_points['highest'] = Point3D(
                lon=corrected_lon,
                lat=corrected_lat,
                elevation=track_analysis.max_elev_point.elevation
            )

        logger.info("坐标纠偏完成")
        return self.key_points

    def get_gcj02_start_coord(self, track_analysis: TrackAnalysisResult) -> str:
        """
        获取纠偏后的起点坐标字符串

        Args:
            track_analysis: 轨迹分析结果

        Returns:
            str: "lon,lat" 格式的坐标字符串
        """
        if 'start' in self.key_points:
            return f"{self.key_points['start'].lon},{self.key_points['start'].lat}"
        elif track_analysis and track_analysis.start_point:
            return f"{track_analysis.start_point.lon},{track_analysis.start_point.lat}"
        raise ValueError("无法获取起点坐标")
