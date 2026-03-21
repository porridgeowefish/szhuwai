"""
主控大脑 (Orchestrator)
====================

户外活动规划的主控制器，协调各个服务，实现核心的规划流程。
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from src.schemas.base import Point3D
from src.schemas.output import (
    OutdoorActivityPlan,
    PlanningContext,
    CloudSeaAssessment
)
from src.schemas.weather import WeatherSummary
from src.schemas.track import TrackAnalysisResult
from src.schemas.transport import TransportRoutes
from src.schemas.search import WebSearchResponse

# 导入服务层
from src.services.track_service import TrackService
from src.services.weather_service import WeatherService
from src.services.transport_service import TransportService
from src.services.search_service import SearchService
from src.services.llm_service import LLMService
from src.services.weather_analyzer import WeatherAnalyzer


class OutdoorPlannerRouter:
    """户外活动规划主控器"""

    def __init__(self):
        """初始化规划器"""
        # 初始化服务
        self.track_service = TrackService()
        self.weather_service = WeatherService()
        self.transport_service = TransportService()
        self.search_service = SearchService()
        self.llm_service = LLMService()
        self.weather_analyzer = WeatherAnalyzer()

        # 关键点（存储轨迹解析后的重要位置）
        self.key_points: Dict[str, Point3D] = {}

    def execute_planning(
        self,
        trip_date: str,
        departure_point: str,
        additional_info: str,
        gpx_path: str,
        plan_title: str = "",
        key_destinations: List[str] = None
    ) -> OutdoorActivityPlan:
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
        if key_destinations is None:
            key_destinations = []

        # 步骤 1: 轨迹解析
        track_analysis = self.track_service.analyze(gpx_path)
        if not track_analysis:
            raise ValueError("无法解析轨迹文件，规划终止")

        # 步骤 2: 坐标纠偏
        self.key_points = self.track_service.correct_coordinates(track_analysis)

        # 步骤 3: 提取坐标真理
        start_point = track_analysis.start_point
        if not start_point:
            raise ValueError("轨迹解析成功但无法获取起点坐标，规划终止")

        destination_coord = f"{start_point.lon},{start_point.lat}"
        logger.info(f"提取到轨迹目的地坐标: {destination_coord}")

        # 步骤 4: 并发数据获取
        weather_data, transport_data, search_data, precise_location_name, around_rescue_data = self._gather_data_concurrently(
            track_analysis=track_analysis,
            trip_date=trip_date,
            departure_point=departure_point,
            destination_coord=destination_coord,
            additional_info=additional_info,
            plan_title=plan_title,
            key_destinations=key_destinations
        )

        # 步骤 5: 上下文组装
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
            plan_title=plan_title,
            key_destinations=key_destinations
        )

        # 步骤 6: LLM 生成
        plan = self._llm_synthesis(context)

        # 步骤 7: 计算云海指数
        self._calculate_cloud_sea(plan, context)

        return plan

    def _gather_data_concurrently(
        self,
        track_analysis: TrackAnalysisResult,
        trip_date: str,
        departure_point: str,
        destination_coord: str,
        additional_info: str,
        plan_title: str = "",
        key_destinations: List[str] = None
    ) -> Tuple[Optional[WeatherSummary], Optional[TransportRoutes], List[WebSearchResponse], str, List[Dict]]:
        """
        使用线程池并发获取数据
        """
        logger.info("开始并发获取数据（基于轨迹坐标）")

        if key_destinations is None:
            key_destinations = []

        # 获取纠偏后的起点坐标
        gcj_lon, gcj_lat = self._get_gcj02_coords(track_analysis)

        # 获取逆地理编码
        precise_location_name = self.transport_service.get_reverse_geocode(gcj_lon, gcj_lat)
        if not precise_location_name:
            precise_location_name = track_analysis.track_name or "户外徒步"
        logger.info(f"轨迹位置精准地名: {precise_location_name}")

        # 构建搜索关键词
        search_keywords = " ".join(key_destinations) if key_destinations else (plan_title or "户外徒步")
        logger.info(f"搜索关键词（基于用户输入）: {search_keywords}")

        # 定义并发任务
        def fetch_weather():
            """获取天气数据"""
            try:
                start = track_analysis.start_point

                # 获取额外抽样点
                additional_points = []
                if track_analysis.max_elev_point:
                    additional_points.append((
                        track_analysis.max_elev_point.lon,
                        track_analysis.max_elev_point.lat,
                        "最高点"
                    ))
                if track_analysis.end_point:
                    additional_points.append((
                        track_analysis.end_point.lon,
                        track_analysis.end_point.lat,
                        "终点"
                    ))
                # 中点
                if hasattr(track_analysis, 'track_points') and track_analysis.track_points and len(track_analysis.track_points) > 10:
                    mid_idx = len(track_analysis.track_points) // 2
                    mid_point = track_analysis.track_points[mid_idx]
                    additional_points.append((mid_point.lon, mid_point.lat, "中点"))

                return self.weather_service.get_summary(
                    lon=start.lon,
                    lat=start.lat,
                    trip_date=trip_date,
                    include_hourly=True,
                    include_multi_point=True,
                    additional_points=additional_points
                )
            except Exception as e:
                logger.error(f"获取天气数据失败: {e}")
                return None

        def fetch_transport():
            """获取交通路线"""
            try:
                return self.transport_service.plan(departure_point, destination_coord)
            except Exception as e:
                logger.error(f"获取交通路线失败: {e}")
                return None

        def fetch_search():
            """执行搜索"""
            try:
                return self.search_service.search(search_keywords)
            except Exception as e:
                logger.error(f"搜索失败: {e}")
                return []

        def fetch_around_rescue():
            """获取周边救援数据"""
            try:
                return self.transport_service.search_around_rescue(gcj_lon, gcj_lat)
            except Exception as e:
                logger.error(f"周边救援搜索失败: {e}")
                return []

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
                        if result:
                            search_data = result if isinstance(result, list) else [result]
                    elif name == "around_rescue":
                        around_rescue_data = result if result else []
                except Exception as e:
                    logger.error(f"并发任务 {name} 执行失败: {e}")

        logger.info(f"数据获取完成: 搜索结果={len(search_data)}组, 救援点={len(around_rescue_data)}个")
        return weather_data, transport_data, search_data, precise_location_name, around_rescue_data

    def _get_gcj02_coords(self, track_analysis: TrackAnalysisResult) -> Tuple[float, float]:
        """获取纠偏后的坐标"""
        if 'start' in self.key_points:
            return self.key_points['start'].lon, self.key_points['start'].lat
        elif track_analysis.start_point:
            return track_analysis.start_point.lon, track_analysis.start_point.lat
        raise ValueError("无法获取起点坐标")

    def _assemble_context(
        self,
        user_request: str,
        track_analysis: Optional[TrackAnalysisResult],
        weather_data: Optional[WeatherSummary],
        transport_data: Optional[TransportRoutes],
        search_data: List[WebSearchResponse],
        additional_info: str = "",
        precise_location_name: str = "",
        around_rescue_data: List[Dict] = None,
        plan_title: str = "",
        key_destinations: List[str] = None
    ) -> PlanningContext:
        """组装规划上下文"""
        logger.info("组装规划上下文")

        confidence_score = self._calculate_confidence_score(
            track_analysis, weather_data, transport_data
        )

        context = PlanningContext(
            raw_request=user_request,
            additional_info=additional_info,
            precise_location_name=precise_location_name,
            plan_title=plan_title,
            key_destinations=key_destinations or [],
            track_analysis_raw=track_analysis or self._create_empty_track(),
            weather_raw=weather_data or self._create_empty_weather(),
            transport_raw=transport_data or self._create_empty_transport(),
            search_raw=search_data,
            around_rescue_data=around_rescue_data or [],
            confidence_score=confidence_score
        )

        logger.info("上下文组装完成")
        return context

    def _llm_synthesis(self, context: PlanningContext) -> OutdoorActivityPlan:
        """LLM 提炼与实例化"""
        logger.info("开始 LLM 提炼与生成")

        # 生成概述
        track_overview = self._generate_track_overview(context.track_analysis_raw)
        weather_overview = self._generate_weather_overview(context.weather_raw)
        transport_overview = self._generate_transport_overview(context.transport_raw)

        # 调用 LLM 服务
        plan = self.llm_service.generate_plan(
            context=context,
            track_overview=track_overview,
            weather_overview=weather_overview,
            transport_overview=transport_overview
        )

        logger.info("LLM 提炼完成")
        return plan

    def _calculate_cloud_sea(self, plan: OutdoorActivityPlan, context: PlanningContext):
        """计算云海指数"""
        try:
            if context.weather_raw and context.weather_raw.forecast_3d:
                daily_list = context.weather_raw.forecast_3d.daily
                if daily_list and len(daily_list) > 0:
                    city_weather = daily_list[0]

                    # 查找最高点天气
                    summit_weather = None
                    if context.weather_raw.grid_points:
                        for pt in context.weather_raw.grid_points:
                            if pt.get("point_type") == "最高点":
                                summit_weather = type('SummitWeather', (), {
                                    'tempMin': pt.get("temp", 20),
                                    'humidity': pt.get("humidity", 50),
                                    'windSpeedDay': 0
                                })()
                                break

                    if summit_weather:
                        cloud_sea_result = self.weather_analyzer.calculate_cloud_sea_probability(
                            city_weather, summit_weather
                        )

                        assessment = cloud_sea_result.get("assessment", "一般")
                        probability = cloud_sea_result.get("probability", 0)
                        factors = []
                        if cloud_sea_result.get("conditions", {}).get("high_humidity"):
                            factors.append("高湿度")
                        if cloud_sea_result.get("conditions", {}).get("low_wind"):
                            factors.append("低风速")
                        if cloud_sea_result.get("conditions", {}).get("inversion_layer"):
                            factors.append("逆温层")

                        score = round(probability / 10)

                        if plan.track_detail:
                            plan.track_detail.cloud_sea_assessment = CloudSeaAssessment(
                                score=score,
                                level=assessment,
                                factors=factors
                            )
                        logger.info(f"云海指数计算完成: {assessment}, 分数={score}")
        except Exception as e:
            logger.warning(f"计算云海指数失败: {e}")

    def _calculate_confidence_score(self, track_analysis, weather_data, transport_data) -> float:
        """计算方案可信度评分"""
        score = 0.5

        if track_analysis and track_analysis.total_distance_km > 0:
            score += 0.2
            if track_analysis.total_distance_km > 5:
                score += 0.1

        if weather_data:
            score += 0.2

        if transport_data:
            score += 0.1

        return min(score, 1.0)

    def _create_empty_track(self) -> TrackAnalysisResult:
        """创建空的轨迹分析结果"""
        from src.schemas.base import Point3D
        default_point = Point3D(lon=116.4, lat=39.9, elevation=100)

        return TrackAnalysisResult(
            track_name="未知",
            total_distance_km=0.1,
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
            estimated_duration_hours=0.1,
            safety_risk="低风险",
            track_points_count=1
        )

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
            origin=LocationInfo(address="未知起点", lat=0, lon=0, city="未知"),
            destination=LocationInfo(address="未知终点", lat=0, lon=0, city="未知"),
            outbound={},
            return_route={},
            summary=RouteSummary()
        )

    def _generate_track_overview(self, track_analysis) -> str:
        """生成轨迹概述"""
        if not track_analysis:
            return "无轨迹数据"
        return f"{track_analysis.total_distance_km:.1f}km/爬升{track_analysis.total_ascent_m:.1f}m"

    def _generate_weather_overview(self, weather_data) -> str:
        """生成天气概述"""
        if not weather_data:
            return "无天气数据"

        conditions = weather_data.summary.conditions or "未知"

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

        return f"{conditions}，温度信息不可用"

    def _generate_transport_overview(self, transport_data) -> str:
        """生成交通概述"""
        if not transport_data:
            return "交通信息不可用"

        if transport_data.summary.total_distance and transport_data.summary.total_time:
            cost_info = f"，{transport_data.summary.cost}" if transport_data.summary.cost else ""
            return f"驾车{transport_data.summary.total_distance}，约{transport_data.summary.total_time}{cost_info}"

        if transport_data.outbound and "driving" in transport_data.outbound:
            driving = transport_data.outbound["driving"]
            distance_km = driving.get("distance_km", 0)
            duration_min = driving.get("duration_min", 0)
            tolls = driving.get("tolls_yuan", 0)
            cost_str = f"，过路费{tolls}元" if tolls > 0 else ""
            return f"驾车{distance_km:.1f}公里，约{duration_min}分钟{cost_str}"

        if transport_data.recommended_mode:
            return f"建议{transport_data.recommended_mode}"

        return "交通信息不可用"
