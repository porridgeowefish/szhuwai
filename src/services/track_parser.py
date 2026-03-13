"""
轨迹解析服务
============

支持 GPX 和 KML 格式的轨迹文件解析，将轨迹数据转换为 TrackAnalysisResult 模型。

职责：
- 解析 GPX/KML 文件提取轨迹点
- 对轨迹点进行平滑处理（去除噪点）
- 计算距离、爬升、下降等统计信息
- 识别大爬升/大下降路段
- 生成难度和安全评估
"""

from pathlib import Path
from typing import List, Literal, Optional, Union

from loguru import logger

from src.schemas.base import Point3D
from src.schemas.track import TrackAnalysisResult, TerrainChange


class TrackParseError(Exception):
    """轨迹解析错误"""
    pass


class TrackParser:
    """轨迹文件解析器"""

    # 业务规则常量
    LARGE_ASCENT_THRESHOLD = 200  # 大爬升阈值（米）
    LARGE_DESCENT_THRESHOLD = 300  # 大下降阈值（米）
    ASCENT_INTERRUPTION_THRESHOLD = 50  # 爬升中断阈值（米）
    DESCENT_INTERRUPTION_THRESHOLD = 20  # 下降中断阈值（米）

    # 平滑算法常量
    SMOOTHING_WINDOW_SIZE = 5  # 滑动平均窗口大小（推荐3-5）
    ELEVATION_OUTLIER_THRESHOLD = 50  # 海拔异常值阈值（米）
    SMOOTHING_MIN_POINTS = 50  # 最少点数阈值，低于此值不进行平滑（避免影响少量测试点）

    def __init__(self) -> None:
        """初始化解析器"""
        self._gpx_parser = None
        self._kml_parser = None

    def _smooth_elevation(self, points: List[Point3D]) -> List[Point3D]:
        """
        对轨迹点海拔进行滑动平均滤波，去除噪点

        使用窗口大小为 5 的滑动平均，平滑每个点的海拔值。
        只有当数据点数量超过阈值时才进行平滑处理。

        Args:
            points: 原始轨迹点列表

        Returns:
            List[Point3D]: 平滑后的轨迹点列表
        """
        # 只有当数据点数量足够多时才进行平滑处理
        if len(points) < self.SMOOTHING_MIN_POINTS:
            return points[:]

        window_size = min(self.SMOOTHING_WINDOW_SIZE, len(points))
        half_window = window_size // 2

        smoothed_points = []

        for i, point in enumerate(points):
            # 计算窗口内海拔平均值
            window_start = max(0, i - half_window)
            window_end = min(len(points), i + half_window + 1)
            window_points = points[window_start:window_end]

            # 计算平均海拔
            avg_elevation = sum(p.elevation for p in window_points) / len(window_points)

            # 检测并过滤异常值（与平均值差异过大的点）
            if abs(point.elevation - avg_elevation) > self.ELEVATION_OUTLIER_THRESHOLD:
                # 使用窗口平均值替换异常值
                smoothed_points.append(Point3D(
                    lat=point.lat,
                    lon=point.lon,
                    elevation=avg_elevation,
                    timestamp=point.timestamp
                ))
            else:
                smoothed_points.append(point)

        return smoothed_points

    def parse_file(
        self,
        file_path: Union[str, Path],
        track_name: Optional[str] = None
    ) -> TrackAnalysisResult:
        """
        解析轨迹文件

        Args:
            file_path: 轨迹文件路径（.gpx 或 .kml）
            track_name: 轨迹名称（可选，默认从文件名获取）

        Returns:
            TrackAnalysisResult: 轨迹分析结果

        Raises:
            TrackParseError: 解析失败时抛出
            FileNotFoundError: 文件不存在时抛出
        """
        file_path = Path(file_path)

        # 文件存在性检查
        if not file_path.exists():
            raise FileNotFoundError(f"轨迹文件不存在: {file_path}")

        # 确定文件类型
        file_ext = file_path.suffix.lower()
        if file_ext not in {'.gpx', '.kml'}:
            raise TrackParseError(f"不支持的文件格式: {file_ext}")

        # 设置轨迹名称
        if track_name is None:
            track_name = file_path.stem

        # 根据文件类型解析
        try:
            if file_ext == '.gpx':
                return self._parse_gpx(file_path, track_name)
            else:
                return self._parse_kml(file_path, track_name)
        except ImportError as e:
            logger.error(f"解析库未安装: {e}")
            raise TrackParseError("请安装 gpxpy: pip install gpxpy") from e
        except Exception as e:
            logger.error(f"解析文件 {file_path} 失败: {e}")
            raise TrackParseError(f"解析失败: {e}") from e

    def _parse_gpx(
        self,
        file_path: Path,
        track_name: str
    ) -> TrackAnalysisResult:
        """
        解析 GPX 文件

        Args:
            file_path: GPX 文件路径
            track_name: 轨迹名称

        Returns:
            TrackAnalysisResult: 轨迹分析结果
        """
        try:
            import gpxpy
        except ImportError as e:
            raise ImportError("gpxpy 库未安装") from e

        with open(file_path, 'r', encoding='utf-8') as f:
            gpx_content = gpxpy.parse(f)

        # 提取所有轨迹点
        points: List[Point3D] = []
        for track in gpx_content.tracks:
            for segment in track.segments:
                for point in segment.points:
                    points.append(Point3D(
                        lat=point.latitude,
                        lon=point.longitude,
                        elevation=point.elevation if point.elevation is not None else 0,
                        timestamp=point.time
                    ))

        if not points:
            raise TrackParseError("GPX 文件中未找到轨迹点")

        logger.info(f"从 {file_path} 解析到 {len(points)} 个轨迹点")

        # 对轨迹点进行平滑处理（去除海拔噪点）
        smoothed_points = self._smooth_elevation(points)
        logger.info("海拔平滑处理完成")

        return self._analyze_points(smoothed_points, track_name)

    def _parse_kml(
        self,
        file_path: Path,
        track_name: str
    ) -> TrackAnalysisResult:
        """
        解析 KML 文件

        Args:
            file_path: KML 文件路径
            track_name: 轨迹名称

        Returns:
            TrackAnalysisResult: 轨迹分析结果
        """
        import xml.etree.ElementTree as ET

        # 使用字节模式读取，避免编码问题
        with open(file_path, 'rb') as f:
            kml_content = f.read()

        # 解析 XML
        tree = ET.fromstring(kml_content)

        # KML namespace
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}

        # 提取所有轨迹点
        points: List[Point3D] = []

        # 查找所有 coordinates 元素
        for coord_text in tree.findall('.//kml:coordinates', ns):
            if coord_text.text:
                # 解析坐标字符串
                for coord_pair in coord_text.text.strip().split():
                    parts = coord_pair.split(',')
                    if len(parts) >= 2:
                        try:
                            lon = float(parts[0])
                            lat = float(parts[1])
                            elev = float(parts[2]) if len(parts) > 2 else 0
                            points.append(Point3D(
                                lat=lat,
                                lon=lon,
                                elevation=elev,
                                timestamp=None
                            ))
                        except (ValueError, IndexError):
                            continue

        if not points:
            raise TrackParseError("KML 文件中未找到轨迹点")

        logger.info(f"从 {file_path} 解析到 {len(points)} 个轨迹点")

        # 对轨迹点进行平滑处理（去除海拔噪点）
        smoothed_points = self._smooth_elevation(points)
        logger.info("海拔平滑处理完成")

        return self._analyze_points(smoothed_points, track_name)

    def _analyze_points(
        self,
        points: List[Point3D],
        track_name: str
    ) -> TrackAnalysisResult:
        """
        分析轨迹点，生成分析结果

        Args:
            points: 轨迹点列表
            track_name: 轨迹名称

        Returns:
            TrackAnalysisResult: 轨迹分析结果
        """
        if len(points) < 2:
            raise TrackParseError("轨迹点数量不足（至少需要2个点）")

        # 统计数据初始化
        total_distance_m = 0.0
        total_ascent_m = 0.0
        total_descent_m = 0.0

        # 初始化极值（包括第一个点）
        max_elevation = points[0].elevation
        min_elevation = points[0].elevation
        max_elev_point = points[0]
        min_elev_point = points[0]

        # 地形变化段识别
        terrain_changes: List[TerrainChange] = []

        # 当前爬升/下降段状态
        current_ascent_start: Optional[Point3D] = None
        current_descent_start: Optional[Point3D] = None
        current_ascent_peak_elevation = -float('inf')
        current_descent_valley_elevation = float('inf')

        # 计算每一段的统计信息
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            # 计算水平距离（Haversine 公式的简化版）
            distance = self._haversine_distance(p1.lat, p1.lon, p2.lat, p2.lon)
            total_distance_m += distance

            # 计算海拔差
            elev_diff = p2.elevation - p1.elevation

            # 更新累计爬升/下降
            if elev_diff > 0:
                total_ascent_m += elev_diff
            else:
                total_descent_m += abs(elev_diff)

            # 更新极值点
            if p2.elevation > max_elevation:
                max_elevation = p2.elevation
                max_elev_point = p2
            if p2.elevation < min_elevation:
                min_elevation = p2.elevation
                min_elev_point = p2

            # 地形变化段识别（大爬升）
            if elev_diff > 0:
                if current_ascent_start is None:
                    current_ascent_start = p1
                    current_ascent_peak_elevation = p1.elevation

                current_ascent_peak_elevation = max(current_ascent_peak_elevation, p2.elevation)

                # 检查是否结束当前下降段
                if current_descent_start is not None:
                    descent_diff = current_descent_valley_elevation - current_ascent_start.elevation
                    if abs(descent_diff) >= self.LARGE_DESCENT_THRESHOLD:
                        # 结束下降段
                        descent_distance = self._haversine_distance(
                            current_descent_start.lat, current_descent_start.lon,
                            p2.lat, p2.lon
                        )
                        if descent_distance > 0:
                            gradient = (abs(descent_diff) / descent_distance) * 100
                            terrain_changes.append(TerrainChange(
                                change_type="大下降",
                                start_point=current_descent_start,
                                end_point=Point3D(
                                    lat=p2.lat, lon=p2.lon,
                                    elevation=current_descent_valley_elevation,
                                    timestamp=None
                                ),
                                elevation_diff=abs(descent_diff),
                                distance_m=descent_distance,
                                gradient_percent=gradient
                            ))
                    current_descent_start = None
                    current_descent_valley_elevation = float('inf')

            # 地形变化段识别（大下降）
            elif elev_diff < 0:
                if current_descent_start is None:
                    current_descent_start = p1
                    current_descent_valley_elevation = p1.elevation

                current_descent_valley_elevation = min(current_descent_valley_elevation, p2.elevation)

                # 检查是否结束当前爬升段
                if current_ascent_start is not None:
                    ascent_diff = current_ascent_peak_elevation - current_ascent_start.elevation
                    # 检查中断是否小于阈值
                    interruption = abs(p2.elevation - current_ascent_peak_elevation)
                    if ascent_diff >= self.LARGE_ASCENT_THRESHOLD and interruption < self.ASCENT_INTERRUPTION_THRESHOLD:
                        ascent_distance = self._haversine_distance(
                            current_ascent_start.lat, current_ascent_start.lon,
                            p2.lat, p2.lon
                        )
                        if ascent_distance > 0:
                            gradient = (ascent_diff / ascent_distance) * 100
                            terrain_changes.append(TerrainChange(
                                change_type="大爬升",
                                start_point=current_ascent_start,
                                end_point=Point3D(
                                    lat=p2.lat, lon=p2.lon,
                                    elevation=current_ascent_peak_elevation,
                                    timestamp=None
                                ),
                                elevation_diff=ascent_diff,
                                distance_m=ascent_distance,
                                gradient_percent=gradient
                            ))
                    current_ascent_start = None
                    current_ascent_peak_elevation = -float('inf')

        # 处理最后一个未结束的段
        if current_ascent_start is not None:
            ascent_diff = current_ascent_peak_elevation - current_ascent_start.elevation
            if ascent_diff >= self.LARGE_ASCENT_THRESHOLD:
                ascent_distance = self._haversine_distance(
                    current_ascent_start.lat, current_ascent_start.lon,
                    points[-1].lat, points[-1].lon
                )
                if ascent_distance > 0:
                    gradient = (ascent_diff / ascent_distance) * 100
                    terrain_changes.append(TerrainChange(
                        change_type="大爬升",
                        start_point=current_ascent_start,
                        end_point=Point3D(
                            lat=points[-1].lat, lon=points[-1].lon,
                            elevation=current_ascent_peak_elevation,
                            timestamp=None
                        ),
                        elevation_diff=ascent_diff,
                        distance_m=ascent_distance,
                        gradient_percent=gradient
                    ))

        if current_descent_start is not None:
            descent_diff = current_descent_valley_elevation - current_descent_start.elevation
            if abs(descent_diff) >= self.LARGE_DESCENT_THRESHOLD:
                descent_distance = self._haversine_distance(
                    current_descent_start.lat, current_descent_start.lon,
                    points[-1].lat, points[-1].lon
                )
                if descent_distance > 0:
                    gradient = (abs(descent_diff) / descent_distance) * 100
                    terrain_changes.append(TerrainChange(
                        change_type="大下降",
                        start_point=current_descent_start,
                        end_point=Point3D(
                            lat=points[-1].lat, lon=points[-1].lon,
                            elevation=current_descent_valley_elevation,
                            timestamp=None
                        ),
                        elevation_diff=abs(descent_diff),
                        distance_m=descent_distance,
                        gradient_percent=gradient
                    ))

        # 计算平均海拔
        avg_elevation = sum(p.elevation for p in points) / len(points)

        # 计算难度评分
        difficulty_score = self._calculate_difficulty_score(
            total_distance_m / 1000,
            total_ascent_m,
            total_descent_m,
            terrain_changes
        )

        # 确定难度等级
        if difficulty_score <= 25:
            difficulty_level: Literal["简单", "中等", "困难", "极难"] = "简单"
        elif difficulty_score <= 50:
            difficulty_level = "中等"
        elif difficulty_score <= 75:
            difficulty_level = "困难"
        else:
            difficulty_level = "极难"

        # 确定安全风险等级
        intense_segments = len(terrain_changes)
        if intense_segments == 0:
            safety_risk: Literal["低风险", "中等风险", "高风险", "极高风险"] = "低风险"
        elif intense_segments <= 2:
            safety_risk = "中等风险"
        elif intense_segments <= 5:
            safety_risk = "高风险"
        else:
            safety_risk = "极高风险"

        # 计算预计用时
        estimated_duration = self._estimate_duration(
            total_distance_m / 1000,
            total_ascent_m
        )

        # 构建分析结果
        return TrackAnalysisResult(
            total_distance_km=total_distance_m / 1000,
            total_ascent_m=total_ascent_m,
            total_descent_m=total_descent_m,
            max_elevation_m=max_elevation,
            min_elevation_m=min_elevation,
            avg_elevation_m=avg_elevation,
            start_point=points[0],
            end_point=points[-1],
            max_elev_point=max_elev_point,
            min_elev_point=min_elev_point,
            terrain_analysis=terrain_changes,
            difficulty_score=difficulty_score,
            difficulty_level=difficulty_level,
            estimated_duration_hours=estimated_duration,
            safety_risk=safety_risk,
            track_name=track_name,
            track_points_count=len(points)
        )

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        计算两点间的水平距离（Haversine 公式）

        Args:
            lat1, lon1: 第一个点的经纬度
            lat2, lon2: 第二个点的经纬度

        Returns:
            float: 距离（米）
        """
        from math import radians, sin, cos, sqrt, asin

        R = 6371000  # 地球半径（米）

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = (sin(delta_lat / 2) ** 2 +
             cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2)
        c = 2 * asin(sqrt(a))

        return R * c

    def _calculate_difficulty_score(
        self,
        distance_km: float,
        ascent_m: float,
        descent_m: float,
        terrain_changes: List[TerrainChange]
    ) -> float:
        """
        计算难度评分

        Args:
            distance_km: 总距离（公里）
            ascent_m: 累计爬升（米）
            descent_m: 累计下降（米）
            terrain_changes: 地形变化段

        Returns:
            float: 难度评分（0-100）
        """
        # 基础分数：距离和海拔变化
        distance_score = min(distance_km * 2, 40)  # 最多40分
        elevation_score = min((ascent_m + descent_m) / 10, 30)  # 最多30分

        # 地形复杂度分数
        terrain_score = min(len(terrain_changes) * 5, 30)  # 最多30分

        total = distance_score + elevation_score + terrain_score
        return min(total, 100)

    def _estimate_duration(
        self,
        distance_km: float,
        ascent_m: float
    ) -> float:
        """
        估算用时（基于 Naismith 规则）

        规则：
        - 平地：1km 用 15 分钟
        - 爬升：每 100m 用 10 分钟
        - 下降：每 100m 用 5 分钟

        Args:
            distance_km: 总距离（公里）
            ascent_m: 累计爬升（米）

        Returns:
            float: 预计用时（小时）
        """
        base_time = distance_km * 0.25  # 平地时间（小时）
        ascent_time = ascent_m / 1000  # 爬升时间（小时）
        total_time = base_time + ascent_time

        # 根据难度调整（更难的路线用时更长）
        return total_time * 1.1


__all__ = ["TrackParser", "TrackParseError"]
