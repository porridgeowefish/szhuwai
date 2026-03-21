"""
交通服务
========

封装交通路线规划逻辑。
"""

from typing import List

from loguru import logger

from src.schemas.transport import TransportRoutes, LocationInfo, RouteSummary
from src.api.map_client import MapClient


class TransportService:
    """交通规划服务"""

    def __init__(self):
        """初始化服务"""
        self.client = MapClient()

    def plan(
        self,
        departure_point: str,
        destination_coord: str
    ) -> TransportRoutes:
        """
        规划交通路线

        Args:
            departure_point: 出发地点（文字地址）
            destination_coord: 目的地坐标（"lon,lat" 格式）

        Returns:
            TransportRoutes: 交通路线数据
        """
        try:
            logger.info(f"获取交通路线: 起点={departure_point}, 终点坐标={destination_coord}")

            # 出发地地理编码
            departure_geocode = self.client.geocode(departure_point)
            departure_coord = f"{departure_geocode.lon},{departure_geocode.lat}"
            logger.info(f"出发地点地理编码: {departure_coord}")

            # 获取驾车路线
            driving_route = self.client.driving_route(departure_coord, destination_coord)

            # 获取公交/地铁路线
            transit_routes = []
            try:
                city = departure_geocode.city or departure_geocode.province
                transit_routes = self.client.transit_route(departure_coord, destination_coord, city)
                if transit_routes:
                    logger.info(f"获取到 {len(transit_routes)} 条公交/地铁路线")
            except Exception as e:
                logger.warning(f"获取公交路线失败: {e}")

            # 构建响应
            return self._build_transport_routes(
                departure_point=departure_point,
                departure_coord=departure_coord,
                departure_geocode=departure_geocode,
                destination_coord=destination_coord,
                driving_route=driving_route,
                transit_routes=transit_routes
            )

        except Exception as e:
            logger.error(f"获取交通路线失败: {e}")
            raise

    def _build_transport_routes(
        self,
        departure_point: str,
        departure_coord: str,
        departure_geocode,
        destination_coord: str,
        driving_route,
        transit_routes: List
    ) -> TransportRoutes:
        """构建 TransportRoutes 响应"""
        dep_lon, dep_lat = departure_coord.split(',')
        dest_lon, dest_lat = destination_coord.split(',')

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

    def get_reverse_geocode(self, lon: float, lat: float) -> str:
        """
        获取逆地理编码位置名称

        Args:
            lon: 经度
            lat: 纬度

        Returns:
            str: 精准位置名称
        """
        try:
            result = self.client.reverse_geocode(f"{lon},{lat}")
            return result.get_precise_location_name()
        except Exception as e:
            logger.warning(f"逆地理编码失败: {e}")
            return ""

    def search_around_rescue(self, lon: float, lat: float, radius: int = 10000) -> List[dict]:
        """
        搜索周边救援设施

        Args:
            lon: 经度
            lat: 纬度
            radius: 搜索半径（米）

        Returns:
            List[dict]: 救援设施数据
        """
        try:
            location = f"{lon},{lat}"
            keywords = "医院|诊所|派出所|公安局"
            logger.info(f"周边救援搜索: location={location}, keywords={keywords}")

            results = self.client.search_around(
                location=location,
                keywords=keywords,
                radius=radius,
                page_size=20
            )

            if results:
                logger.info(f"找到 {len(results)} 个周边救援点")
            else:
                logger.info("周边救援搜索未找到结果，返回空列表")

            return results if results else []

        except Exception as e:
            logger.error(f"周边救援搜索失败: {e}")
            return []
