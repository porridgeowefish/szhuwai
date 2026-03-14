"""
Map API Client
==============

Client for integrating with 高德地图 (Gaode Maps) API.
"""

import logging
import time
from typing import Dict, Optional, List
from functools import wraps

from . import BaseAPIClient, handle_api_errors, APIError
from .config import api_config
from src.schemas.transport import (
    TransitRoute,
    TransitSegment,
    DrivingRoute,
    WalkingRoute,
    TransportRoutes,
    GeocodeResult,
    ReverseGeocodeResult,
    POIInfo,
    RoadInfo
)

logger = logging.getLogger(__name__)


class MapClient(BaseAPIClient):
    """高德地图API客户端"""

    def __init__(self, config=None):
        super().__init__(config or api_config)
        self.base_url = self.config.MAP_BASE_URL

    def _safe_get_string(self, data: dict, key: str, default: str = "") -> str:
        """
        安全获取字符串类型的字段，处理高德 API 返回的空列表 []
        空列表会被转换为空字符串，避免 Pydantic 验证失败

        Args:
            data: 字典数据
            key: 键名
            default: 默认值

        Returns:
            str: 字符串值
        """
        value = data.get(key, default)
        if isinstance(value, str):
            return value
        elif value is None or value == []:
            return default
        else:
            # 如果是其他类型，尝试转换为字符串
            return str(value) if value else default

    def _retry_request(self, func=None, max_retries=3, delay=1):
        """重试请求装饰器"""
        if func is None:
            return lambda f: self._retry_request(f, max_retries, delay)

        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except APIError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"请求失败，第 {attempt + 1} 次重试: {str(e)}")
                        time.sleep(delay * (2 ** attempt))  # 指数退避
                        continue
            raise last_error or APIError("请求失败，超过最大重试次数")
        return wrapper

    def validate_response(self, response: Dict) -> bool:
        """
        验证API响应格式

        高德API有多种响应格式：
        - 大部分接口返回 status="1" 表示成功
        - 部分接口返回 info="OK" 或 info="ok" 表示成功
        - 地理编码等接口返回的顶层可能没有status，但在内部字段
        """
        # 情况1：标准 status 字段
        if "status" in response:
            return response["status"] == "1"

        # 情况2：info 字段（路径规划等接口）
        if "info" in response:
            return response["info"].lower() == "ok"

        # 情况3：地理编码等接口，检查是否有有效数据
        # 如果响应中包含 geocodes、regeocode、route 等字段，认为有效
        valid_keys = ["geocodes", "regeocode", "route", "pois", "suggestions"]
        if any(key in response for key in valid_keys):
            return True

        # 其他情况认为无效
        return False

    def parse_error(self, response: Dict) -> str:
        """解析错误信息"""
        error_codes = {
            "1": "请求成功",
            "0": "请求失败",
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

        # 调试：打印响应内容
        logger.info(f"高德地图原始响应: {response}")

        # 高德返回可能多个结果，取第一个
        geocodes = response.get("geocodes", [])
        if not geocodes:
            # 如果没有geocodes但有其他字段，打印出来
            logger.warning(f"响应中没有geocodes，响应键: {list(response.keys())}")
            raise APIError(f"未找到地址: {response}", 0, response)

        geo_data = geocodes[0]

        return GeocodeResult(
            address=self._safe_get_string(geo_data, "formatted_address"),
            province=self._safe_get_string(geo_data, "province"),
            city=self._safe_get_string(geo_data, "city"),
            district=self._safe_get_string(geo_data, "district"),
            street=self._safe_get_string(geo_data, "street"),
            adcode=self._safe_get_string(geo_data, "adcode"),
            lon=float(geo_data["location"].split(",")[0]),
            lat=float(geo_data["location"].split(",")[1])
        )

    @handle_api_errors
    def reverse_geocode(self, location: str, extensions: str = "all",
                        max_retries: int = 3) -> ReverseGeocodeResult:
        """
        逆地理编码：坐标转地址（核心功能）

        Args:
            location: 经度,纬度 (GCJ02坐标系)
            extensions: 返回数据详细程度 (base/all)，默认 all 以获取 POI 和道路信息
            max_retries: 最大重试次数

        Returns:
            ReverseGeocodeResult: 包含省/市/区/乡镇/POI/道路等详细地名

        Raises:
            APIError: 坐标格式错误或API调用失败
        """
        endpoint = "geocode/regeo"

        # 1. 解析并验证坐标格式
        try:
            lon, lat = location.split(",")
            lon, lat = float(lon), float(lat)
        except (ValueError, AttributeError) as e:
            raise APIError(f"无效的坐标格式: {location}", 0, {})

        # 2. 坐标范围验证（中国境内GCJ02）
        if not (72 < lon < 137 and 0 < lat < 56):
            logger.warning(f"坐标可能不在中境: {location}")

        # 强制使用 extensions=all 以获取完整数据
        params = {
            "location": location,
            "key": self.config.MAP_API_KEY,
            "extensions": "all",  # 强制使用 all
            "radius": "1000",
            "roadlevel": "0"
        }

        # 3. 带重试的请求
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self._make_request("GET", endpoint, params=params)
                break
            except APIError as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(f"逆地理编码请求失败，第 {attempt + 1} 次重试: {str(e)}")
                    time.sleep(1 * (2 ** attempt))  # 指数退避
                    continue
                raise

        # 4. 解析返回数据（处理空列表问题）
        regeocode = response.get("regeocode", {})
        address_component = regeocode.get("addressComponent", {})

        # 安全获取嵌套字典中的字符串
        def safe_get_nested_string(parent_key: str, child_key: str, default: str = "") -> str:
            """安全获取嵌套字典中的字符串"""
            parent = address_component.get(parent_key, {})
            if isinstance(parent, dict):
                return self._safe_get_string(parent, child_key, default)
            return default

        # 5. 处理直辖市（城市可能为空）
        province = self._safe_get_string(address_component, "province")
        city = self._safe_get_string(address_component, "city")
        if not city:
            city = province  # 直辖市的城市名等于省份名

        # 6. 构建格式化地址（如果API未返回）
        formatted_address = self._safe_get_string(regeocode, "formatted_address")
        if not formatted_address:
            district = self._safe_get_string(address_component, "district")
            formatted_address = f"{province}{district}"

        # 7. 解析 POI 列表（用于精准定位）
        pois = []
        pois_data = regeocode.get("pois", [])
        if pois_data and isinstance(pois_data, list):
            for poi in pois_data[:10]:  # 最多取前10个
                try:
                    distance_str = poi.get("distance", "9999")
                    distance = float(distance_str) if distance_str else 9999.0
                    pois.append(POIInfo(
                        name=self._safe_get_string(poi, "name"),
                        type=self._safe_get_string(poi, "type"),
                        typecode=self._safe_get_string(poi, "typecode"),
                        address=self._safe_get_string(poi, "address"),
                        location=self._safe_get_string(poi, "location"),
                        distance=distance
                    ))
                except Exception as e:
                    logger.debug(f"解析POI失败: {e}")
                    continue

        # 8. 解析道路列表
        roads = []
        roads_data = regeocode.get("roads", [])
        if roads_data and isinstance(roads_data, list):
            for road in roads_data[:5]:  # 最多取前5条
                try:
                    distance_str = road.get("distance", "9999")
                    distance = float(distance_str) if distance_str else None
                    roads.append(RoadInfo(
                        name=self._safe_get_string(road, "name"),
                        distance=distance,
                        direction=self._safe_get_string(road, "direction")
                    ))
                except Exception as e:
                    logger.debug(f"解析道路失败: {e}")
                    continue

        # 9. 解析社区/小区信息
        neighborhood = ""
        neighborhood_data = address_component.get("neighborhood", {})
        if isinstance(neighborhood_data, dict):
            neighborhood = self._safe_get_string(neighborhood_data, "name")

        return ReverseGeocodeResult(
            address=formatted_address,
            province=province,
            city=city,
            district=self._safe_get_string(address_component, "district"),
            adcode=self._safe_get_string(address_component, "adcode"),
            township=self._safe_get_string(address_component, "township"),
            neighborhood=neighborhood,
            street_number=safe_get_nested_string("streetNumber", "street"),
            building=safe_get_nested_string("building", "name"),
            lon=lon,
            lat=lat,
            pois=pois,
            roads=roads
        )

    @handle_api_errors
    def driving_route(self, origin: str, destination: str,
                     strategy: int = 2) -> DrivingRoute:
        """
        驾车路线规划（简化版，仅返回核心信息）

        Args:
            origin: 起点坐标 "经度,纬度"
            destination: 终点坐标 "经度,纬度"
            strategy: 路线策略
                - 0: 速度优先（时间）
                - 1: 费用优先（不走收费路段的最快道路）
                - 2: 距离优先（最短距离，不避开拥堵）
                - 10: 返回单条结果（躲避拥堵）

        Returns:
            DrivingRoute: 包含驾车时间、距离、过路费、出租车预估费用
        """
        endpoint = "direction/driving"
        params = {
            "origin": origin,
            "destination": destination,
            "key": self.config.MAP_API_KEY,
            "strategy": str(strategy),
            "extensions": "all",  # 必须为 all 才返回 taxi_cost
            "nosteps": "1"  # 不返回详细步骤，减少数据量
        }

        response = self._make_request("GET", endpoint, params=params)

        # 防御性编程：检查返回状态
        info = response.get("info", "")
        if info.lower() != "ok":
            raise APIError(f"高德地图 API 返回错误: {info} - {response.get('info_code', 'Unknown')}", 0, response)

        route = response.get("route", {})
        paths = route.get("paths", [])

        if not paths:
            raise APIError("未找到驾车路线", 0, response)

        path = paths[0]

        # 提取出租车费用（在 route 层级，不是 paths 里）
        taxi_cost = route.get("taxi_cost")
        taxi_cost_yuan = int(float(taxi_cost)) if taxi_cost else None

        return DrivingRoute(
            available=True,
            duration_min=int(int(path.get("duration", 0)) / 60),
            distance_km=float(int(path.get("distance", 0)) / 1000),
            tolls_yuan=int(float(path.get("tolls", 0) or 0)),
            taxi_cost_yuan=taxi_cost_yuan
        )

    @handle_api_errors
    def walking_route(self, origin: str, destination: str) -> WalkingRoute:
        """步行路线规划（简化版，仅返回核心信息）"""
        endpoint = "direction/walking"
        params = {
            "origin": origin,
            "destination": destination,
            "key": self.config.MAP_API_KEY,
            "extensions": "base"
        }

        response = self._make_request("GET", endpoint, params=params)

        # 防御性编程：检查返回状态（高德返回 info="ok" 小写）
        info = response.get("info", "")
        if info.lower() != "ok":
            raise APIError(f"高德地图 API 返回错误: {info} - {response.get('info_code', 'Unknown')}", 0, response)

        route = response.get("route", {})
        paths = route.get("paths", [])

        if not paths:
            raise APIError("未找到步行路线", 0, response)

        path = paths[0]

        return WalkingRoute(
            available=True,
            duration_min=int(path.get("duration", 0) / 60),
            distance_m=int(path.get("distance", 0))
        )

    @handle_api_errors
    def transit_route(self, origin: str, destination: str,
                     city: str, strategy: int = 0) -> List[TransitRoute]:
        """
        公交路线规划 - 返回前3条路线（简化版，仅返回核心信息）

        Args:
            origin: 起点坐标 "经度,纬度"
            destination: 终点坐标 "经度,纬度"
            city: 城市名称或adcode（必填）
            strategy: 路线策略
                - 0: 最快捷
                - 1: 最经济
                - 2: 最少换乘
                - 3: 最少步行

        Returns:
            List[TransitRoute]: 公交路线列表（最多3条）
        """
        endpoint = "direction/transit/integrated"
        params = {
            "origin": origin,
            "destination": destination,
            "key": self.config.MAP_API_KEY,
            "city": city,  # 必填参数
            "strategy": str(strategy),
            "nightflag": "0",
            "extensions": "base"  # base 包含3个方案的基本信息
        }

        response = self._make_request("GET", endpoint, params=params)

        # 防御性编程：检查返回状态
        info = response.get("info", "")
        if info.lower() != "ok":
            raise APIError(f"高德地图 API 返回错误: {info} - {response.get('info_code', 'Unknown')}", 0, response)

        route = response.get("route", {})
        # 注意：高德API返回的是 transits，不是 transfers
        transits = route.get("transits", [])

        if not transits:
            return []

        routes = []
        # 取前3条路线
        for transit in transits[:3]:
            segments = []

            # 解析公交段详细信息
            for step_data in transit.get("segments", []):
                # 公交/地铁段
                bus_info = step_data.get("bus", {})
                buslines = bus_info.get("buslines", [])

                if buslines:
                    for busline in buslines:
                        # 判断是地铁还是公交
                        line_name = self._safe_get_string(busline, "name")
                        is_subway = "地铁" in line_name or "轻轨" in line_name

                        # 获取站点信息
                        departure_stop_obj = busline.get("departure_stop", {})
                        arrival_stop_obj = busline.get("arrival_stop", {})

                        segment = TransitSegment(
                            type="subway" if is_subway else "bus",
                            line_name=line_name,
                            line_id=self._safe_get_string(busline, "id"),
                            departure_stop=self._safe_get_string(departure_stop_obj, "name") if isinstance(departure_stop_obj, dict) else str(departure_stop_obj),
                            arrival_stop=self._safe_get_string(arrival_stop_obj, "name") if isinstance(arrival_stop_obj, dict) else str(arrival_stop_obj),
                            duration_min=int(int(step_data.get("duration", 0)) / 60),
                            distance_m=int(step_data.get("distance", 0)),
                            price_yuan=int(float(step_data.get("price", 0) or 0)),
                            operator=self._safe_get_string(busline, "operator")
                        )
                        segments.append(segment)

                # 步行段（如果有单独的步行段）
                walking_info = step_data.get("walking", {})
                if walking_info and walking_info.get("distance"):
                    # 步行段不作为TransitSegment，但可以记录步行距离

                    pass

            # 获取票价
            cost_str = transit.get("cost", "0")
            try:
                cost_yuan = int(float(cost_str)) if cost_str else 0
            except (ValueError, TypeError):
                cost_yuan = 0

            transit_route = TransitRoute(
                available=True,
                duration_min=int(int(transit.get("duration", 0)) / 60),
                distance_km=float(int(transit.get("distance", 0)) / 1000),
                cost_yuan=cost_yuan,
                walking_distance=int(transit.get("walking_distance", 0) or 0),
                segments=segments if segments else None,
                departure_stop=segments[0].departure_stop if segments else None,
                arrival_stop=segments[-1].arrival_stop if segments else None,
                line_name=segments[0].line_name if segments else None
            )
            routes.append(transit_route)

        return routes

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

    @handle_api_errors
    def search_around(self, location: str, keywords: str,
                      radius: int = 10000, page_size: int = 20) -> List[Dict]:
        """
        周边雷达搜索（关键字搜索周边的 POI）

        Args:
            location: 中心点坐标 "经度,纬度" (GCJ02坐标系)
            keywords: 搜索关键词，多个用 "|" 分隔，如 "医院|诊所|派出所|公安局"
            radius: 搜索半径（米），默认 10km
            page_size: 每页返回结果数，最大 25

        Returns:
            List[Dict]: POI 列表，包含 name, address, location, distance, tel 等字段
                        如果未搜索到结果，返回空列表 []

        Raises:
            APIError: API 调用失败
        """
        endpoint = "place/around"
        params = {
            "location": location,
            "keywords": keywords,
            "key": self.config.MAP_API_KEY,
            "radius": str(radius),
            "extensions": "all",  # 返回详细信息
            "offset": str(min(page_size, 25))  # 高德限制最大25
        }

        response = self._make_request("GET", endpoint, params=params)

        # 解析返回的 POI 列表
        pois = response.get("pois", [])
        if not pois:
            logger.info(f"周边搜索未找到结果: keywords={keywords}, location={location}")
            return []

        results = []
        for poi in pois:
            try:
                # 解析距离
                distance_str = poi.get("distance", "")
                distance = float(distance_str) if distance_str else None

                results.append({
                    "name": self._safe_get_string(poi, "name"),
                    "type": self._safe_get_string(poi, "type"),
                    "typecode": self._safe_get_string(poi, "typecode"),
                    "address": self._safe_get_string(poi, "address"),
                    "location": self._safe_get_string(poi, "location"),
                    "distance": distance,
                    "tel": self._safe_get_string(poi, "tel"),
                    "pname": self._safe_get_string(poi, "pname"),  # 省
                    "cityname": self._safe_get_string(poi, "cityname"),  # 市
                    "adname": self._safe_get_string(poi, "adname"),  # 区
                })
            except Exception as e:
                logger.debug(f"解析周边 POI 失败: {e}")
                continue

        logger.info(f"周边搜索找到 {len(results)} 个结果: keywords={keywords}")
        return results

    @handle_api_errors
    def get_transport_routes(self, origin: str, destination: str,
                           city: str = None) -> TransportRoutes:
        """获取综合交通路线"""
        from src.schemas.transport import LocationInfo, RouteSummary

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
                transit_routes = self.transit_route(origin, destination, city)
                if transit_routes:
                    # 取第一条公交路线作为默认
                    transport_routes.outbound["transit"] = transit_routes[0].model_dump()

                    # 提取打车费用（如果有）
                    for route in transit_routes:
                        if hasattr(route, 'segments') and route.segments:
                            for segment in route.segments:
                                if segment.type == "walk":
                                    transport_routes.walking_distance_m += segment.distance_m

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

            # 设置打车费用（从驾车路线中提取，如果有）
            if transport_routes.outbound.get("driving"):
                transport_routes.taxi_cost_yuan = transport_routes.outbound["driving"].get("tolls_yuan", 0)

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