"""
报告生成工具
============

提供完整的户外活动计划生成功能。
"""

from typing import List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.domain.orchestrator import OutdoorPlannerRouter


# 模块级缓存，用于存储最新生成的计划
_latest_plan = [None]


class ReportGenerateInput(BaseModel):
    """报告生成输入参数"""
    trip_date: str = Field(
        ...,
        description="出行日期，格式：YYYY-MM-DD，例如：2025-05-01"
    )
    departure_point: str = Field(
        ...,
        description="出发地点（文字地址），例如：北京市朝阳区国贸"
    )
    gpx_path: str = Field(
        ...,
        description="GPX/KML 轨迹文件的绝对路径，例如：/path/to/track.gpx"
    )
    plan_title: str = Field(
        default="",
        description="线路名称/计划书标题（可选），例如：香山一日游"
    )
    key_destinations: List[str] = Field(
        default_factory=list,
        description="核心目的地列表（可选），用于搜索关键词，例如：['香山', '碧云寺']"
    )
    additional_info: str = Field(
        default="",
        description="补充信息（可选），例如：计划8点出发，希望中午到达山顶野餐"
    )


@tool("report_generate", args_schema=ReportGenerateInput)
def report_generate(
    trip_date: str,
    departure_point: str,
    gpx_path: str,
    plan_title: str = "",
    key_destinations: Optional[List[str]] = None,
    additional_info: str = ""
) -> str:
    """
    生成完整的户外活动计划报告。

    该工具会执行完整的数据采集和计划生成流程：
    1. 轨迹解析（距离、爬升、难度）
    2. 坐标纠偏（WGS84 -> GCJ02）
    3. 天气查询（格点天气、多抽样点）
    4. 交通路线规划（驾车、公交）
    5. 网络搜索（景点、救援、攻略、装备）
    6. LLM 生成完整计划（概述、行程、装备、安全等）

    这是核心工具，会调用所有其他服务生成最终报告。

    Args:
        trip_date: 出行日期 (YYYY-MM-DD)
        departure_point: 出发地点
        gpx_path: GPX/KML 轨迹文件路径
        plan_title: 线路名称（可选）
        key_destinations: 核心目的地列表（可选）
        additional_info: 补充信息（可选）

    Returns:
        str: 格式化的户外活动计划摘要字符串
    """
    try:
        # 处理默认参数
        if key_destinations is None:
            key_destinations = []

        # 创建规划器实例
        router = OutdoorPlannerRouter()

        # 执行完整规划流程
        plan = router.execute_planning(
            trip_date=trip_date,
            departure_point=departure_point,
            additional_info=additional_info,
            gpx_path=gpx_path,
            plan_title=plan_title,
            key_destinations=key_destinations
        )

        # 缓存计划（供后续 API 查询）
        _latest_plan[0] = plan

        # 格式化输出
        output_parts = [
            "=== 户外活动计划报告 ===",
            f"",
            f"计划名称: {plan.plan_title or '未命名'}",
            f"生成时间: {plan.generated_at}",
            f"可信度评分: {plan.confidence_score:.0%}",
            f"",
            "=== 计划概述 ===",
            f"活动类型: {plan.activity_type}",
            f"难度等级: {plan.difficulty_level}",
            f"预计时长: {plan.estimated_duration}",
            f"最佳季节: {plan.best_season}",
            f"",
            plan.overview,
            f"",
            "=== 轨迹信息 ==="
        ]

        # 添加轨迹详情
        if plan.track_detail:
            td = plan.track_detail
            output_parts.extend([
                f"总里程: {td.total_distance} 公里",
                f"总爬升: {td.total_ascent} 米",
                f"总下降: {td.total_descent} 米",
                f"最高海拔: {td.max_elevation} 米",
                f"最低海拔: {td.min_elevation} 米",
                f"平均海拔: {td.avg_elevation} 米",
                f"预计用时: {td.estimated_duration} 小时",
                f"难度评分: {td.difficulty_score}/100",
                f"安全风险: {td.safety_risk}"
            ])

            # 云海指数
            if td.cloud_sea_assessment:
                csa = td.cloud_sea_assessment
                output_parts.extend([
                    f"",
                    f"云海指数: {csa.score}/10 ({csa.level})",
                    f"影响因素: {', '.join(csa.factors) if csa.factors else '无'}"
                ])

        output_parts.append("")

        # 添加天气信息
        if plan.weather_forecast:
            wf = plan.weather_forecast
            output_parts.extend([
                "=== 天气预报 ===",
                f"出行日期天气: {wf.conditions}",
                f"温度范围: {wf.temp_min}°C ~ {wf.temp_max}°C",
                f"降水概率: {wf.precip_prob}%",
                f"风力: {wf.wind}",
                f"风险等级: {wf.risk_level}",
                f"建议: {wf.recommendation}",
                f""
            ])

        # 添加交通信息
        if plan.transportation:
            trans = plan.transportation
            output_parts.extend([
                "=== 交通信息 ===",
                f"出发地: {trans.origin}",
                f"目的地: {trans.destination}",
                f"推荐方式: {trans.recommended_mode}",
                f"最快方式: {trans.fastest_mode}",
                f"费用: {trans.cost_estimate}",
                f""
            ])

        # 添加行程安排
        if plan.itinerary and len(plan.itinerary) > 0:
            output_parts.append("=== 行程安排 ===")
            for i, item in enumerate(plan.itinerary, 1):
                time_str = f"{item.time}" if hasattr(item, 'time') else f"阶段{i}"
                activity_str = item.activity if hasattr(item, 'activity') else str(item)
                output_parts.append(f"{time_str}: {activity_str}")
            output_parts.append("")

        # 添加装备建议
        if plan.equipment and len(plan.equipment) > 0:
            output_parts.extend([
                "=== 装备建议 ===",
                f"必带装备: {', '.join(plan.equipment[:5])}",
                f"建议装备: {', '.join(plan.equipment[5:10]) if len(plan.equipment) > 5 else ''}",
                f""
            ])

        # 添加安全提示
        if plan.safety_tips and len(plan.safety_tips) > 0:
            output_parts.extend([
                "=== 安全提示 ===",
                *plan.safety_tips[:5],
                f""
            ])

        # 添加紧急联系
        if plan.emergency_contacts:
            output_parts.extend([
                "=== 紧急联系 ===",
                *plan.emergency_contacts,
                f""
            ])

        output_parts.append("=== 报告生成完成 ===")

        return "\n".join(output_parts)

    except Exception as e:
        return f"错误: 报告生成失败 - {str(e)}"


def get_latest_plan():
    """
    获取最新生成的计划对象。

    Returns:
        OutdoorActivityPlan: 最新的户外活动计划对象，如果不存在则返回 None
    """
    return _latest_plan[0]
