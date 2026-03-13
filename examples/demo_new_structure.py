"""
演示重构后的新结构
===================

展示 PlanningContext 和轻量化 OutdoorActivityPlan 的使用方法。
"""

from datetime import datetime
from src.schemas.output import OutdoorActivityPlan, EmergencyRescueContact
from src.schemas.weather import CityWeatherDaily

def demonstrate_new_structure():
    """演示新的结构"""
    print("=== 演示重构后的新结构 ===\n")

    # 1. PlanningContext 只在内部流转，不在此演示
    print("1. PlanningContext（内部流转数据）")
    print("- 包含所有原始 API 数据（轨迹、天气、交通、搜索）")
    print("- 仅在系统内部使用，不暴露给前端")
    print("- 用于 LLM 生成最终内容的上下文")
    print()

    # 2. 创建轻量化 OutdoorActivityPlan（最终交付物）

    # 2. 创建轻量化 OutdoorActivityPlan（最终交付物）
    print("2. 创建轻量化 OutdoorActivityPlan（最终交付物）")

    # 创建当天的详细天气（用于前端 UI）
    daily_weather = CityWeatherDaily(
        fxDate="2024-03-15",
        tempMax=25,
        tempMin=15,
        textDay="晴",
        windScaleDay="3",
        windSpeedDay=10,
        humidity=65,
        precip=0.0,
        pressure=1013,
        uvIndex=6,
        vis=20
    )

    # 创建应急救援电话
    emergency_contacts = [
        EmergencyRescueContact(name="急救中心", phone="120", type="医疗"),
        EmergencyRescueContact(name="报警电话", phone="110", type="报警"),
        EmergencyRescueContact(name="景区救援", phone="12301", type="救援")
    ]

    # 创建计划
    plan = OutdoorActivityPlan(
        plan_id="hiking-2024-001",
        plan_name="香山经典徒步路线",
        overall_rating="推荐",

        # 文本概述（由 LLM 基于 Context 生成）
        track_overview="11km/爬升750m/困难",
        weather_overview="周末晴朗，最高25度，无降水风险",
        transport_overview="建议驾车，约1.5小时",

        # 精准保留的天气数据
        trip_date_weather=daily_weather,
        hourly_weather=[],  # 实际使用时填入逐小时数据
        critical_grid_weather=[],  # 实际使用时填入关键点天气

        # 核心规划内容
        itinerary=[
            {"time": "08:00", "activity": "从市区出发", "location": "北京市区"},
            {"time": "09:30", "activity": "开始徒步", "location": "香山步道"},
            {"time": "12:00", "activity": "山顶休息", "location": "香炉峰"}
        ],
        equipment_recommendations=[
            {"name": "登山鞋", "category": "鞋类", "priority": "必需"},
            {"name": "登山杖", "category": "导航工具", "priority": "推荐"}
        ],
        scenic_spots=[
            {"name": "香炉峰", "description": "北京最高峰", "difficulty": "中等", "location": {"lat": 39.99, "lon": 116.19, "elevation": 575}}
        ],
        precautions=[
            "提前查看天气预报",
            "携带足够的水和食物",
            "告知家人行程计划"
        ],

        # 安全与应急
        safety_assessment={"overall_risk": "中等风险", "recommendation": "谨慎推荐"},
        safety_issues=[
            {"type": "地形风险", "severity": "中", "description": "部分路段坡度较陡", "mitigation": "使用登山杖，注意休息"}
        ],
        risk_factors=["部分路段坡度较大"],
        emergency_rescue_contacts=emergency_contacts
    )

    print("- 计划ID:", plan.plan_id)
    print("- 总体评级:", plan.overall_rating)
    print("- 轨迹概述:", plan.track_overview)
    print("- 天气概述:", plan.weather_overview)
    print("- 交通概述:", plan.transport_overview)
    print("\n- 当日天气:", plan.trip_date_weather.textDay,
          plan.trip_date_weather.tempMax, "°C")
    print("- 应急救援电话数量:", len(plan.emergency_rescue_contacts))
    for contact in plan.emergency_rescue_contacts:
        print(f"  * {contact.name}: {contact.phone} ({contact.type})")

    print("\n=== 重构优势 ===")
    print("1. PlanningContext 只在内部流转，不暴露给前端")
    print("2. OutdoorActivityPlan 是轻量化模型，只包含前端需要的数据")
    print("3. 天气数据精准保留，便于前端做滑动栏展示")
    print("4. 应急救援电话聚焦为公共救援电话，更符合安全规范")

    return plan

if __name__ == "__main__":
    plan = demonstrate_new_structure()