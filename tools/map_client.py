"""
Map API Client
==============

Client for integrating with 高德地图 (Gaode Maps) API.
"""

import logging
from typing import Dict, Optional, List
from urllib.parse import quote

logger = logging.getLogger(__name__)

from . import BaseAPIClient, handle_api_errors, APIError
from .config import api_config
from schemas.transport import (
    RouteStep,
    TransitRoute,
    DrivingRoute,
    WalkingRoute,
    TransportRoutes,
    GeocodeResult,
    ReverseGeocodeResult
)


class MapClient(BaseAPIClient):
    """高德地图API客户端"""

    def __init__(self, config=None):
        super().__init__(config or api_config)
        self.base_url = self.config.MAP_BASE_URL

    def validate_response(self, response: Dict) -> bool:
        """验证API响应格式"""
        if "status" not in response:
            return False
        return response["status"] == "1"

    def parse_error(self, response: Dict) -> str:
        """解析错误信息"""
        error_codes = {
            "0": "请求成功",
            "1": "未知错误",
            "2": "权限不足",
            "3": "key无效",
            "4": "非法参数",
            "5": "非法请求",
            "6": "不存在",
            "7": "服务不可用",
            "8": "超出请求限制",
            "9": "无相关数据",
            "10": "IP被封禁",
            "11": "账号被冻结",
            "12": "缺乏key必填参数",
            "13": "非法的key",
            "14": "配额不足",
            "15": "浏览器Referer非法",
            "16": "IP白名单校验失败",
            "17": "服务被禁用",
            "18": "敏感词校验失败",
            "19": "签名错误",
            "20": "无应用权限",
            "21": "无应用权限",
            "22": "无应用权限",
            "23": "APP不存在",
            "24": "APP被禁用",
            "25": "应用权限状态无效",
            "26": "平台权限校验失败",
            "27": "API服务不可用",
            "100": "请求超时"
        }

        status = response.get("status", "Unknown")
        return error_codes.get(status, f"未知错误: {status}")

    @handle_api_errors
    def geocode(self, address: str, city: str = None) -> GeocodeResult:
        """地理编码：地址转坐标"""
        endpoint = "geocode/geo"
        params = {
            "address": address,
            "key": self.config.MAP_API_KEY
        }
        if city:
            params["city"] = city

        response = self._make_request("GET", endpoint, params=params)

        # 高德返回可能多个结果，取第一个
        geocodes = response.get("geocodes", [])
        if not geocodes:
            raise APIError("未找到地址", 0, response)

        geo_data = geocodes[0]
        return GeocodeResult(
            address=geo_data.get("formatted_address", ""),
            province=geo_data.get("province", ""),
            city=geo_data.get("city", ""),
            district=geo_data.get("district", ""),
            street=geo_data.get("street", ""),
            adcode=geo_data.get("adcode", ""),
            lon=float(geo_data["location"].split(",")[0]),
            lat=float(geo_data["location"].split(",")[1])
        )

    @handle_api_errors
    def reverse_geocode(self, location: str, extensions: str = "all") -> ReverseGeocodeResult:
        """逆地理编码：坐标转地址"""
        endpoint = "geocode/regeo"
        params = {
            "location": location,
            "key": self.config.MAP_API_KEY,
            "extensions": extensions,
            "radius": "1000",
            "roadlevel": "0"
        }

        response = self._make_request("GET", endpoint, params=params)

        regeocode = response.get("regeocode", {})
        address_component = regeocode.get("address_component", {})
        formatted_address = regeocode.get("formatted_address", "")

        return ReverseGeocodeResult(
            address=formatted_address,
            province=address_component.get("province", ""),
            city=address_component.get("city", ""),
            district=address_component.get("district", ""),
            adcode=address_component.get("adcode", ""),
            township=address_component.get("township", ""),
            street_number=address_component.get("streetNumber", {}).get("streetNumber", ""),
            building=address_component.get("building", {}).get("name", ""),
            lon=float(location.split(",")[0]),
            lat=float(location.split(",")[1])
        )

    @handle_api_errors
    def driving_route(self, origin: str, destination: str,
                     strategy: str = "LEAST_TIME") -> DrivingRoute:
        """驾车路线规划"""
        endpoint = "direction/driving"
        params = {
            "origin": origin,
            "destination": destination,
            "key": self.config.MAP_API_KEY,
            "strategy": strategy,
            "extensions": "base"
        }

        response = self._make_request("GET", endpoint, params=params)
        route = response.get("route", {})
        paths = route.get("paths", [])

        if not paths:
            raise APIError("未找到驾车路线", 0, response)

        path = paths[0]
        steps = []

        for step_data in path.get("steps", []):
            step = RouteStep(
                instruction=step_data.get("instruction", ""),
                distance=step_data.get("distance", 0),
                duration=step_data.get("duration", 0),
                action=step_data.get("action", ""),
                orientation=step_data.get("orientation"),
                road_name=step_data.get("road_name")
            )
            steps.append(step)

        return DrivingRoute(
            available=True,
            duration_min=int(int(path.get("duration", 0)) / 60),
            distance_km=float(int(path.get("distance", 0)) / 1000),
            tolls_yuan=int(path.get("tolls", 0)),
            traffic_lights=path.get("traffic_lights", 0),
            steps=steps
        )

    @handle_api_errors
    def walking_route(self, origin: str, destination: str) -> WalkingRoute:
        """步行路线规划"""
        endpoint = "direction/walking"
        params = {
            "origin": origin,
            "destination": destination,
            "key": self.config.MAP_API_KEY,
            "extensions": "base"
        }

        response = self._make_request("GET", endpoint, params=params)
        route = response.get("route", {})
        paths = route.get("paths", [])

        if not paths:
            raise APIError("未找到步行路线", 0, response)

        path = paths[0]
        steps = []

        for step_data in path.get("steps", []):
            step = RouteStep(
                instruction=step_data.get("instruction", ""),
                distance=step_data.get("distance", 0),
                duration=step_data.get("duration", 0),
                action=step_data.get("action", ""),
                orientation=step_data.get("orientation"),
                road_name=step_data.get("road_name")
            )
            steps.append(step)

        return WalkingRoute(
            available=True,
            duration_min=int(path.get("duration", 0) / 60),
            distance_m=int(path.get("distance", 0)),
            steps=steps
        )

    @handle_api_errors
    def transit_route(self, origin: str, destination: str,
                     city: str = None) -> TransitRoute:
        """公交路线规划"""
        endpoint = "direction/transit/integrated"
        params = {
            "origin": origin,
            "destination": destination,
            "key": self.config.MAP_API_KEY,
            "nightflag": "0",
            "extensions": "base"
        }
        if city:
            params["city"] = city

        response = self._make_request("GET", endpoint, params=params)
        route = response.get("route", {})
        transfers = route.get("transfers", [])

        if not transfers:
            return TransitRoute(
                available=False,
                duration_min=0,
                distance_km=0,
                cost_yuan=0,
                walking_distance=0,
                steps=[]
            )

        transfer = transfers[0]
        steps = []

        for step_data in transfer.get("segments", []):
            for walk_data in step_data.get("walk_steps", []):
                step = RouteStep(
                    instruction=walk_data.get("instruction", ""),
                    distance=walk_data.get("distance", 0),
                    duration=walk_data.get("duration", 0),
                    action="walking",
                    orientation=walk_data.get("orientation"),
                    road_name=walk_data.get("road_name")
                )
                steps.append(step)

        return TransitRoute(
            available=True,
            duration_min=int(transfer.get("duration", 0) / 60),
            distance_km=float(transfer.get("distance", 0) / 1000),
            cost_yuan=int(transfer.get("price", 0)),
            walking_distance=int(transfer.get("walking_distance", 0)),
            steps=steps
        )

    @handle_api_errors
    def distance_matrix(self, origins: List[str], destinations: List[str],
                       strategy: str = "LEAST_TIME") -> Dict:
        """距离矩阵查询"""
        endpoint = "distance/batch"
        params = {
            "origins": ";".join(origins),
            "destinations": ";".join(destinations),
            "key": self.config.MAP_API_KEY
        }

        return self._make_request("GET", endpoint, params=params)

    @handle_api_errors
    def place_search(self, keywords: str, city: str = None,
                     bbox: str = None, page_size: int = 10) -> Dict:
        """地点搜索"""
        endpoint = "place/text"
        params = {
            "keywords": keywords,
            "key": self.config.MAP_API_KEY,
            "page_size": page_size
        }
        if city:
            params["city"] = city
        if bbox:
            params["bbox"] = bbox

        return self._make_request("GET", endpoint, params=params)

    def get_transport_routes(self, origin: str, destination: str,
                           city: str = None) -> TransportRoutes:
        """获取综合交通路线"""
        from schemas.transport import LocationInfo, RouteSummary

        transport_routes = TransportRoutes(
            origin=LocationInfo(address=origin),
            destination=LocationInfo(address=destination),
            outbound={},
            summary=RouteSummary()
        )

        try:
            # 获取驾车路线
            driving_route = self.driving_route(origin, destination)
            transport_routes.outbound["driving"] = driving_route.model_dump()

            # 获取步行路线
            walking_route = self.walking_route(origin, destination)
            transport_routes.outbound["walking"] = walking_route.model_dump()

            # 获取公交路线
            if city:
                transit_route = self.transit_route(origin, destination, city)
                transport_routes.outbound["transit"] = transit_route.model_dump()

            # 设置推荐方案
            fastest_mode = min(
                [(mode, route.get("duration_min", float('inf')))
                  for mode, route in transport_routes.outbound.items()],
                key=lambda x: x[1]
            )
            if fastest_mode[1] != float('inf'):
                transport_routes.fastest_mode = fastest_mode[0]

            cheapest_mode = min(
                [(mode, route.get("cost_yuan", 0) if mode != "walking" else 0)
                  for mode, route in transport_routes.outbound.items()],
                key=lambda x: x[1]
            )
            transport_routes.cheapest_mode = cheapest_mode[0]

            # 根据距离和时间推荐
            if transport_routes.outbound.get("driving"):
                driving = transport_routes.outbound["driving"]
                if driving["distance_km"] < 50:  # 50公里以内
                    transport_routes.recommended_mode = "driving"
                else:
                    transport_routes.recommended_mode = "transit" if transport_routes.outbound.get("transit") else "driving"

        except APIError as e:
            logger.error(f"获取交通路线失败: {str(e)}")

        return transport_routes

    def get_batch_geocode(self, addresses: List[str]) -> List[Optional[GeocodeResult]]:
        """批量地理编码"""
        results = []
        for address in addresses:
            try:
                result = self.geocode(address)
                results.append(result)
            except APIError as e:
                logger.warning(f"地理编码失败 {address}: {str(e)}")
                results.append(None)
        return results