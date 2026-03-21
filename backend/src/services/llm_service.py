"""
LLM 服务
========

封装大模型调用逻辑。
"""

import json
from datetime import datetime

import requests
from loguru import logger

from src.schemas.output import OutdoorActivityPlan, PlanningContext
from src.api.config import api_config
from src.prompts import get_system_prompt, get_user_prompt


class LLMService:
    """大模型服务"""

    def __init__(self):
        """初始化服务"""
        self.config = api_config

    def generate_plan(
        self,
        context: PlanningContext,
        track_overview: str,
        weather_overview: str,
        transport_overview: str
    ) -> OutdoorActivityPlan:
        """
        生成户外活动计划

        Args:
            context: 规划上下文
            track_overview: 轨迹概述
            weather_overview: 天气概述
            transport_overview: 交通概述

        Returns:
            OutdoorActivityPlan: 生成的户外活动计划
        """
        logger.info("开始 LLM 提炼与生成")

        # 生成计划ID
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 构建 LLM 提示词
        llm_prompt = self._build_prompt(context)

        # 调用 LLM API
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

    def _build_prompt(self, context: PlanningContext) -> str:
        """构建 LLM 提示词"""
        # 准备轨迹分析信息
        track_info = {
            "total_distance_km": context.track_analysis_raw.total_distance_km,
            "total_ascent_m": context.track_analysis_raw.total_ascent_m,
            "total_descent_m": context.track_analysis_raw.total_descent_m,
            "difficulty_level": context.track_analysis_raw.difficulty_level,
            "weather_condition": context.weather_raw.summary.conditions if context.weather_raw and context.weather_raw.summary else '未知',
            "transport_route": context.transport_raw.summary.total_distance if context.transport_raw and context.transport_raw.summary else '未知'
        }

        # 准备24小时逐小时天气数据
        hourly_weather_data = ""
        if context.weather_raw and context.weather_raw.hourly_24h and context.weather_raw.hourly_24h.hourly:
            for hour in context.weather_raw.hourly_24h.hourly:
                time_str = hour.fxTime.split('T')[1][:5] if 'T' in hour.fxTime else hour.fxTime
                hourly_weather_data += f"- {time_str}: 温度{hour.temp}°C, 降水概率{hour.pop}%, 降水量{hour.precip}mm, 风力{hour.windScale}级\n"

        # 准备多抽样点格点天气数据
        grid_points_data = ""
        if context.weather_raw and context.weather_raw.grid_points:
            for point in context.weather_raw.grid_points:
                grid_points_data += f"- **{point['point_type']}**: 温度{point['temp']}°C, 风力{point['wind_scale']}级, 湿度{point['humidity']}%\n"

        # 准备搜索结果数据
        search_content = self._format_search_results(context)

        # 准备周边救援数据
        rescue_content = self._format_rescue_data(context)

        # 使用提示词管理器生成最终提示词
        prompt = get_user_prompt(
            raw_request=context.raw_request,
            additional_info=context.additional_info,
            track_info=track_info,
            hourly_weather_data=hourly_weather_data,
            grid_points_data=grid_points_data,
            search_content=search_content,
            rescue_content=rescue_content
        )

        return prompt

    def _format_search_results(self, context: PlanningContext) -> str:
        """格式化搜索结果"""
        scenic_results = []
        rescue_results = []
        guide_results = []
        equipment_results = []

        for search_response in context.search_raw:
            query = search_response.query.lower()
            for result in search_response.results:
                result_info = f"- {result.title}: {result.content[:150]}..."

                if '景点' in query or '景区' in query or '旅游' in query:
                    scenic_results.append(result_info)
                elif '救援' in query or '蓝天' in query or '应急' in query:
                    rescue_results.append(result_info)
                elif '攻略' in query or '路线' in query or '注意事项' in query:
                    guide_results.append(result_info)
                elif '装备' in query or '登山' in query or '露营' in query:
                    equipment_results.append(result_info)

        search_content = ""
        if scenic_results:
            search_content += "### 周边景区/景点\n" + "\n".join(scenic_results[:5]) + "\n"
        if rescue_results:
            search_content += "### 应急救援信息（Web搜索）\n" + "\n".join(rescue_results[:5]) + "\n"
        if guide_results:
            search_content += "### 徒步攻略参考\n" + "\n".join(guide_results[:5]) + "\n"
        if equipment_results:
            search_content += "### 装备推荐参考\n" + "\n".join(equipment_results[:5]) + "\n"

        return search_content

    def _format_rescue_data(self, context: PlanningContext) -> str:
        """格式化周边救援数据"""
        if not context.around_rescue_data:
            return "无（10km范围内未搜索到医院/派出所，请使用 Web 搜索结果或通用报警电话）\n"

        rescue_content = f"**精准位置**: {context.precise_location_name}\n\n"

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
            rescue_content += "### 周边医院/诊所\n" + "\n".join(hospitals[:10]) + "\n"
        if police:
            rescue_content += "### 周边派出所/公安局\n" + "\n".join(police[:5]) + "\n"

        rescue_content += "\n**重要提示**：以上数据来自高德地图 API，是轨迹起点周边的真实救援设施，请优先将这些电话填入 emergency_rescue_contacts。\n"

        return rescue_content

    def _call_llm_api(
        self,
        prompt: str,
        plan_id: str,
        track_overview: str,
        weather_overview: str,
        transport_overview: str,
        context: PlanningContext
    ) -> OutdoorActivityPlan:
        """调用 LLM API 生成户外活动计划"""
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.LLM_API_KEY}"
        }

        # 使用提示词管理器获取系统提示词
        system_prompt = get_system_prompt()
        logger.debug(f"系统提示词长度: {len(system_prompt)} 字符")

        # 构建请求体（使用配置化参数）
        payload = {
            "model": self.config.LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.LLM_TEMPERATURE,
            "max_tokens": self.config.LLM_MAX_TOKENS,
            "response_format": {"type": "json_object"}
        }

        # 发送请求（使用配置的超时时间）
        response = requests.post(
            self.config.LLM_BASE_URL,
            headers=headers,
            json=payload,
            timeout=self.config.LLM_TIMEOUT,
            proxies=self.config.PROXY if self.config.should_use_proxy() else None
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

        # 使用用户输入的线路名称作为计划书标题
        if context.plan_title and context.plan_title.strip():
            plan_data["plan_name"] = context.plan_title.strip()

        # 确保 overview 字段使用我们生成的版本
        plan_data["track_overview"] = track_overview
        plan_data["weather_overview"] = weather_overview
        plan_data["transport_overview"] = transport_overview

        # 填充轨迹详细分析数据
        self._fill_track_detail(plan_data, context)

        # 填充交通方案详情
        if context.transport_raw and context.transport_raw.outbound:
            plan_data["transport_scheme"] = context.transport_raw.model_dump()

        # 转换为 Pydantic 模型
        return OutdoorActivityPlan(**plan_data)

    def _fill_track_detail(self, plan_data: dict, context: PlanningContext):
        """填充轨迹详细分析数据"""
        from src.schemas.output import TrackDetailAnalysis, TerrainSegment, ElevationPoint

        track_raw = context.track_analysis_raw
        if not track_raw:
            return

        # 转换地形分析数据
        terrain_segments = []
        for seg in track_raw.terrain_analysis:
            terrain_segments.append(TerrainSegment(
                change_type=seg.change_type,
                elevation_diff=round(seg.elevation_diff, 1),
                distance_m=round(seg.distance_m, 1),
                gradient_percent=round(seg.gradient_percent, 1),
                start_distance_m=round(getattr(seg, 'start_distance_m', 0), 1)
            ))

        # 转换海拔轨迹点数据
        elevation_points = []
        for pt in track_raw.elevation_points:
            elevation_points.append(ElevationPoint(
                distance_m=round(pt.distance_m, 1),
                elevation_m=round(pt.elevation_m, 1),
                is_key_point=pt.is_key_point,
                label=pt.label
            ))

        # 创建轨迹详细分析
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
            elevation_points=elevation_points,
        )
        plan_data["track_detail"] = track_detail.model_dump()
