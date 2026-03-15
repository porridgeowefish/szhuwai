"""
主控大脑 (Orchestrator)
====================

户外活动规划的主控制器，协调各个 API 客户端和服务，实现核心的规划流程。
"""

import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger

from src.schemas.base import Point3D
from src.schemas.output import (
    OutdoorActivityPlan,
    PlanningContext,
    TrackDetailAnalysis,
    TerrainSegment
)
from src.schemas.weather import WeatherSummary
from src.schemas.track import TrackAnalysisResult
from src.schemas.transport import TransportRoutes
from src.schemas.search import WebSearchResponse

from src.services.track_parser import TrackParser
from src.services.geo_coord_utils import wgs84_to_gcj02

from src.api.weather_client import WeatherClient
from src.api.map_client import MapClient
from src.api.search_client import SearchClient
from src.api.config import api_config


class OutdoorPlannerRouter:
    """户外活动规划主控器"""

    def __init__(self):
        """初始化规划器"""
        # 初始化服务
        self.track_parser = TrackParser()
        self.weather_client = WeatherClient()
        self.map_client = MapClient()
        self.search_client = SearchClient()

        # 关键点（存储轨迹解析后的重要位置）
        self.key_points: Dict[str, Point3D] = {}

    def execute_planning(self, trip_date: str, departure_point: str,
                         additional_info: str, gpx_path: str,
                         plan_title: str = "", key_destinations: List[str] = None) -> OutdoorActivityPlan:
        """
        执行户外活动规划主流程

        Args:
            trip_date: 出行时间（YYYY-MM-DD）
            departure_point: 出发地点（供高德解析使用）
            additional_info: 补充信息
            gpx_path: GPX/KML 轨迹文件路径（必填）
            plan_title: 线路名称/计划书标题（作为计划书名称）
            key_destinations: 核心目的地列表（用于搜索关键词）

        Returns:
            OutdoorActivityPlan: 最终的户外活动计划

        Raises:
            ValueError: 如果轨迹解析失败
        """
        # 默认值处理
        if key_destinations is None:
            key_destinations = []
        # 步骤 1: 强制解析轨迹（轨迹是唯一数据源）
        track_analysis = self._parse_track(gpx_path)
        if not track_analysis:
            raise ValueError("无法解析轨迹文件，规划终止")

        # 步骤 2: 坐标纠偏
        self._coordinate_correction(track_analysis)

        # 步骤 3: 提取坐标真理（轨迹起点的经纬度为绝对目的地）
        start_point = track_analysis.start_point
        if not start_point:
            raise ValueError("轨迹解析成功但无法获取起点坐标，规划终止")

        destination_coord = f"{start_point.lon},{start_point.lat}"
        logger.info(f"提取到轨迹目的地坐标: {destination_coord}")

        # 步骤 4: 并发数据获取（基于轨迹坐标）
        weather_data, transport_data, search_data, precise_location_name, around_rescue_data = self._gather_data_concurrently(
            track_analysis=track_analysis,
            trip_date=trip_date,
            departure_point=departure_point,
            destination_coord=destination_coord,
            additional_info=additional_info,
            plan_title=plan_title,
            key_destinations=key_destinations
        )

        # 步骤 5: 上下文组装（使用用户输入的线路名称作为计划书标题）
        user_request = f"计划在{trip_date}从{departure_point}出发进行户外活动。{additional_info}"
        context = self._assemble_context(
            user_request=user_request,
            track_analysis=track_analysis,
            weather_data=weather_data,
            transport_data=transport_data,
            search_data=search_data,
            additional_info=additional_info,
            precise_location_name=precise_location_name,
            around_rescue_data=around_rescue_data,
            plan_title=plan_title,  # 传递线路名称
            key_destinations=key_destinations  # 传递核心目的地
        )

        # 步骤 6: LLM 提炼与实例化
        return self._llm_synthesis(context)

    def _parse_track(self, gpx_path: str) -> Optional[TrackAnalysisResult]:
        """
        步骤 1: 轨迹解析（强制必填）

        Args:
            gpx_path: GPX/KML 轨迹文件路径

        Returns:
            TrackAnalysisResult: 轨迹分析结果

        Raises:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果文件解析失败
        """
        if not gpx_path or not Path(gpx_path).exists():
            raise FileNotFoundError(f"轨迹文件不存在: {gpx_path}")

        try:
            logger.info(f"开始解析轨迹文件: {gpx_path}")
            track_analysis = self.track_parser.parse_file(gpx_path)
            logger.info(f"轨迹解析完成: 总距离 {track_analysis.total_distance_km:.2f}km, "
                       f"爬升 {track_analysis.total_ascent_m}m, 下降 {track_analysis.total_descent_m}m")
            return track_analysis
        except Exception as e:
            logger.error(f"轨迹解析失败: {e}")
            raise ValueError(f"轨迹文件解析失败: {str(e)}")

    def _coordinate_correction(self, track_analysis: TrackAnalysisResult):
        """
        步骤 2: 坐标纠偏
        将所有 WGS84 坐标转为 GCJ02
        """
        logger.info("开始坐标纠偏（WGS84 -> GCJ02）")

        # 处理关键点（起点、终点、最高点、最低点等）
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

    def _gather_data_concurrently(self, track_analysis: TrackAnalysisResult,
                                  trip_date: str, departure_point: str,
                                  destination_coord: str, additional_info: str,
                                  plan_title: str = "", key_destinations: List[str] = None) -> Tuple[Optional[WeatherSummary], Optional[TransportRoutes], List[WebSearchResponse], str, List[Dict]]:
        """
        步骤 4: 使用线程池并发调用 API 客户端获取数据

        基于轨迹解析的坐标进行所有查询，确保数据的准确性和一致性。

        Args:
            track_analysis: 轨迹分析结果
            trip_date: 出行时间
            departure_point: 出发地点（用于地理编码）
            destination_coord: 目的地坐标（轨迹起点坐标）
            additional_info: 补充信息
            plan_title: 线路名称/计划书标题
            key_destinations: 核心目的地列表（用于搜索关键词）

        Returns:
            Tuple: (天气数据, 交通数据, 搜索数据, 精准位置名称, 周边救援数据)
        """
        logger.info("开始并发获取数据（基于轨迹坐标）")

        # 默认值处理
        if key_destinations is None:
            key_destinations = []

        # 获取关键坐标用于天气查询（WGS84坐标系）
        weather_location = f"{track_analysis.start_point.lat},{track_analysis.start_point.lon}"

        # 步骤 1: 获取逆地理编码，仅用于周边救援数据查询（不再用于搜索关键词）
        precise_location_name = ""
        regeo_result = None
        try:
            # 使用纠偏后的坐标（GCJ02）进行逆地理编码
            if 'start' in self.key_points:
                gcj_lon = self.key_points['start'].lon
                gcj_lat = self.key_points['start'].lat
            else:
                gcj_lon = track_analysis.start_point.lon
                gcj_lat = track_analysis.start_point.lat

            regeo_result = self.map_client.reverse_geocode(f"{gcj_lon},{gcj_lat}")

            # 按优先级提取精准位置名称（仅用于显示，不再用于搜索）
            precise_location_name = regeo_result.get_precise_location_name()

            logger.info(f"轨迹位置精准地名: {precise_location_name}")
            logger.debug(f"逆地理编码详情: POI数={len(regeo_result.pois)}, 道路数={len(regeo_result.roads)}")

        except Exception as e:
            logger.warning(f"逆地理编码失败: {e}")
            # 兜底：使用轨迹文件名或默认
            precise_location_name = track_analysis.track_name or "户外徒步"

        # 步骤 2: 构建搜索查询（基于用户输入的核心目的地，而非逆地理编码）
        # 使用核心目的地作为搜索关键词
        search_keywords = " ".join(key_destinations) if key_destinations else (plan_title or "户外徒步")
        logger.info(f"搜索关键词（基于用户输入）: {search_keywords}")

        search_queries = []

        # 1. 周边景区搜索（使用核心目的地）
        search_queries.append(f"{search_keywords} 景点 景区 旅游")

        # 2. 附近救援队搜索（使用核心目的地）
        search_queries.append(f"{search_keywords} 户外徒步 应急救援队 报警电话")

        # 3. 徒步攻略搜索（使用核心目的地）
        search_queries.append(f"{search_keywords} 徒步攻略 登山路线 注意事项")

        # 4. 装备推荐搜索（使用核心目的地）
        search_queries.append(f"{search_keywords} 徒步装备 登山装备 露营装备推荐")

        # 定义获取函数
        def fetch_weather():
            """获取轨迹多点的格点天气数据和全天24小时逐小时预报"""
            try:
                start = track_analysis.start_point
                # 使用格点天气API - 参数是 (lon, lat) 顺序
                logger.info(f"获取格点天气: lon={start.lon}, lat={start.lat}, 日期={trip_date}")

                # 获取3天格点天气预报（主要数据源）
                grid_weather = self.weather_client.get_grid_weather_3d(start.lon, start.lat)

                # 获取全天24小时逐小时天气预报（格点API）
                hourly_weather = None
                try:
                    hourly_weather = self.weather_client.get_grid_weather_24h(start.lon, start.lat)
                    logger.info(f"获取到24小时逐小时天气数据，共{len(hourly_weather.hourly)}小时")
                except Exception as e:
                    logger.warning(f"获取24小时逐小时天气失败: {e}")

                # 获取多抽样点的格点天气（起点、中点、最高点、终点）
                grid_point_weather_list = []

                # 1. 起点
                try:
                    start_now = self.weather_client.get_grid_weather_now(start.lon, start.lat)
                    if start_now and "now" in start_now:
                        now = start_now["now"]
                        grid_point_weather_list.append({
                            "point_type": "起点",
                            "temp": int(float(now.get("temp", 0))),
                            "wind_scale": now.get("windScale", "0"),
                            "humidity": int(float(now.get("humidity", 0)))
                        })
                except Exception as e:
                    logger.warning(f"获取起点实时天气失败: {e}")

                # 2. 最高点
                if track_analysis.max_elev_point:
                    try:
                        highest = track_analysis.max_elev_point
                        highest_now = self.weather_client.get_grid_weather_now(highest.lon, highest.lat)
                        if highest_now and "now" in highest_now:
                            now = highest_now["now"]
                            grid_point_weather_list.append({
                                "point_type": "最高点",
                                "temp": int(float(now.get("temp", 0))),
                                "wind_scale": now.get("windScale", "0"),
                                "humidity": int(float(now.get("humidity", 0)))
                            })
                    except Exception as e:
                        logger.warning(f"获取最高点实时天气失败: {e}")

                # 3. 终点
                if track_analysis.end_point:
                    try:
                        end = track_analysis.end_point
                        end_now = self.weather_client.get_grid_weather_now(end.lon, end.lat)
                        if end_now and "now" in end_now:
                            now = end_now["now"]
                            grid_point_weather_list.append({
                                "point_type": "终点",
                                "temp": int(float(now.get("temp", 0))),
                                "wind_scale": now.get("windScale", "0"),
                                "humidity": int(float(now.get("humidity", 0)))
                            })
                    except Exception as e:
                        logger.warning(f"获取终点实时天气失败: {e}")

                # 4. 中点（如果轨迹点足够多）
                if hasattr(track_analysis, 'track_points') and track_analysis.track_points and len(track_analysis.track_points) > 10:
                    try:
                        mid_idx = len(track_analysis.track_points) // 2
                        mid_point = track_analysis.track_points[mid_idx]
                        mid_now = self.weather_client.get_grid_weather_now(mid_point.lon, mid_point.lat)
                        if mid_now and "now" in mid_now:
                            now = mid_now["now"]
                            grid_point_weather_list.append({
                                "point_type": "中点",
                                "temp": int(float(now.get("temp", 0))),
                                "wind_scale": now.get("windScale", "0"),
                                "humidity": int(float(now.get("humidity", 0)))
                            })
                    except Exception as e:
                        logger.warning(f"获取中点实时天气失败: {e}")

                logger.info(f"获取到{len(grid_point_weather_list)}个抽样点的天气数据")

                # 将 GridWeatherResponse 转换为 CityWeatherResponse 格式
                from src.schemas.weather import WeatherSummary, CityWeatherResponse, CityWeatherDaily

                city_daily = []
                for day in grid_weather.daily:
                    city_daily.append(CityWeatherDaily(
                        fxDate=day.fxDate,
                        tempMax=day.tempMax,
                        tempMin=day.tempMin,
                        textDay=day.textDay,
                        windScaleDay=day.windScaleDay,
                        windSpeedDay=day.windSpeedDay,
                        humidity=day.humidity,
                        precip=day.precip,
                        pressure=day.pressure
                        # 格点天气API不返回 uvIndex、vis、cloud，这些字段保持为 None
                    ))

                city_weather = CityWeatherResponse(
                    location=grid_weather.location,
                    updateTime=grid_weather.updateTime,
                    daily=city_daily
                )

                summary = WeatherSummary(
                    trip_date=trip_date,
                    forecast_days=3,
                    use_grid=True,
                    forecast_3d=city_weather
                )
                # 计算最高最低温度
                if grid_weather and grid_weather.daily:
                    temps = []
                    for day in grid_weather.daily:
                        temps.extend([day.tempMax, day.tempMin])
                    if temps:
                        summary.max_temp = max(temps)
                        summary.min_temp = min(temps)

                # 附加全天24小时逐小时天气数据（存储在summary中）
                if hourly_weather:
                    summary.hourly_24h = hourly_weather

                # 附加多抽样点天气数据
                summary.grid_points = grid_point_weather_list

                return summary
            except Exception as e:
                logger.error(f"获取天气数据失败: {e}")
                return None

        def fetch_transport():
            """获取从出发地点到轨迹起点的交通路线（驾车 + 公交/地铁）"""
            try:
                logger.info(f"获取交通路线: 起点={departure_point}, 终点坐标={destination_coord}")
                # 先对出发地点进行地理编码
                departure_geocode = self.map_client.geocode(departure_point)
                departure_coord = f"{departure_geocode.lon},{departure_geocode.lat}"
                logger.info(f"出发地点地理编码: {departure_coord}")

                # 获取驾车路线
                driving_route = self.map_client.driving_route(departure_coord, destination_coord)

                # 获取公交/地铁路线（需要城市名）
                transit_routes = []
                try:
                    city = departure_geocode.city or departure_geocode.province
                    transit_routes = self.map_client.transit_route(departure_coord, destination_coord, city)
                    if transit_routes:
                        logger.info(f"获取到 {len(transit_routes)} 条公交/地铁路线")
                except Exception as e:
                    logger.warning(f"获取公交路线失败: {e}")

                # 转换为 TransportRoutes 格式
                from src.schemas.transport import TransportRoutes, LocationInfo, RouteSummary

                dep_lon, dep_lat = departure_coord.split(',')
                dest_lon, dest_lat = destination_coord.split(',')

                # 构建 outbound 字典（驾车 + 公交/地铁）
                outbound = {"driving": driving_route.model_dump()}
                if transit_routes:
                    outbound["transit"] = transit_routes[0].model_dump()

                # 确定最快和最便宜的交通方式
                mode_times = {"驾车": driving_route.duration_min}
                mode_costs = {"驾车": driving_route.tolls_yuan}

                if transit_routes:
                    for i, route in enumerate(transit_routes):
                        mode_name = f"公交方案{i+1}" if i > 0 else "公交"
                        mode_times[mode_name] = route.duration_min
                        mode_costs[mode_name] = route.cost_yuan

                fastest_mode = min(mode_times.keys(), key=lambda k: mode_times[k])
                cheapest_mode = min(mode_costs.keys(), key=lambda k: mode_costs[k])

                # 推荐方案（综合考虑）
                if driving_route.distance_km < 50:
                    recommended_mode = "驾车"
                elif transit_routes:
                    recommended_mode = "公交"
                else:
                    recommended_mode = "驾车"

                # 构建汇总信息
                total_distance = f"{driving_route.distance_km:.1f}公里"
                total_time = f"{driving_route.duration_min}分钟"
                cost_info = f"过路费约{driving_route.tolls_yuan}元" if driving_route.tolls_yuan > 0 else ""

                return TransportRoutes(
                    origin=LocationInfo(
                        address=departure_point,
                        lon=float(dep_lon),
                        lat=float(dep_lat),
                        city=departure_geocode.city,
                        province=departure_geocode.province
                    ),
                    destination=LocationInfo(
                        address="轨迹起点",
                        lon=float(dest_lon),
                        lat=float(dest_lat)
                    ),
                    outbound=outbound,
                    return_route={},
                    summary=RouteSummary(
                        total_distance=total_distance,
                        total_time=total_time,
                        cost=cost_info,
                        fastest_mode=fastest_mode,
                        cheapest_mode=cheapest_mode
                    ),
                    recommended_mode=recommended_mode,
                    fastest_mode=fastest_mode,
                    cheapest_mode=cheapest_mode,
                    taxi_cost_yuan=driving_route.tolls_yuan,
                    transit_routes=transit_routes if transit_routes else None
                )
            except Exception as e:
                logger.error(f"获取交通路线失败: {e}")
                return None

        def fetch_search():
            """执行多个搜索查询并合并结果"""
            all_results = []
            for query in search_queries:
                try:
                    logger.info(f"执行搜索查询: {query}")
                    result = self.search_client.search(query, max_results=5)
                    if result and isinstance(result, WebSearchResponse):
                        all_results.append(result)
                except Exception as e:
                    logger.error(f"搜索失败 [{query}]: {e}")
                    continue
            return all_results

        def fetch_around_rescue():
            """获取周边救援数据（医院、派出所、公安局）- 硬核数据"""
            try:
                # 使用纠偏后的坐标（GCJ02）
                if 'start' in self.key_points:
                    gcj_lon = self.key_points['start'].lon
                    gcj_lat = self.key_points['start'].lat
                else:
                    gcj_lon = track_analysis.start_point.lon
                    gcj_lat = track_analysis.start_point.lat

                location = f"{gcj_lon},{gcj_lat}"

                # 搜索周边医院、诊所、派出所、公安局
                keywords = "医院|诊所|派出所|公安局"
                logger.info(f"周边救援搜索: location={location}, keywords={keywords}")

                results = self.map_client.search_around(
                    location=location,
                    keywords=keywords,
                    radius=10000,  # 10km 半径
                    page_size=20
                )

                if results:
                    logger.info(f"找到 {len(results)} 个周边救援点")
                else:
                    logger.info("周边救援搜索未找到结果，返回空列表")

                return results  # 如果没搜到，返回空列表 []，严禁编造数据

            except Exception as e:
                logger.error(f"周边救援搜索失败: {e}")
                return []  # 失败返回空列表，不编造数据

        # 使用线程池并发执行
        weather_data = None
        transport_data = None
        search_data = []
        around_rescue_data = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_name = {
                executor.submit(fetch_weather): "weather",
                executor.submit(fetch_transport): "transport",
                executor.submit(fetch_search): "search",
                executor.submit(fetch_around_rescue): "around_rescue"
            }

            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    result = future.result()
                    if name == "weather":
                        weather_data = result
                    elif name == "transport":
                        transport_data = result
                    elif name == "search":
                        # fetch_search 现在返回 List[WebSearchResponse]
                        if result:
                            search_data = result if isinstance(result, list) else [result]
                    elif name == "around_rescue":
                        around_rescue_data = result if result else []
                except Exception as e:
                    logger.error(f"并发任务 {name} 执行失败: {e}")

        logger.info(f"数据获取完成: 搜索结果={len(search_data)}组, 救援点={len(around_rescue_data)}个")
        return weather_data, transport_data, search_data, precise_location_name, around_rescue_data

    def _assemble_context(self, user_request: str,
                         track_analysis: Optional[TrackAnalysisResult],
                         weather_data: Optional[WeatherSummary],
                         transport_data: Optional[TransportRoutes],
                         search_data: List[WebSearchResponse],
                         additional_info: str = "",
                         precise_location_name: str = "",
                         around_rescue_data: List[Dict] = None,
                         plan_title: str = "",
                         key_destinations: List[str] = None) -> PlanningContext:
        """
        步骤 4: 上下文组装
        """
        logger.info("组装规划上下文")

        # 生成评分（基于距离、爬升、天气条件等）
        confidence_score = self._calculate_confidence_score(
            track_analysis, weather_data, transport_data
        )

        context = PlanningContext(
            raw_request=user_request,
            additional_info=additional_info,
            precise_location_name=precise_location_name,
            plan_title=plan_title,  # 新增：线路名称
            key_destinations=key_destinations or [],  # 新增：核心目的地列表
            track_analysis_raw=track_analysis or self._create_empty_track(),
            weather_raw=weather_data or self._create_empty_weather(),
            transport_raw=transport_data or self._create_empty_transport(),
            search_raw=search_data,
            around_rescue_data=around_rescue_data or [],  # 严格使用空列表，不编造
            confidence_score=confidence_score
        )

        logger.info("上下文组装完成")
        return context

    def _create_empty_weather(self):
        """创建空的天气数据"""
        from src.schemas.weather import WeatherSummary, WeatherSummaryInfo

        return WeatherSummary(
            trip_date=datetime.now().strftime('%Y-%m-%d'),
            forecast_days=1,
            use_grid=False,
            summary=WeatherSummaryInfo(
                conditions="未知",
                recommendation="未知",
                risk_level="未知"
            )
        )

    def _create_empty_transport(self):
        """创建空的交通数据"""
        from src.schemas.transport import TransportRoutes, LocationInfo, RouteSummary

        return TransportRoutes(
            origin=LocationInfo(
                address="未知起点",
                lat=0,
                lon=0,
                city="未知"
            ),
            destination=LocationInfo(
                address="未知终点",
                lat=0,
                lon=0,
                city="未知"
            ),
            outbound={},
            return_route={},
            summary=RouteSummary()
        )

    def _llm_synthesis(self, context: PlanningContext) -> OutdoorActivityPlan:
        """
        步骤 5: LLM 提炼与实例化
        使用大模型将 PlanningContext 转化为 OutdoorActivityPlan
        """
        logger.info("开始 LLM 提炼与生成")

        # 提取关键信息
        track_overview = self._generate_track_overview(context.track_analysis_raw)
        weather_overview = self._generate_weather_overview(context.weather_raw)
        transport_overview = self._generate_transport_overview(context.transport_raw)

        # 生成计划ID
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 构建 LLM 提示词
        llm_prompt = self._build_llm_prompt(context)

        # 调用 LLM API 生成计划（无兜底，失败即抛出异常）
        plan = self._call_llm_api(
            prompt=llm_prompt,
            plan_id=plan_id,
            track_overview=track_overview,
            weather_overview=weather_overview,
            transport_overview=transport_overview,
            context=context
        )

        logger.info("LLM 提炼完成")
        return plan

    def _call_llm_api(self, prompt: str, plan_id: str,
                     track_overview: str, weather_overview: str,
                     transport_overview: str, context: PlanningContext) -> OutdoorActivityPlan:
        """调用 LLM API 生成户外活动计划"""

        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_config.LLM_API_KEY}"
        }

        # 构建请求体
        # 使用Pro/moonshotai/Kimi-K2.5 使用K2.5，最新模型
        payload = {
            "model": "Pro/moonshotai/Kimi-K2.5",
            "messages": [
                {
                    "role": "system",
                    "content": """你是一个专业的户外活动规划助手。根据用户请求和收集到的数据（轨迹、天气、交通、安全信息），生成一个结构化的户外活动计划。

请严格按照以下 JSON 格式输出户外活动计划，确保所有字段都正确填写。

⚠️ 重要约束（必须遵守）：
1. **equipment_recommendations 中的 category 字段必须从以下列表中选择**：
   - 服装、鞋类、背包、露营装备、炊具、安全装备、导航工具、卫生用品、电子产品、其他
   - 绝对不允许创造新分类！例如防晒霜归入"卫生用品"或"其他"

2. **equipment_recommendations 中的 priority 字段必须从以下列表中选择**：
   - 必需、推荐、可选

3. **safety_issues 中的 type 字段必须从以下列表中选择**：
   - 天气风险、地形风险、交通风险、野生动物风险、紧急情况、装备风险、身体条件风险

4. **safety_issues 中的 severity 字段必须从以下列表中选择**：
   - 低、中、高、极高

5. **scenic_spots 中的 difficulty 字段必须从以下列表中选择**：
   - 简单、中等、困难

6. **overall_rating 和 safety_assessment 中的 recommendation 字段必须从以下列表中选择**：
   - 推荐、谨慎推荐、不推荐

7. **emergency_rescue_contacts 中的 type 字段必须从以下列表中选择**：
   - 医疗、救援、报警

8. **⚠️ 零幻觉原则**：请基于提供的真实轨迹指标（里程、爬升、海拔）进行风险评估。如果数据缺失，请报告数据不足，严禁编造轨迹指标或虚构数据。
以下是一个样例json文件，请你作为生成参考。
```json
{
    "plan_id": "计划ID",
    "plan_name": "计划名称",
    "overall_rating": "推荐|谨慎推荐|不推荐",
    "track_overview": "轨迹概述，如：11km/爬升750m/困难",
    "weather_overview": "天气概述，如：周末晴朗，最高25度，无降水风险",
    "transport_overview": "交通概述，如：建议驾车，约1.5小时",
    "trip_date_weather": {
        "fxDate": "YYYY-MM-DD",
        "tempMax": 25,
        "tempMin": 15,
        "textDay": "晴",
        "windScaleDay": "3",
        "windSpeedDay": 10,
        "humidity": 50,
        "precip": 0,
        "pressure": 1013,
        "uvIndex": 8,
        "vis": 20
    },
    "hourly_weather": [
        {"fxTime": "YYYY-MM-DDTHH:MM:SS", "temp": 18, "pop": 0, "precip": 0, "windScale": "2"}
    ],
    "critical_grid_weather": [
        {"point_type": "起点|终点|最高点|中点", "temp": 18, "wind_scale": "2", "humidity": 65}
    ],
    "itinerary": [
        {"time": "08:00", "activity": "活动内容", "location": "地点", "duration_minutes": 30, "notes": "备注"}
    ],
    "equipment_recommendations": [
        {"name": "装备名称", "category": "服装|鞋类|背包|露营装备|炊具|安全装备|导航工具|卫生用品|电子产品|其他", "priority": "必需|推荐|可选", "quantity": 1, "weight_kg": 3, "description": "描述", "alternatives": ["替代品"]}
    ],
    "scenic_spots": [
        {"name": "景点名称", "description": "景点描述", "location": {"lon": 116.4, "lat": 39.9, "elevation": 100}, "best_view_time": "10:00-14:00", "photo_spots": ["摄影点"], "difficulty": "简单|中等|困难", "estimated_visit_time_min": 30}
    ],
    "precautions": ["注意事项1", "注意事项2"],
    "safety_assessment": {
        "overall_risk": "低风险|中等风险|高风险",
        "conditions": "条件描述",
        "recommendation": "推荐|谨慎推荐|不推荐",
        "risk_level": "低风险|中等风险|高风险"
    },
    "safety_issues": [
        {"type": "天气风险|地形风险|交通风险|野生动物风险|紧急情况|装备风险|身体条件风险", "severity": "低|中|高|极高", "description": "问题描述", "mitigation": "缓解措施", "emergency_contact": "紧急联系方式"}
    ],
    "risk_factors": ["风险因素1", "风险因素2"],
    "emergency_rescue_contacts": [
        {"name": "救援机构名称", "phone": "电话", "type": "医疗|救援|报警"}
    ]
}
```

请根据以下上下文信息生成计划："""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"}
        }

        # 发送请求
        response = requests.post(
            api_config.LLM_BASE_URL,
            headers=headers,
            json=payload,
            timeout=60,
            proxies=api_config.PROXY if api_config.should_use_proxy() else None
        )

        if response.status_code != 200:
            raise Exception(f"LLM API 返回错误: {response.status_code} - {response.text}")

        # 解析响应
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")

        # 解析 JSON
        try:
            plan_data = json.loads(content)
        except json.JSONDecodeError:
            raise Exception(f"无法解析 LLM 返回的 JSON: {content[:200]}")

        # 添加必要字段
        plan_data["plan_id"] = plan_id
        plan_data["created_at"] = datetime.now()

        # 使用用户输入的线路名称作为计划书标题（覆盖LLM生成的名称）
        if context.plan_title and context.plan_title.strip():
            plan_data["plan_name"] = context.plan_title.strip()

        # 确保 overview 字段使用我们生成的版本
        plan_data["track_overview"] = track_overview
        plan_data["weather_overview"] = weather_overview
        plan_data["transport_overview"] = transport_overview

        # 填充轨迹详细分析数据（从原始轨迹分析结果中提取）
        track_raw = context.track_analysis_raw
        if track_raw:
            # 转换地形分析数据
            terrain_segments = []
            for seg in track_raw.terrain_analysis:
                terrain_segments.append(TerrainSegment(
                    change_type=seg.change_type,
                    elevation_diff=round(seg.elevation_diff, 1),
                    distance_m=round(seg.distance_m, 1),
                    gradient_percent=round(seg.gradient_percent, 1)
                ))

            # 创建轨迹详细分析（数据格式化到小数点后一位）
            track_detail = TrackDetailAnalysis(
                total_distance_km=round(track_raw.total_distance_km, 1),
                total_ascent_m=round(track_raw.total_ascent_m, 1),
                total_descent_m=round(track_raw.total_descent_m, 1),
                max_elevation_m=round(track_raw.max_elevation_m, 1),
                min_elevation_m=round(track_raw.min_elevation_m, 1),
                avg_elevation_m=round(track_raw.avg_elevation_m, 1),
                difficulty_level=track_raw.difficulty_level,
                difficulty_score=round(track_raw.difficulty_score, 1),
                estimated_duration_hours=round(track_raw.estimated_duration_hours, 1),
                safety_risk=track_raw.safety_risk,
                terrain_analysis=terrain_segments,
                cloud_sea_assessment=None  # TODO: 后续可添加云海评估逻辑
            )
            plan_data["track_detail"] = track_detail.model_dump()

        # 填充交通方案详情（从 transport_raw 中提取）
        if context.transport_raw and context.transport_raw.outbound:
            plan_data["transport_scheme"] = context.transport_raw.model_dump()

        # 转换为 Pydantic 模型
        return OutdoorActivityPlan(**plan_data)

    def _calculate_confidence_score(self, track_analysis, weather_data, transport_data) -> float:
        """计算方案可信度评分"""
        score = 0.5  # 基础分

        # 基于轨迹质量加分
        if track_analysis and track_analysis.total_distance_km > 0:
            score += 0.2
            if track_analysis.total_distance_km > 5:  # 5km以上
                score += 0.1

        # 基于天气条件加分
        if weather_data:
            score += 0.2
            # TODO: 根据天气具体条件调整

        # 基于交通路线加分
        if transport_data:
            score += 0.1

        return min(score, 1.0)

    def _create_empty_track(self) -> TrackAnalysisResult:
        """创建空的轨迹分析结果"""
        from src.schemas.base import Point3D
        from src.schemas.track import TrackAnalysisResult

        # 创建一个默认的起点，避免API调用失败
        default_point = Point3D(lon=116.4, lat=39.9, elevation=100)

        return TrackAnalysisResult(
            track_name="未知",
            total_distance_km=0.1,  # 不能为0
            total_ascent_m=0,
            total_descent_m=0,
            max_elevation_m=100,
            min_elevation_m=100,
            avg_elevation_m=100,
            start_point=default_point,
            end_point=default_point,
            max_elev_point=default_point,
            min_elev_point=default_point,
            terrain_analysis=[],
            difficulty_score=10,
            difficulty_level="简单",
            estimated_duration_hours=0.1,  # 不能为0
            safety_risk="低风险",
            track_points_count=1  # 不能为0
        )

    def _generate_track_overview(self, track_analysis) -> str:
        """生成轨迹概述（仅显示里程和爬升）"""
        if not track_analysis:
            return "无轨迹数据"

        distance_km = track_analysis.total_distance_km
        ascent_m = track_analysis.total_ascent_m
        return f"{distance_km:.1f}km/爬升{ascent_m:.1f}m"

    def _generate_weather_overview(self, weather_data) -> str:
        """生成天气概述"""
        if not weather_data:
            return "无天气数据"

        # 从 summary.conditions 获取天气状况描述
        conditions = weather_data.summary.conditions or "未知"

        # 优先检查 forecast_3d（格点天气使用这个）
        forecast = None
        if weather_data.forecast_3d and weather_data.forecast_3d.daily:
            forecast = weather_data.forecast_3d.daily[0]
        elif weather_data.forecast_7d and weather_data.forecast_7d.daily:
            forecast = weather_data.forecast_7d.daily[0]

        if forecast:
            temp_range = f"{forecast.tempMin}~{forecast.tempMax}°C"
            precip = f"降水{forecast.precip}mm"
            wind = f"风力{forecast.windScaleDay}级"
            return f"{forecast.textDay}，{temp_range}，{precip}，{wind}"

        # 否则返回基本描述
        return f"{conditions}，温度信息不可用"

    def _generate_transport_overview(self, transport_data) -> str:
        """生成交通概述"""
        if not transport_data:
            return "交通信息不可用"

        # 使用 TransportRoutes 的汇总信息
        if transport_data.summary.total_distance and transport_data.summary.total_time:
            cost_info = f"，{transport_data.summary.cost}" if transport_data.summary.cost else ""
            return f"驾车{transport_data.summary.total_distance}，约{transport_data.summary.total_time}{cost_info}"

        # 从 outbound 中提取驾车信息
        if transport_data.outbound and "driving" in transport_data.outbound:
            driving = transport_data.outbound["driving"]
            distance_km = driving.get("distance_km", 0)
            duration_min = driving.get("duration_min", 0)
            tolls = driving.get("tolls_yuan", 0)
            cost_str = f"，过路费{tolls}元" if tolls > 0 else ""
            return f"驾车{distance_km:.1f}公里，约{duration_min}分钟{cost_str}"

        # 使用推荐的交通方式
        if transport_data.recommended_mode:
            return f"建议{transport_data.recommended_mode}"

        return "交通信息不可用"

    def _build_llm_prompt(self, context: PlanningContext) -> str:
        """构建 LLM 提示"""
        # 构建额外要求的提示部分
        additional_info_section = ""
        if context.additional_info and context.additional_info.strip():
            additional_info_section = f"""
## ⚠️ 用户额外要求（请在规划中重点考虑）
{context.additional_info}

**重要提示**：请在行程安排、装备建议、注意事项等方面充分考虑上述用户的额外要求。
"""

        # 整理搜索结果，按类别分组
        scenic_results = []
        rescue_results = []
        guide_results = []
        equipment_results = []

        for search_response in context.search_raw:
            query = search_response.query.lower()
            for result in search_response.results:
                result_info = f"- {result.title}: {result.content[:150]}..."

                # 根据搜索查询关键词分类
                if '景点' in query or '景区' in query or '旅游' in query:
                    scenic_results.append(result_info)
                elif '救援' in query or '蓝天' in query or '应急' in query:
                    rescue_results.append(result_info)
                elif '攻略' in query or '路线' in query or '注意事项' in query:
                    guide_results.append(result_info)
                elif '装备' in query or '登山' in query or '露营' in query:
                    equipment_results.append(result_info)

        # 构建搜索结果部分
        search_section = "\n## 搜索参考信息\n"

        if scenic_results:
            search_section += "\n### 周边景区/景点\n"
            search_section += "\n".join(scenic_results[:5]) + "\n"

        if rescue_results:
            search_section += "\n### 应急救援信息（Web搜索）\n"
            search_section += "\n".join(rescue_results[:5]) + "\n"

        if guide_results:
            search_section += "\n### 徒步攻略参考\n"
            search_section += "\n".join(guide_results[:5]) + "\n"

        if equipment_results:
            search_section += "\n### 装备推荐参考\n"
            search_section += "\n".join(equipment_results[:5]) + "\n"

        # 构建高德周边救援数据部分（硬核数据）
        around_rescue_section = ""
        if context.around_rescue_data:
            around_rescue_section = "\n## 🏥 高德地图周边救援数据（硬核数据，优先使用）\n"
            around_rescue_section += f"**精准位置**: {context.precise_location_name}\n\n"

            # 按类型分组
            hospitals = []
            police = []
            for poi in context.around_rescue_data:
                poi_type = poi.get("type", "")
                name = poi.get("name", "未知")
                address = poi.get("address", "")
                tel = poi.get("tel", "")
                distance = poi.get("distance", "")
                distance_str = f"{distance:.0f}米" if distance else "未知距离"

                if "医院" in poi_type or "诊所" in poi_type:
                    hospitals.append(f"- **{name}**: {address}, 距离{distance_str}" + (f", 电话: {tel}" if tel else ""))
                elif "派出所" in poi_type or "公安" in poi_type:
                    police.append(f"- **{name}**: {address}, 距离{distance_str}" + (f", 电话: {tel}" if tel else ""))

            if hospitals:
                around_rescue_section += "\n### 周边医院/诊所\n"
                around_rescue_section += "\n".join(hospitals[:10]) + "\n"

            if police:
                around_rescue_section += "\n### 周边派出所/公安局\n"
                around_rescue_section += "\n".join(police[:5]) + "\n"

            around_rescue_section += "\n**重要提示**：以上数据来自高德地图 API，是轨迹起点周边的真实救援设施，请优先将这些电话填入 emergency_rescue_contacts。\n"
        else:
            around_rescue_section = "\n## 🏥 高德地图周边救援数据\n无（10km范围内未搜索到医院/派出所，请使用 Web 搜索结果或通用报警电话）\n"

        # 构建全天24小时逐小时天气数据部分
        hourly_24h_section = ""
        if context.weather_raw and context.weather_raw.hourly_24h and context.weather_raw.hourly_24h.hourly:
            hourly_24h_section = "\n## 🕐 全天24小时逐小时天气预报（格点API，不基于活动时间）\n"
            hourly_24h_section += "**重要**：请在 hourly_weather 字段中输出全天24小时的逐小时天气数据，不需要根据活动时间过滤。\n\n"
            hourly_24h_section += "### 格点逐小时预报数据\n"
            for hour in context.weather_raw.hourly_24h.hourly:
                time_str = hour.fxTime.split('T')[1][:5] if 'T' in hour.fxTime else hour.fxTime
                hourly_24h_section += f"- {time_str}: 温度{hour.temp}°C, 降水概率{hour.pop}%, 降水量{hour.precip}mm, 风力{hour.windScale}级\n"

        # 构建多抽样点格点天气数据部分
        grid_points_section = ""
        if context.weather_raw and context.weather_raw.grid_points:
            grid_points_section = "\n## 📍 多抽样点格点天气数据（格点API）\n"
            grid_points_section += "**重要**：请在 critical_grid_weather 字段中包含以下所有抽样点的天气数据。\n\n"
            grid_points_section += "### 各点位实时天气\n"
            for point in context.weather_raw.grid_points:
                grid_points_section += f"- **{point['point_type']}**: 温度{point['temp']}°C, 风力{point['wind_scale']}级, 湿度{point['humidity']}%\n"

        prompt = f"""
请根据以下户外活动规划信息，生成一个详细的户外活动计划：

## 用户原始请求
{context.raw_request}
{additional_info_section}
## 轨迹分析信息
- 总距离：{context.track_analysis_raw.total_distance_km:.1f}公里
- 总爬升：{context.track_analysis_raw.total_ascent_m}米
- 总下降：{context.track_analysis_raw.total_descent_m}米
- 难度：{context.track_analysis_raw.difficulty_level}
- 天气条件：{context.weather_raw.summary.conditions if context.weather_raw and context.weather_raw.summary else '未知'}
- 交通路线：{context.transport_raw.summary.total_distance if context.transport_raw and context.transport_raw.summary else '未知'}
{hourly_24h_section}
{grid_points_section}
{search_section}
{around_rescue_section}
请按照 OutdoorActivityPlan 的结构化输出格式，生成一个完整的户外活动计划，包括：
1. 基础信息（计划ID、创建时间、计划名称、推荐等级）
2. 轨迹概述、天气概述、交通概述
3. 天气数据（当天详细天气、逐小时天气、关键格点天气）
4. 行程安排、装备建议、风景点推荐（请参考上述周边景区信息）
5. 注意事项（请参考上述徒步攻略）、安全评估、安全风险点、风险因素标签
6. 应急救援电话（**优先使用高德地图周边救援数据中的医院/派出所电话**，其次参考 Web 搜索结果）

## 重要约束条件

关于装备建议 (equipment_recommendations)：
请注意，装备的 `category` 字段必须且只能从以下列表中选择：
['服装', '鞋类', '背包', '露营装备', '炊具', '安全装备', '导航工具', '卫生用品', '电子产品', '其他']。

绝对不允许创造新的分类！例如：
- 如果建议带防晒霜、护肤品、面霜等，请归类到 "卫生用品"
- 如果建议带登山杖、GPS等，请归类到 "导航工具"
- 如果建议带急救包、手电筒等，请归类到 "安全装备"
- 如果建议带其他未明确列出的物品，请归类到 "其他"

## 零幻觉原则
- 仅基于上述已知信息生成计划
- 如果某些数据缺失（如无周边救援数据），请报告数据不足，严禁编造数据
- 不要捏造轨迹指标、天气数据或救援电话

请确保输出完全符合 OutdoorActivityPlan 的 JSON Schema。
"""
        return prompt