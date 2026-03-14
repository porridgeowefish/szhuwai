"""
装备推荐提示词管理
==================

管理户外活动装备推荐的提示词模板。
"""

from typing import List, Dict, Any, Optional
from enum import Enum


class ActivityType(str, Enum):
    """活动类型"""
    HIKING = "徒步"
    CLIMBING = "登山"
    CAMPING = "露营"
    TRAIL_RUNNING = "越野跑"
    MOUNTAINEERING = "高海拔登山"


class SeasonType(str, Enum):
    """季节类型"""
    SPRING = "春季"
    SUMMER = "夏季"
    AUTUMN = "秋季"
    WINTER = "冬季"


class DifficultyLevel(str, Enum):
    """难度等级"""
    EASY = "简单"
    MODERATE = "中等"
    HARD = "困难"
    EXTREME = "极难"


class EquipmentPromptManager:
    """装备推荐提示词管理器"""

    # 装备分类映射
    EQUIPMENT_CATEGORIES = {
        "服装": ["冲锋衣", "速干衣", "保暖层", "防晒衣", "雨衣", "抓绒衣"],
        "鞋类": ["登山鞋", "越野跑鞋", "溯溪鞋", "徒步袜"],
        "背包": ["登山包", "越野包", "腰包", "防水袋"],
        "露营装备": ["帐篷", "睡袋", "防潮垫", "地钉", "营地灯"],
        "炊具": ["炉头", "气罐", "锅具", "餐具", "水袋", "滤水器"],
        "安全装备": ["急救包", "头灯", "哨子", "保温毯", "绳索", "冰爪"],
        "导航工具": ["GPS", "指南针", "地图", "登山杖"],
        "卫生用品": ["防晒霜", "驱蚊液", "纸巾", "垃圾袋", "洗漱用品"],
        "电子产品": ["手机", "充电宝", "相机", "对讲机", "运动手表"],
        "其他": ["墨镜", "帽子", "手套", "护膝", "徒步杖"]
    }

    # 必需装备模板
    ESSENTIAL_EQUIPMENT = {
        "base": [
            {"name": "登山包", "category": "背包", "priority": "必需", "description": "根据行程选择30-50L容量", "quantity": 1},
            {"name": "登山鞋", "category": "鞋类", "priority": "必需", "description": "防滑透气，已磨合", "quantity": 1},
            {"name": "饮用水", "category": "炊具", "priority": "必需", "description": "每2小时1升，根据行程调整", "quantity": 2},
            {"name": "应急食品", "category": "炊具", "priority": "必需", "description": "能量棒、巧克力、坚果等高热量食物", "quantity": 3},
            {"name": "手机", "category": "电子产品", "priority": "必需", "description": "充满电，备好离线地图", "quantity": 1},
        ],
        "safety": [
            {"name": "急救包", "category": "安全装备", "priority": "必需", "description": "创可贴、消毒药水、止痛药、绷带", "quantity": 1},
            {"name": "头灯", "category": "安全装备", "priority": "必需", "description": "及备用电池，防止天黑迷路", "quantity": 1},
            {"name": "保温毯", "category": "安全装备", "priority": "必需", "description": "紧急保暖，轻便易携带", "quantity": 1},
            {"name": "哨子", "category": "安全装备", "priority": "必需", "description": "求救信号用", "quantity": 1},
        ]
    }

    # 季节特定装备
    SEASONAL_EQUIPMENT = {
        SeasonType.SPRING: [
            {"name": "防风外套", "category": "服装", "priority": "推荐", "description": "春季多风", "quantity": 1},
            {"name": "速干裤", "category": "服装", "priority": "推荐", "description": "透气快干", "quantity": 1},
        ],
        SeasonType.SUMMER: [
            {"name": "防晒衣", "category": "服装", "priority": "必需", "description": "UPF50+防晒", "quantity": 1},
            {"name": "遮阳帽", "category": "其他", "priority": "必需", "description": "宽檐帽更佳", "quantity": 1},
            {"name": "防晒霜", "category": "卫生用品", "priority": "必需", "description": "SPF50+", "quantity": 1},
            {"name": "驱蚊液", "category": "卫生用品", "priority": "推荐", "description": "含DEET成分", "quantity": 1},
        ],
        SeasonType.AUTUMN: [
            {"name": "保暖层", "category": "服装", "priority": "推荐", "description": "抓绒或薄羽绒", "quantity": 1},
            {"name": "冲锋衣", "category": "服装", "priority": "推荐", "description": "防风防雨", "quantity": 1},
        ],
        SeasonType.WINTER: [
            {"name": "厚羽绒服", "category": "服装", "priority": "必需", "description": "高蓬松度", "quantity": 1},
            {"name": "保暖帽", "category": "其他", "priority": "必需", "description": "覆盖耳朵", "quantity": 1},
            {"name": "保暖手套", "category": "其他", "priority": "必需", "description": "防水更佳", "quantity": 1},
            {"name": "冰爪", "category": "安全装备", "priority": "推荐", "description": "防滑必备", "quantity": 1},
        ]
    }

    # 难度特定装备
    DIFFICULTY_EQUIPMENT = {
        DifficultyLevel.MODERATE: [
            {"name": "登山杖", "category": "导航工具", "priority": "推荐", "description": "双杖更佳，减轻膝盖压力", "quantity": 2},
        ],
        DifficultyLevel.HARD: [
            {"name": "登山杖", "category": "导航工具", "priority": "必需", "description": "双杖必需，节省30%体力", "quantity": 2},
            {"name": "护膝", "category": "其他", "priority": "推荐", "description": "保护膝盖关节", "quantity": 2},
            {"name": "备用袜子", "category": "鞋类", "priority": "推荐", "description": "保持足部干爽", "quantity": 2},
        ],
        DifficultyLevel.EXTREME: [
            {"name": "登山杖", "category": "导航工具", "priority": "必需", "description": "双杖必需", "quantity": 2},
            {"name": "护膝", "category": "其他", "priority": "必需", "description": "必需品", "quantity": 2},
            {"name": "GPS设备", "category": "导航工具", "priority": "必需", "description": "专业导航", "quantity": 1},
            {"name": "对讲机", "category": "电子产品", "priority": "推荐", "description": "团队通讯", "quantity": 1},
        ]
    }

    @classmethod
    def get_equipment_recommendation_prompt(
        cls,
        activity_type: str,
        season: str,
        difficulty: str,
        duration_hours: float,
        distance_km: float,
        elevation_gain: float,
        weather_conditions: Optional[Dict[str, Any]] = None,
        additional_requirements: Optional[List[str]] = None
    ) -> str:
        """
        生成装备推荐提示词
        """
        prompt = f"""
## 装备推荐需求分析

### 活动基本信息
- 活动类型: {activity_type}
- 季节: {season}
- 难度等级: {difficulty}
- 预计时长: {duration_hours:.1f}小时
- 总距离: {distance_km:.1f}公里
- 累计爬升: {elevation_gain:.0f}米
"""

        if weather_conditions:
            prompt += f"""
### 天气条件
- 天气状况: {weather_conditions.get('condition', '未知')}
- 最高温度: {weather_conditions.get('temp_max', '未知')}°C
- 最低温度: {weather_conditions.get('temp_min', '未知')}°C
- 风力等级: {weather_conditions.get('wind_scale', '未知')}级
- 降水概率: {weather_conditions.get('precip_probability', '未知')}%
"""

        if additional_requirements:
            prompt += f"""
### 额外要求
{chr(10).join(f'- {req}' for req in additional_requirements)}
"""

        prompt += f"""
### 装备分类约束
装备的 category 字段必须从以下列表中选择:
{list(cls.EQUIPMENT_CATEGORIES.keys())}

### 装备优先级
- 必需: 必须携带，缺少会影响安全
- 推荐: 强烈建议携带，提升体验
- 可选: 锦上添花，根据个人情况选择

请根据上述条件，生成合适的装备清单，每种装备需包含:
1. name: 装备名称
2. category: 分类（必须从上述列表选择）
3. priority: 优先级（必需/推荐/可选）
4. quantity: 数量
5. weight_kg: 重量估计（可选）
6. description: 描述说明
7. alternatives: 替代品建议（可选）
"""
        return prompt

    @classmethod
    def get_essential_equipment(cls, difficulty: str, season: str) -> List[Dict]:
        """获取基础必需装备"""
        essentials = cls.ESSENTIAL_EQUIPMENT["base"].copy()
        essentials.extend(cls.ESSENTIAL_EQUIPMENT["safety"])

        # 添加季节装备
        try:
            season_enum = SeasonType(season)
            if season_enum in cls.SEASONAL_EQUIPMENT:
                essentials.extend(cls.SEASONAL_EQUIPMENT[season_enum])
        except ValueError:
            pass

        # 添加难度装备
        try:
            diff_enum = DifficultyLevel(difficulty)
            if diff_enum in cls.DIFFICULTY_EQUIPMENT:
                essentials.extend(cls.DIFFICULTY_EQUIPMENT[diff_enum])
        except ValueError:
            pass

        return essentials


def get_equipment_prompt(
    activity_type: str,
    season: str,
    difficulty: str,
    duration_hours: float,
    distance_km: float,
    elevation_gain: float,
    **kwargs
) -> str:
    """获取装备推荐提示词的便捷函数"""
    return EquipmentPromptManager.get_equipment_recommendation_prompt(
        activity_type=activity_type,
        season=season,
        difficulty=difficulty,
        duration_hours=duration_hours,
        distance_km=distance_km,
        elevation_gain=elevation_gain,
        **kwargs
    )
