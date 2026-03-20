"""
交通规划路由
============

POST /api/v1/transport/plan - 交通规划
"""

from typing import Optional

from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel, Field

from src.schemas.transport import TransportRoutes
from src.api.map_client import MapClient

router = APIRouter(prefix="/transport", tags=["交通规划"])


class TransportPlanResponse(BaseModel):
    """交通规划响应"""
    success: bool = Field(True, description="请求是否成功")
    data: Optional[TransportRoutes] = Field(None, description="交通路线数据")
    message: Optional[str] = Field(None, description="附加消息")


@router.post("/plan", response_model=TransportPlanResponse)
async def plan_transport(
    departure_point: str = Form(..., description="出发地点"),
    destination_lon: float = Form(..., description="目的地经度"),
    destination_lat: float = Form(..., description="目的地纬度")
) -> TransportPlanResponse:
    """
    规划交通路线

    - **departure_point**: 出发地点（供高德解析使用）
    - **destination_lon**: 目的地经度
    - **destination_lat**: 目的地纬度
    """
    try:
        client = MapClient()

        # 出发地地理编码
        departure_geocode = client.geocode(departure_point)
        departure_coord = f"{departure_geocode.lon},{departure_geocode.lat}"

        # 目的地坐标
        destination_coord = f"{destination_lon},{destination_lat}"

        # 获取驾车路线
        driving_route = client.driving_route(departure_coord, destination_coord)

        # 获取公交/地铁路线
        transit_routes = []
        try:
            city = departure_geocode.city or departure_geocode.province
            transit_routes = client.transit_route(departure_coord, destination_coord, city)
        except Exception:
            pass

        # 构建响应
        from src.schemas.transport import TransportRoutes, LocationInfo, RouteSummary

        dep_lon, dep_lat = departure_coord.split(',')

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

        # 推荐方案
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

        transport_data = TransportRoutes(
            origin=LocationInfo(
                address=departure_point,
                lon=float(dep_lon),
                lat=float(dep_lat),
                city=departure_geocode.city,
                province=departure_geocode.province
            ),
            destination=LocationInfo(
                address="目的地",
                lon=float(destination_lon),
                lat=float(destination_lat)
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

        return TransportPlanResponse(
            success=True,
            data=transport_data,
            message="交通规划成功"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"交通规划失败: {str(e)}"
        )
