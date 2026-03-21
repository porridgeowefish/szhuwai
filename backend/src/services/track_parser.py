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
from src.schemas.track import TrackAnalysisResult, TerrainChange, ElevationPoint, TrackPointGCJ02
from src.services.geo_coord_utils import wgs84_to_gcj02


class TrackParseError(Exception):
    """轨迹解析错误"""
    pass


class TrackParser:
    """轨迹文件解析器"""

    # 业务规则常量 - 大爬升/大下降识别
    # 大爬升：单次连续爬升超过300m，中间允许25m以内下降
    # 大下降：单次连续下降超过300m，中间允许25m以内上升
    LARGE_ASCENT_THRESHOLD = 300  # 大爬升阈值：上升 >= 300m
    LARGE_ASCENT_DESCENT_TOLERANCE = 50  # 大爬升时允许的最大下降： < 50m
    LARGE_DESCENT_THRESHOLD = 300  # 大下降阈值：下降 >= 300m
    LARGE_DESCENT_ASCENT_TOLERANCE = 50  # 大下降时允许的最大上升：< 50m

    # 中断条件
    GRADIENT_CHECK_DISTANCE_M = 1000  # 坡度检查距离：1km
    MIN_GRADIENT_THRESHOLD_M = 40  # 最小海拔变化阈值：40m（1km内变化不超过此值则中断）

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
            logger.error(f"Parser library not installed: {e}")
            raise TrackParseError("请安装 gpxpy: pip install gpxpy") from e
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
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

        logger.info(f"Parsed {len(points)} track points from {file_path}")

        # 对轨迹点进行平滑处理（去除海拔噪点）
        smoothed_points = self._smooth_elevation(points)
        logger.info("Elevation smoothing completed")

        return self._analyze_points(smoothed_points, track_name)

    def _parse_kml(
        self,
        file_path: Path,
        track_name: str
    ) -> TrackAnalysisResult:
        """
        解析 KML 文件（支持标准格式和 Google Earth 扩展格式）

        支持两种格式：
        1. 标准 KML: <LineString><coordinates>lon,lat,elev</coordinates></LineString>
        2. Google Earth 扩展: <gx:Track><gx:coord>lon lat elev</gx:coord></gx:Track>

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

        # KML namespace（包含 gx 扩展）
        ns = {
            'kml': 'http://www.opengis.net/kml/2.2',
            'gx': 'http://www.google.com/kml/ext/2.2'
        }

        # 提取所有轨迹点
        points: List[Point3D] = []

        # 1. 优先尝试解析 gx:coord 格式（Google Earth 扩展格式）
        for coord_elem in tree.findall('.//gx:coord', ns):
            if coord_elem.text:
                # gx:coord 格式：空格分隔的 "lon lat elev"
                parts = coord_elem.text.strip().split()
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

        # 2. 如果没有找到 gx:coord，尝试标准 coordinates 格式
        if not points:
            for coord_text in tree.findall('.//kml:coordinates', ns):
                if coord_text.text:
                    # coordinates 格式：逗号分隔的 "lon,lat,elev"，多个点用空格分隔
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

        logger.info(f"Parsed {len(points)} track points from {file_path}")

        # 对轨迹点进行平滑处理（去除海拔噪点）
        smoothed_points = self._smooth_elevation(points)
        logger.info("Elevation smoothing completed")

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

        # 大爬升/大下降段状态跟踪
        # ascent_start: 大爬升起点
        # ascent_peak: 大爬升过程中的最高点
        # ascent_distance: 累计距离
        ascent_start: Optional[Point3D] = None
        ascent_peak: Optional[Point3D] = None
        ascent_distance_m = 0.0
        ascent_last_check_idx = 0  # 上次坡度检查的点索引

        # descent_start: 大下降起点
        # descent_valley: 大下降过程中的最低点
        # descent_distance: 累计距离
        descent_start: Optional[Point3D] = None
        descent_valley: Optional[Point3D] = None
        descent_distance_m = 0.0
        descent_last_check_idx = 0  # 上次坡度检查的点索引

        # 累计距离（用于坡度检查）
        segment_distance_m = 0.0

        # 计算每一段的统计信息
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            # 计算水平距离（Haversine 公式）
            distance = self._haversine_distance(p1.lat, p1.lon, p2.lat, p2.lon)
            total_distance_m += distance
            segment_distance_m += distance

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

            # ========== 大爬升识别逻辑 ==========
            # 规则：上升 >= 300m，下降 < 25m，算作连续大爬升
            if elev_diff >= 0:
                # 上升或平地
                if ascent_start is None:
                    # 开始新的爬升段
                    ascent_start = p1
                    ascent_peak = p2
                    ascent_distance_m = distance
                    ascent_last_check_idx = i
                else:
                    # 继续爬升段
                    ascent_distance_m += distance
                    if p2.elevation > ascent_peak.elevation:
                        ascent_peak = p2

                # 检查是否需要中断当前下降段
                if descent_start is not None:
                    # 计算从下降起点到当前点的上升量
                    ascent_since_descent_start = p2.elevation - descent_valley.elevation if descent_valley else 0
                    if ascent_since_descent_start >= self.LARGE_DESCENT_ASCENT_TOLERANCE:
                        # 上升超过阈值，中断下降段
                        # 先检查是否满足大下降条件
                        total_descent = descent_start.elevation - descent_valley.elevation
                        if total_descent > self.LARGE_DESCENT_THRESHOLD:
                            terrain_changes.append(TerrainChange(
                                change_type="large_descent",
                                start_point=descent_start,
                                end_point=descent_valley,
                                elevation_diff=total_descent,
                                distance_m=descent_distance_m,
                                gradient_percent=(total_descent / descent_distance_m * 100) if descent_distance_m > 0 else 0
                            ))
                        # 重置下降段
                        descent_start = None
                        descent_valley = None
                        descent_distance_m = 0.0

            else:
                # 下降
                if ascent_start is not None:
                    # 计算当前累计下降量（从峰值到当前点）
                    descent_from_peak = ascent_peak.elevation - p2.elevation

                    if descent_from_peak >= self.LARGE_ASCENT_DESCENT_TOLERANCE:
                        # 下降超过阈值，检查是否满足大爬升条件
                        total_ascent = ascent_peak.elevation - ascent_start.elevation
                        logger.info(f"[Ascent] Descent exceeds tolerance({self.LARGE_ASCENT_DESCENT_TOLERANCE}m), current ascent={total_ascent}m, threshold={self.LARGE_ASCENT_THRESHOLD}m")
                        if total_ascent >= self.LARGE_ASCENT_THRESHOLD:
                            logger.info(f"[Ascent] Large ascent detected! ascent={total_ascent}m, distance={ascent_distance_m}m")
                            terrain_changes.append(TerrainChange(
                                change_type="large_ascent",
                                start_point=ascent_start,
                                end_point=ascent_peak,
                                elevation_diff=total_ascent,
                                distance_m=ascent_distance_m,
                                gradient_percent=(total_ascent / ascent_distance_m * 100) if ascent_distance_m > 0 else 0
                            ))
                        # 重置爬升段
                        ascent_start = None
                        ascent_peak = None
                        ascent_distance_m = 0.0

                        # 开始新的下降段
                        descent_start = p1
                        descent_valley = p2
                        descent_distance_m = distance
                        descent_last_check_idx = i
                    else:
                        # 下降未超过阈值，继续爬升段（累计下降量）
                        ascent_distance_m += distance

                # 处理下降段
                if descent_start is None:
                    descent_start = p1
                    descent_valley = p2
                    descent_distance_m = distance
                    descent_last_check_idx = i
                else:
                    descent_distance_m += distance
                    if p2.elevation < descent_valley.elevation:
                        descent_valley = p2

            # ========== 坡度检查（1km 内变化不超过 40m 则中断） ==========
            # 检查爬升段
            if ascent_start is not None and ascent_distance_m >= self.GRADIENT_CHECK_DISTANCE_M:
                # 找到 1km 前的点
                check_distance = 0.0
                check_idx = ascent_last_check_idx + 1  # 默认使用最远可检查点
                for j in range(i, ascent_last_check_idx, -1):
                    if j > 0:
                        seg_dist = self._haversine_distance(
                            points[j-1].lat, points[j-1].lon,
                            points[j].lat, points[j].lon
                        )
                        check_distance += seg_dist
                        if check_distance >= self.GRADIENT_CHECK_DISTANCE_M:
                            check_idx = j
                            break

                # 计算这 1km 内的海拔变化（允许一定误差，使用实际找到的最远点）
                elev_change = abs(points[i+1].elevation - points[check_idx].elevation)
                if elev_change < self.MIN_GRADIENT_THRESHOLD_M:
                    # 坡度太缓，中断当前爬升段
                    total_ascent = ascent_peak.elevation - ascent_start.elevation
                    logger.info(f"[Gradient] Ascent segment interrupted: elev_change={elev_change:.0f}m < {self.MIN_GRADIENT_THRESHOLD_M}m in 1km, current_ascent={total_ascent:.0f}m")
                    if total_ascent >= self.LARGE_ASCENT_THRESHOLD:
                        terrain_changes.append(TerrainChange(
                            change_type="大爬升",
                            start_point=ascent_start,
                            end_point=ascent_peak,
                            elevation_diff=total_ascent,
                            distance_m=ascent_distance_m,
                            gradient_percent=(total_ascent / ascent_distance_m * 100) if ascent_distance_m > 0 else 0
                        ))
                    # 从中断点重新开始
                    ascent_start = points[check_idx]
                    ascent_peak = points[i+1]
                    ascent_distance_m = self._haversine_distance(
                        points[check_idx].lat, points[check_idx].lon,
                        points[i+1].lat, points[i+1].lon
                    )
                    ascent_last_check_idx = i

            # 检查下降段
            if descent_start is not None and descent_distance_m >= self.GRADIENT_CHECK_DISTANCE_M:
                # 找到 1km 前的点
                check_distance = 0.0
                check_idx = descent_last_check_idx + 1  # 默认使用最远可检查点
                for j in range(i, descent_last_check_idx, -1):
                    if j > 0:
                        seg_dist = self._haversine_distance(
                            points[j-1].lat, points[j-1].lon,
                            points[j].lat, points[j].lon
                        )
                        check_distance += seg_dist
                        if check_distance >= self.GRADIENT_CHECK_DISTANCE_M:
                            check_idx = j
                            break

                # 计算这 1km 内的海拔变化
                elev_change = abs(points[i+1].elevation - points[check_idx].elevation)
                if elev_change < self.MIN_GRADIENT_THRESHOLD_M:
                    # 坡度太缓，中断当前下降段
                    total_descent = descent_start.elevation - descent_valley.elevation
                    logger.info(f"[Gradient] Descent segment interrupted: elev_change={elev_change:.0f}m < {self.MIN_GRADIENT_THRESHOLD_M}m in 1km, current_descent={total_descent:.0f}m")
                    if total_descent > self.LARGE_DESCENT_THRESHOLD:
                        terrain_changes.append(TerrainChange(
                            change_type="large_descent",
                            start_point=descent_start,
                            end_point=descent_valley,
                            elevation_diff=total_descent,
                            distance_m=descent_distance_m,
                            gradient_percent=(total_descent / descent_distance_m * 100) if descent_distance_m > 0 else 0
                        ))
                    # 从中断点重新开始
                    descent_start = points[check_idx]
                    descent_valley = points[i+1]
                    descent_distance_m = self._haversine_distance(
                        points[check_idx].lat, points[check_idx].lon,
                        points[i+1].lat, points[i+1].lon
                    )
                    descent_last_check_idx = i

        # ========== 处理最后一个未结束的段 ==========
        logger.info(f"[Ascent] Track ended, pending ascent segment: start={ascent_start.elevation if ascent_start else None}m, peak={ascent_peak.elevation if ascent_peak else None}m")
        if ascent_start is not None and ascent_peak is not None:
            total_ascent = ascent_peak.elevation - ascent_start.elevation
            logger.info(f"[Ascent] Final ascent segment: ascent={total_ascent}m, distance={ascent_distance_m}m, threshold={self.LARGE_ASCENT_THRESHOLD}m")
            if total_ascent >= self.LARGE_ASCENT_THRESHOLD:
                terrain_changes.append(TerrainChange(
                    change_type="large_ascent",
                    start_point=ascent_start,
                    end_point=ascent_peak,
                    elevation_diff=total_ascent,
                    distance_m=ascent_distance_m,
                    gradient_percent=(total_ascent / ascent_distance_m * 100) if ascent_distance_m > 0 else 0
                ))

        if descent_start is not None and descent_valley is not None:
            total_descent = descent_start.elevation - descent_valley.elevation
            if total_descent > self.LARGE_DESCENT_THRESHOLD:
                terrain_changes.append(TerrainChange(
                    change_type="large_descent",
                    start_point=descent_start,
                    end_point=descent_valley,
                    elevation_diff=total_descent,
                    distance_m=descent_distance_m,
                    gradient_percent=(total_descent / descent_distance_m * 100) if descent_distance_m > 0 else 0
                ))

        # 计算平均海拔
        avg_elevation = sum(p.elevation for p in points) / len(points)

        # ========== 生成海拔轨迹点（用于前端可视化）==========
        elevation_points = self._generate_elevation_points(
            points, total_distance_m, max_elev_point, min_elev_point
        )

        # ========== 生成GCJ02轨迹点（用于高德地图平面图）==========
        track_points_gcj02 = self._generate_track_points_gcj02(
            points, max_elev_point, min_elev_point, terrain_changes
        )

        # ========== 为地形变化段添加起点距离 ==========
        # 计算每个点的累计距离
        cumulative_distances = [0.0]
        for i in range(len(points) - 1):
            dist = self._haversine_distance(
                points[i].lat, points[i].lon,
                points[i+1].lat, points[i+1].lon
            )
            cumulative_distances.append(cumulative_distances[-1] + dist)

        # 为每个地形变化段添加起点距离
        for tc in terrain_changes:
            # 找到起点在points中的索引
            found = False
            for idx, p in enumerate(points):
                if (abs(p.lat - tc.start_point.lat) < 1e-5 and
                    abs(p.lon - tc.start_point.lon) < 1e-5):
                    tc.start_distance_m = cumulative_distances[idx]
                    found = True
                    logger.info(f"[Terrain] {tc.change_type}: start_distance={cumulative_distances[idx]:.1f}m, ascent={tc.elevation_diff}m")
                    break
            if not found:
                logger.warning(f"[Terrain] {tc.change_type} cannot match start point: start_point=({tc.start_point.lat}, {tc.start_point.lon})")

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
            elevation_points=elevation_points,
            track_points_gcj02=track_points_gcj02,
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

    def _generate_elevation_points(
        self,
        points: List[Point3D],
        total_distance_m: float,
        max_elev_point: Point3D,
        min_elev_point: Point3D,
        num_samples: int = 100
    ) -> List[ElevationPoint]:
        """
        从轨迹点中抽样生成海拔轨迹点（用于前端可视化）

        对轨迹点进行等距抽样，确保前端能正确显示海拔变化曲线，
        并标记关键点（起点、终点、最高点、最低点）。

        Args:
            points: 原始轨迹点列表
            total_distance_m: 总距离（米）
            max_elev_point: 最高海拔点
            min_elev_point: 最低海拔点
            num_samples: 抽样点数（默认100个）

        Returns:
            List[ElevationPoint]: 抽样后的海拔轨迹点列表
        """
        if len(points) < 2:
            return []

        # 计算每个原始点的累计距离
        cumulative_distances = [0.0]
        for i in range(len(points) - 1):
            dist = self._haversine_distance(
                points[i].lat, points[i].lon,
                points[i+1].lat, points[i+1].lon
            )
            cumulative_distances.append(cumulative_distances[-1] + dist)

        # 计算抽样间隔
        sample_interval = total_distance_m / (num_samples - 1) if num_samples > 1 else total_distance_m

        # 找出关键点在累计距离中的位置
        max_elev_distance = 0.0
        min_elev_distance = 0.0
        for i, p in enumerate(points):
            if (abs(p.lat - max_elev_point.lat) < 1e-6 and
                abs(p.lon - max_elev_point.lon) < 1e-6):
                max_elev_distance = cumulative_distances[i]
            if (abs(p.lat - min_elev_point.lat) < 1e-6 and
                abs(p.lon - min_elev_point.lon) < 1e-6):
                min_elev_distance = cumulative_distances[i]

        # 生成抽样点
        elevation_points: List[ElevationPoint] = []
        for i in range(num_samples):
            target_distance = i * sample_interval

            # 在原始点中找到最接近目标距离的点
            # 二分查找
            left, right = 0, len(cumulative_distances) - 1
            while left < right - 1:
                mid = (left + right) // 2
                if cumulative_distances[mid] <= target_distance:
                    left = mid
                else:
                    right = mid

            # 线性插值获取海拔
            if left == right or cumulative_distances[right] == cumulative_distances[left]:
                elevation = points[left].elevation
            else:
                # 线性插值
                ratio = (target_distance - cumulative_distances[left]) / (cumulative_distances[right] - cumulative_distances[left])
                elevation = points[left].elevation + ratio * (points[right].elevation - points[left].elevation)

            # 判断是否为关键点
            is_key_point = False
            label = None

            # 起点
            if i == 0:
                is_key_point = True
                label = '起点'
            # 终点
            elif i == num_samples - 1:
                is_key_point = True
                label = '终点'
            # 最高点
            elif abs(target_distance - max_elev_distance) < sample_interval / 2:
                is_key_point = True
                label = '最高点'
            # 最低点
            elif abs(target_distance - min_elev_distance) < sample_interval / 2:
                is_key_point = True
                label = '最低点'

            elevation_points.append(ElevationPoint(
                distance_m=round(target_distance, 1),
                elevation_m=round(elevation, 1),
                is_key_point=is_key_point,
                label=label
            ))

        return elevation_points

    def _generate_track_points_gcj02(
        self,
        points: List[Point3D],
        max_elev_point: Point3D,
        min_elev_point: Point3D,
        terrain_changes: List[TerrainChange],
        max_samples: int = 200
    ) -> List[TrackPointGCJ02]:
        """
        生成 GCJ02 坐标系的轨迹点（用于高德地图平面图显示）

        采用智能抽样策略：
        1. 均匀抽样最多 max_samples 个点
        2. 强制包含关键点（起点、终点、最高点、最低点、地形变化段起终点）

        Args:
            points: 原始轨迹点列表（WGS84坐标）
            max_elev_point: 最高海拔点
            min_elev_point: 最低海拔点
            terrain_changes: 地形变化段列表
            max_samples: 最大抽样点数（默认200）

        Returns:
            List[TrackPointGCJ02]: GCJ02坐标系的轨迹点列表
        """
        if len(points) < 2:
            return []

        # 关键点索引集合（用于强制包含）
        key_point_indices: set = set()

        # 起点、终点
        key_point_indices.add(0)
        key_point_indices.add(len(points) - 1)

        # 最高点、最低点
        for i, p in enumerate(points):
            if (abs(p.lat - max_elev_point.lat) < 1e-6 and
                abs(p.lon - max_elev_point.lon) < 1e-6):
                key_point_indices.add(i)
            if (abs(p.lat - min_elev_point.lat) < 1e-6 and
                abs(p.lon - min_elev_point.lon) < 1e-6):
                key_point_indices.add(i)

        # 地形变化段起终点
        for tc in terrain_changes:
            for i, p in enumerate(points):
                if (abs(p.lat - tc.start_point.lat) < 1e-5 and
                    abs(p.lon - tc.start_point.lon) < 1e-5):
                    key_point_indices.add(i)
                if (abs(p.lat - tc.end_point.lat) < 1e-5 and
                    abs(p.lon - tc.end_point.lon) < 1e-5):
                    key_point_indices.add(i)

        # 计算抽样间隔
        sample_step = max(1, len(points) // max_samples)

        # 选择抽样点索引
        sampled_indices: set = set()
        for i in range(0, len(points), sample_step):
            sampled_indices.add(i)

        # 合并关键点
        final_indices = sampled_indices | key_point_indices
        sorted_indices = sorted(final_indices)

        # 生成 GCJ02 坐标点
        track_points_gcj02: List[TrackPointGCJ02] = []
        for idx in sorted_indices:
            p = points[idx]

            # WGS84 -> GCJ02 坐标转换
            gcj_lon, gcj_lat = wgs84_to_gcj02(p.lon, p.lat)

            # 判断是否为关键点
            is_key_point = idx in key_point_indices
            label = None

            if idx == 0:
                label = '起点'
            elif idx == len(points) - 1:
                label = '终点'
            elif (abs(p.lat - max_elev_point.lat) < 1e-6 and
                  abs(p.lon - max_elev_point.lon) < 1e-6):
                label = '最高点'
            elif (abs(p.lat - min_elev_point.lat) < 1e-6 and
                  abs(p.lon - min_elev_point.lon) < 1e-6):
                label = '最低点'

            track_points_gcj02.append(TrackPointGCJ02(
                lng=round(gcj_lon, 6),
                lat=round(gcj_lat, 6),
                elevation=round(p.elevation, 1),
                is_key_point=is_key_point,
                label=label
            ))

        logger.info(f"[Sampling] original={len(points)}, sampled={len(track_points_gcj02)}, key_points={len(key_point_indices)}")
        return track_points_gcj02


__all__ = ["TrackParser", "TrackParseError"]
