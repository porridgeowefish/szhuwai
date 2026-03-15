"""
提示词管理器
============

从YAML配置文件加载提示词，支持模板渲染和动态组装。
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from loguru import logger


class PromptManager:
    """提示词管理器 - 从配置文件加载和管理提示词"""

    _instance = None
    _config = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化提示词管理器"""
        if self._config is None:
            self._load_config()

    def _load_config(self) -> None:
        """加载YAML配置文件"""
        config_path = Path(__file__).parent / "configs" / "planning_prompts.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"提示词配置文件不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

        logger.info(f"已加载提示词配置: {config_path}")

    def reload_config(self) -> None:
        """重新加载配置文件"""
        self._config = None
        self._load_config()

    @property
    def config(self) -> Dict[str, Any]:
        """获取配置"""
        return self._config

    # ==================== 约束条件 ====================

    def get_constraint_values(self, constraint_name: str) -> List[str]:
        """获取指定约束的允许值列表"""
        constraints = self._config.get("constraints", {})
        constraint = constraints.get(constraint_name, {})
        return constraint.get("allowed_values", [])

    def get_all_constraints(self) -> Dict[str, List[str]]:
        """获取所有约束条件"""
        constraints = self._config.get("constraints", {})
        return {k: v.get("allowed_values", []) for k, v in constraints.items()}

    # ==================== 系统提示词 ====================

    def get_system_prompt(self) -> str:
        """生成系统提示词"""
        system_config = self._config.get("system", {})

        # 基础角色定义
        role = system_config.get("role", "户外活动规划助手")
        description = system_config.get("description", "")

        # 约束条件部分
        constraints_section = self._build_constraints_section()

        # JSON Schema 部分
        json_schema_section = self._build_json_schema_section()

        # 核心原则
        principles_section = self._build_principles_section()

        # 示例输出
        example_section = self._build_example_section()

        return f"""你是一个专业的{role}。{description}

{constraints_section}

{json_schema_section}

{principles_section}

以下是一个样例json文件，请你作为生成参考。
{example_section}

请根据以下上下文信息生成计划："""

    def _build_constraints_section(self) -> str:
        """构建约束条件部分"""
        constraints = self._config.get("constraints", {})
        lines = ["⚠️ 重要约束（必须遵守）："]

        constraint_descriptions = {
            "equipment_category": ("equipment_recommendations 中的 category 字段", 1),
            "equipment_priority": ("equipment_recommendations 中的 priority 字段", 2),
            "safety_issue_type": ("safety_issues 中的 type 字段", 3),
            "safety_severity": ("safety_issues 中的 severity 字段", 4),
            "scenic_difficulty": ("scenic_spots 中的 difficulty 字段", 5),
            "overall_rating": ("overall_rating 和 safety_assessment 中的 recommendation 字段", 6),
            "rescue_contact_type": ("emergency_rescue_contacts 中的 type 字段", 7),
        }

        for constraint_key, (desc, num) in constraint_descriptions.items():
            if constraint_key in constraints:
                values = constraints[constraint_key].get("allowed_values", [])
                values_str = "、".join(values)
                lines.append(f"{num}. **{desc}必须从以下列表中选择**：")
                lines.append(f"   - {values_str}")

                note = constraints[constraint_key].get("note")
                if note:
                    lines.append(f"   - {note}")

        # 零幻觉原则
        principles = self._config.get("principles", {})
        zero_hallucination = principles.get("zero_hallucination", {})
        if zero_hallucination:
            lines.append(f"8. **⚠️ {zero_hallucination.get('title', '')}**：{zero_hallucination.get('description', '')}")

        return "\n".join(lines)

    def _build_json_schema_section(self) -> str:
        """构建JSON Schema部分"""
        return "```json\n" + self._config.get("example_output", {}).get("json", "{}") + "\n```"

    def _build_principles_section(self) -> str:
        """构建核心原则部分"""
        principles = self._config.get("principles", {})
        lines = []

        for key, principle in principles.items():
            title = principle.get("title", "")
            description = principle.get("description", "").strip()
            if title and description:
                lines.append(f"## {title}")
                lines.append(description)

        return "\n".join(lines)

    def _build_example_section(self) -> str:
        """构建示例输出部分"""
        return "```json\n" + self._config.get("example_output", {}).get("json", "{}") + "\n```"

    # ==================== 用户提示词 ====================

    def get_user_prompt(
        self,
        raw_request: str,
        additional_info: Optional[str] = None,
        track_info: Optional[Dict[str, Any]] = None,
        hourly_weather_data: Optional[str] = None,
        grid_points_data: Optional[str] = None,
        search_content: Optional[str] = None,
        rescue_content: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        生成用户提示词

        Args:
            raw_request: 用户原始请求
            additional_info: 额外要求
            track_info: 轨迹分析信息
            hourly_weather_data: 24小时逐小时天气数据（格式化字符串）
            grid_points_data: 多抽样点天气数据（格式化字符串）
            search_content: 搜索结果内容
            rescue_content: 救援数据内容
            **kwargs: 其他参数

        Returns:
            完整的用户提示词
        """
        templates = self._config.get("user_prompt_templates", {})
        parts = []

        # 标题
        parts.append(templates.get("header", ""))

        # 原始请求
        if raw_request:
            parts.append(templates.get("raw_request", "").format(raw_request=raw_request))

        # 额外要求
        if additional_info and additional_info.strip():
            parts.append(templates.get("additional_info", "").format(additional_info=additional_info))

        # 轨迹分析
        if track_info:
            track_template = templates.get("track_analysis", "")
            parts.append(track_template.format(
                total_distance_km=track_info.get("total_distance_km", 0),
                total_ascent_m=track_info.get("total_ascent_m", 0),
                total_descent_m=track_info.get("total_descent_m", 0),
                difficulty_level=track_info.get("difficulty_level", "未知"),
                weather_condition=track_info.get("weather_condition", "未知"),
                transport_route=track_info.get("transport_route", "未知")
            ))

        # 24小时逐小时天气
        if hourly_weather_data:
            parts.append(templates.get("hourly_weather_24h", "").format(hourly_data=hourly_weather_data))

        # 多抽样点天气
        if grid_points_data:
            parts.append(templates.get("grid_points", "").format(grid_points_data=grid_points_data))

        # 搜索结果
        if search_content:
            parts.append(templates.get("search_results", "").format(search_content=search_content))

        # 救援数据
        if rescue_content:
            parts.append(templates.get("around_rescue", "").format(rescue_content=rescue_content))

        # 输出要求
        parts.append(templates.get("output_requirements", ""))

        return "\n".join(parts)

    # ==================== 便捷方法 ====================

    def get_allowed_equipment_categories(self) -> List[str]:
        """获取允许的装备分类"""
        return self.get_constraint_values("equipment_category")

    def get_allowed_equipment_priorities(self) -> List[str]:
        """获取允许的装备优先级"""
        return self.get_constraint_values("equipment_priority")

    def get_allowed_safety_types(self) -> List[str]:
        """获取允许的安全问题类型"""
        return self.get_constraint_values("safety_issue_type")

    def get_allowed_safety_severities(self) -> List[str]:
        """获取允许的安全严重程度"""
        return self.get_constraint_values("safety_severity")

    def get_allowed_overall_ratings(self) -> List[str]:
        """获取允许的总体评级"""
        return self.get_constraint_values("overall_rating")


# 全局单例
_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    """获取提示词管理器单例"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


def get_system_prompt() -> str:
    """获取系统提示词"""
    return get_prompt_manager().get_system_prompt()


def get_user_prompt(**kwargs) -> str:
    """获取用户提示词"""
    return get_prompt_manager().get_user_prompt(**kwargs)
