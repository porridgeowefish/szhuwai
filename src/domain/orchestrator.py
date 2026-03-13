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
    SafetyAssessment,
    EmergencyRescueContact,
    ScenicSpot,
    EquipmentItem,
    ItineraryItem,
    GridPointWeather,
    EquipmentCategory
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

    def execute_planning(self, user_request: str, gpx_path: str = None) -> OutdoorActivityPlan:
        """
        执行户外活动规划主流程

        Args:
            user_request: 用户原始请求
            gpx_path: GPX 轨迹文件路径（可选）

        Returns:
            OutdoorActivityPlan: 最终的户外活动计划
        """
        # 步骤 1: 轨迹解析
        track_analysis = self._parse_track(gpx_path)

        # 步骤 2: 坐标纠偏
        if track_analysis:
            self._coordinate_correction(track_analysis)

        # 步骤 3: 并发数据获取
        weather_data, transport_data, search_data = self._gather_data_concurrently(
            track_analysis=track_analysis,
            user_request=user_request
        )

        # 步骤 4: 上下文组装
        context = self._assemble_context(
            user_request=user_request,
            track_analysis=track_analysis,
            weather_data=weather_data,
            transport_data=transport_data,
            search_data=search_data
        )

        # 步骤 5: LLM 提炼与实例化
        return self._llm_synthesis(context)

    def _parse_track(self, gpx_path: str = None) -> Optional[TrackAnalysisResult]:
        """
        步骤 1: 轨迹解析
        """
        if not gpx_path or not Path(gpx_path).exists():
            logger.warning("未提供 GPX 文件或文件不存在，将根据请求关键词规划")
            return None

        try:
            logger.info(f"开始解析轨迹文件: {gpx_path}")
            track_analysis = self.track_parser.parse_file(gpx_path)
            logger.info(f"轨迹解析完成: 总距离 {track_analysis.total_distance_km:.2f}km, "
                       f"爬升 {track_analysis.total_ascent_m}m, 下降 {track_analysis.total_descent_m}m")
            return track_analysis
        except Exception as e:
            logger.error(f"轨迹解析失败: {e}")
            return None

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

    def _gather_data_concurrently(self, track_analysis: Optional[TrackAnalysisResult],
                                user_request: str) -> Tuple[Optional[WeatherSummary], Optional[TransportRoutes], List[WebSearchResponse]]:
        """
        步骤 3: 使用线程池并发调用 API 客户端获取数据
        """
        logger.info("开始并发获取数据")

        # 准备获取位置信息
        location = None
        if track_analysis and self.key_points.get('start'):
            location = f"{self.key_points['start'].lat:.4f},{self.key_points['start'].lon:.4f}"
        elif track_analysis:
            # 如果没有关键点，使用起点
            if track_analysis.start_point:
                location = f"{track_analysis.start_point.lat:.4f},{track_analysis.start_point.lon:.4f}"

        # 构建搜索查询（自动追加安全关键词）
        search_query = f"{user_request} 户外安全 应急救援 报警电话 急救电话"

        # 定义获取函数
        def fetch_weather():
            if location:
                try:
                    return self.weather_client.get_weather_summary(location, user_request)
                except Exception as e:
                    logger.error(f"获取天气数据失败: {e}")
                    return None
            return None

        def fetch_transport():
            if location:
                try:
                    start = self.key_points.get('start')
                    end = self.key_points.get('end')
                    if start and end:
                        return self.map_client.get_driving_route(
                            start.lat, start.lon,
                            end.lat, end.lon
                        )
                except Exception as e:
                    logger.error(f"获取路线数据失败: {e}")
                    return None
            return None

        def fetch_search():
            try:
                return self.search_client.search(search_query, max_results=10)
            except Exception as e:
                logger.error(f"搜索失败: {e}")
                return []

        # 使用线程池并发执行
        weather_data = None
        transport_data = None
        search_data = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_name = {
                executor.submit(fetch_weather): "weather",
                executor.submit(fetch_transport): "transport",
                executor.submit(fetch_search): "search"
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
                        search_data = result
                except Exception as e:
                    logger.error(f"并发任务 {name} 执行失败: {e}")

        logger.info("数据获取完成")
        return weather_data, transport_data, search_data

    def _assemble_context(self, user_request: str,
                         track_analysis: Optional[TrackAnalysisResult],
                         weather_data: Optional[WeatherSummary],
                         transport_data: Optional[TransportRoutes],
                         search_data: List[WebSearchResponse]) -> PlanningContext:
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
            track_analysis_raw=track_analysis or self._create_empty_track(),
            weather_raw=weather_data or self._create_empty_weather(),
            transport_raw=transport_data or self._create_empty_transport(),
            search_raw=search_data,
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

        # 调用 LLM API 生成计划
        try:
            plan = self._call_llm_api(
                prompt=llm_prompt,
                plan_id=plan_id,
                track_overview=track_overview,
                weather_overview=weather_overview,
                transport_overview=transport_overview,
                context=context
            )
        except Exception as e:
            logger.error(f"LLM API 调用失败: {e}，使用备用方案")
            # 如果 LLM 调用失败，使用 mock 计划
            plan = self._create_mock_plan(
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
        # 使用 Qwen/Qwen2.5-7B-Instruct 模型（性价比较高）
        payload = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
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
        {"point_type": "起点|终点|最高点", "temp": 18, "wind_scale": "2", "humidity": 65}
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

        # 确保 overview 字段使用我们生成的版本
        plan_data["track_overview"] = track_overview
        plan_data["weather_overview"] = weather_overview
        plan_data["transport_overview"] = transport_overview

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
        """生成轨迹概述"""
        if not track_analysis:
            return "无轨迹数据"

        distance_km = track_analysis.total_distance_km
        return f"{distance_km:.1f}km/爬升{track_analysis.total_ascent_m}m/下降{track_analysis.total_descent_m}m"

    def _generate_weather_overview(self, weather_data) -> str:
        """生成天气概述"""
        if not weather_data:
            return "无天气数据"

        # 从 summary.conditions 获取天气状况描述
        conditions = weather_data.summary.conditions or "未知"

        # 从 7天预报中取第一天的数据（如果有）
        if weather_data.forecast_7d and weather_data.forecast_7d.daily:
            forecast = weather_data.forecast_7d.daily[0]
            temp_range = f"{forecast.tempMin}~{forecast.tempMax}°C"
            precip = f"降水{forecast.precip}%"
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
            return f"{transport_data.summary.total_distance}，{transport_data.summary.total_time}"

        # 使用推荐的交通方式
        if transport_data.recommended_mode:
            return f"建议{transport_data.recommended_mode}"

        return "交通信息不可用"

    def _build_llm_prompt(self, context: PlanningContext) -> str:
        """构建 LLM 提示"""
        prompt = f"""
请根据以下户外活动规划信息，生成一个详细的户外活动计划：

## 用户原始请求
{context.raw_request}

## 轨迹分析信息
- 总距离：{context.track_analysis_raw.total_distance_km:.1f}公里
- 总爬升：{context.track_analysis_raw.total_ascent_m}米
- 总下降：{context.track_analysis_raw.total_descent_m}米
- 难度：{context.track_analysis_raw.difficulty_level}
- 天气条件：{context.weather_raw.summary.conditions if context.weather_raw else '未知'}
- 交通路线：{context.transport_raw.summary.total_distance if context.transport_raw else '未知'}

## 安全提示信息
从搜索结果中获取了以下安全相关信息：
"""

        for search_response in context.search_raw:
            for result in search_response.results:
                if '救援' in result.title or '急救' in result.title or '安全' in result.title:
                    prompt += f"- {result.title}: {result.content[:200]}...\n"

        prompt += """
请按照 OutdoorActivityPlan 的结构化输出格式，生成一个完整的户外活动计划，包括：
1. 基础信息（计划ID、创建时间、计划名称、推荐等级）
2. 轨迹概述、天气概述、交通概述
3. 天气数据（当天详细天气、逐小时天气、关键格点天气）
4. 行程安排、装备建议、风景点推荐
5. 注意事项、安全评估、安全风险点、风险因素标签
6. 应急救援电话

## 重要约束条件

关于装备建议 (equipment_recommendations)：
请注意，装备的 `category` 字段必须且只能从以下列表中选择：
['服装', '鞋类', '背包', '露营装备', '炊具', '安全装备', '导航工具', '卫生用品', '电子产品', '其他']。

绝对不允许创造新的分类！例如：
- 如果建议带防晒霜、护肤品、面霜等，请归类到 "卫生用品"
- 如果建议带登山杖、GPS等，请归类到 "导航工具"
- 如果建议带急救包、手电筒等，请归类到 "安全装备"
- 如果建议带其他未明确列出的物品，请归类到 "其他"

请确保输出完全符合 OutdoorActivityPlan 的 JSON Schema。
"""
        return prompt

    def _create_mock_plan(self, plan_id: str, track_overview: str,
                         weather_overview: str, transport_overview: str,
                         context: PlanningContext) -> OutdoorActivityPlan:
        """创建示例计划（仅用于演示）"""
        # 这里应该调用真实的 LLM API
        # 临时返回一个示例计划

        # 模拟生成当天的天气
        from src.schemas.weather import CityWeatherDaily, HourlyWeather

        # 模拟风景点
        scenic_spots = [
            ScenicSpot(
                name="观景台",
                description="俯瞰整个山谷的绝佳位置",
                location=Point3D(lon=116.4, lat=39.9, elevation=1000),
                best_view_time="10:00-14:00",
                photo_spots=["东面观景点", "西面观景点"],
                difficulty="中等",
                estimated_visit_time_min=30
            )
        ]

        # 模拟装备建议
        equipment = [
            EquipmentItem(
                name="登山包",
                category=EquipmentCategory.BACKPACK,
                priority="必需",
                quantity=1,
                weight_kg=3,
                description="30L以上的登山背包",
                alternatives=["户外背包"]
            ),
            EquipmentItem(
                name="防晒霜",
                category=EquipmentCategory.HYGIENE,
                priority="推荐",
                quantity=1,
                weight_kg=0.2,
                description="防晒指数SPF50+",
                alternatives=["防晒喷雾"]
            )
        ]

        # 模拟行程安排
        itinerary = [
            ItineraryItem(
                time="08:00",
                activity="集合出发",
                location="停车场",
                duration_minutes=30,
                notes="检查装备，分发路餐"
            )
        ]

        return OutdoorActivityPlan(
            plan_id=plan_id,
            created_at=datetime.now(),
            plan_name=f"户外徒步计划 - {datetime.now().strftime('%m-%d')}",
            overall_rating="推荐",
            track_overview=track_overview,
            weather_overview=weather_overview,
            transport_overview=transport_overview,
            trip_date_weather=CityWeatherDaily(
                fxDate=datetime.now().strftime('%Y-%m-%d'),
                tempMax=25,
                tempMin=15,
                textDay="晴",
                windScaleDay="3",
                windSpeedDay=10,
                humidity=50,
                precip=0,
                pressure=1013,
                uvIndex=8,
                vis=20
            ),
            hourly_weather=[
                HourlyWeather(
                    fxTime="2024-03-13T08:00:00",
                    temp=18,
                    pop=0,
                    precip=0,
                    windScale="2"
                )
            ],
            critical_grid_weather=[
                GridPointWeather(
                    point_type="起点",
                    temp=18,
                    wind_scale="2",
                    humidity=65
                )
            ],
            itinerary=itinerary,
            equipment_recommendations=equipment,
            scenic_spots=scenic_spots,
            precautions=["注意防晒", "携带足够的水", "注意安全"],
            safety_assessment=SafetyAssessment(
                overall_risk="低风险",
                conditions="天气良好，路线清晰",
                recommendation="推荐",
                risk_level="低风险"
            ),
            safety_issues=[],
            risk_factors=[],
            emergency_rescue_contacts=[
                EmergencyRescueContact(
                    name="公安报警",
                    phone="110",
                    type="报警"
                ),
                EmergencyRescueContact(
                    name="急救中心",
                    phone="120",
                    type="医疗"
                )
            ]
        )