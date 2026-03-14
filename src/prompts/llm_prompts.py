"""
LLM 提示词管理
==============

管理户外活动规划的大模型提示词。
"""

from typing import Optional, Dict, Any, List


class LLMPromptManager:
    """LLM 提示词管理器"""

    # 系统提示词模板
    SYSTEM_PROMPT_TEMPLATE = """你是一个专业的户外活动规划助手。根据用户请求和收集到的数据（轨迹、天气、交通、安全信息），生成一个结构化的户外活动计划。

请严格按照以下 JSON 格式输出户外活动计划，确保所有字段都正确填写。

{constraints_section}

{json_schema}

请根据以下上下文信息生成计划："""

    # 约束条件
    CONSTRAINTS = """
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
"""

    # JSON Schema（简化版）
    JSON_SCHEMA = """
输出格式要求：
- plan_id: 计划ID
- plan_name: 计划名称
- overall_rating: 推荐/谨慎推荐/不推荐
- track_overview: 轨迹概述
- weather_overview: 天气概述
- transport_overview: 交通概述
- trip_date_weather: 当天天气详情
- hourly_weather: 逐小时天气
- critical_grid_weather: 关键点天气
- itinerary: 行程安排
- equipment_recommendations: 装备建议
- scenic_spots: 风景点
- precautions: 注意事项
- safety_assessment: 安全评估
- safety_issues: 安全问题
- risk_factors: 风险因素
- emergency_rescue_contacts: 应急联系方式
"""

    @classmethod
    def get_system_prompt(cls) -> str:
        """获取系统提示词"""
        return cls.SYSTEM_PROMPT_TEMPLATE.format(
            constraints_section=cls.CONSTRAINTS,
            json_schema=cls.JSON_SCHEMA
        )

    @classmethod
    def get_user_prompt(
        cls,
        raw_request: str,
        additional_info: Optional[str] = None,
        track_info: Optional[Dict[str, Any]] = None,
        weather_info: Optional[Dict[str, Any]] = None,
        transport_info: Optional[Dict[str, Any]] = None,
        search_results: Optional[List[Dict]] = None
    ) -> str:
        """生成用户提示词"""
        prompt = f"""
请根据以下户外活动规划信息，生成一个详细的户外活动计划：

## 用户原始请求
{raw_request}
"""

        if additional_info and additional_info.strip():
            prompt += f"""
## ⚠️ 用户额外要求（请在规划中重点考虑）
{additional_info}

**重要提示**：请在行程安排、装备建议、注意事项等方面充分考虑上述用户的额外要求。
"""

        if track_info:
            prompt += f"""
## 轨迹分析信息
- 总距离：{track_info.get('distance_km', '未知')}公里
- 总爬升：{track_info.get('ascent_m', '未知')}米
- 总下降：{track_info.get('descent_m', '未知')}米
- 难度：{track_info.get('difficulty', '未知')}
- 预计用时：{track_info.get('duration_hours', '未知')}小时
"""

        if weather_info:
            prompt += f"""
## 天气信息
- 天气状况：{weather_info.get('condition', '未知')}
- 温度范围：{weather_info.get('temp_min', '未知')}~{weather_info.get('temp_max', '未知')}°C
- 风力：{weather_info.get('wind_scale', '未知')}级
"""

        if transport_info:
            prompt += f"""
## 交通信息
{transport_info.get('overview', '交通信息不可用')}
"""

        if search_results:
            prompt += """
## 搜索参考信息
"""
            for category, results in search_results.items():
                if results:
                    prompt += f"\n### {category}\n"
                    for r in results[:3]:
                        content = r.get('content', '')[:150] if r.get('content') else ''
                        prompt += f"- {r.get('title', '')}: {content}...\n"

        prompt += """
请按照 OutdoorActivityPlan 的结构化输出格式，生成一个完整的户外活动计划。

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


def get_system_prompt() -> str:
    """获取系统提示词的便捷函数"""
    return LLMPromptManager.get_system_prompt()


def get_user_prompt(**kwargs) -> str:
    """获取用户提示词的便捷函数"""
    return LLMPromptManager.get_user_prompt(**kwargs)
