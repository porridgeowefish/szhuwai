"""
Map API Client
==============

Client for integrating with 高德地图 (Gaode Maps) API.
"""

import logging
import re
import time
from typing import Dict, List
from functools import wraps

from . import BaseAPIClient, handle_api_errors, APIError
from .config import api_config
from src.schemas.transport import (
    TransitRoute,
    TransitSegment,
    DrivingRoute,
    WalkingRoute,
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

    @staticmethod
    def _safe_int(value) -> int:
        """安全整数解析：处理高德返回的字符串/数字/空值，失败返回 0。"""
        try:
            if value is None or value == "":
                return 0
            return int(float(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _stop_name(stop_obj) -> str:
        """提取公交/地铁站点名：兼容 dict 或已是字符串的情况。"""
        if isinstance(stop_obj, dict):
            return str(stop_obj.get("name") or "")
        if stop_obj in (None, "", []):
            return ""
        return str(stop_obj)

    # 地铁/轨道交通识别：优先权威 type 字段，线路名正则兜底
    _RAIL_RE = re.compile(r"地铁|轻轨|有轨电车|磁悬浮|APM|机场线")

    @classmethod
    def _is_subway_line(cls, busline: dict, line_name: str) -> bool:
        """判断某条 busline 是否为地铁/轨道交通。"""
        line_type = str(busline.get("type") or "")
        if line_type and ("地铁" in line_type or "轻轨" in line_type):
            return True
        return bool(cls._RAIL_RE.search(line_name or ""))

    def _normalize_coordinate_pair(self, location: str) -> str:
        """按高德 Web 服务要求规范化 lon,lat 坐标（小数点后最多 6 位）。

        若传入的不是合法坐标（如地名文本），原样返回交由下游 API 处理，
        避免在参数解析阶段抛 ValueError 导致整条链路崩溃。
        """
        try:
            lon_text, lat_text = location.split(",", 1)
            lon, lat = float(lon_text), float(lat_text)
        except (ValueError, AttributeError):
            return location
        return f"{lon:.6f},{lat:.6f}"

    def _normalize_coordinate_sequence(self, location: str) -> str:
        """规范化单个或多个坐标对；多个起点用 | 分隔时保持原结构。"""
        return "|".join(self._normalize_coordinate_pair(item) for item in location.split("|"))

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
        info = response.get("info") or response.get("message")
        infocode = response.get("infocode") or response.get("info_code")
        if info or infocode:
            return f"高德地图 API 错误: {info or '未知原因'} (infocode={infocode or 'Unknown'})"

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
        except (ValueError, AttributeError):
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
        for attempt in range(max_retries):
            try:
                response = self._make_request("GET", endpoint, params=params)
                break
            except APIError as e:
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
    def ip_location(self) -> Dict[str, str]:
        """IP 定位：浏览器无法取得经纬度时的低精度兜底。"""
        endpoint = "ip"
        params = {
            "key": self.config.MAP_API_KEY,
        }
        response = self._make_request("GET", endpoint, params=params)
        return {
            "province": self._safe_get_string(response, "province"),
            "city": self._safe_get_string(response, "city"),
            "adcode": self._safe_get_string(response, "adcode"),
            "rectangle": self._safe_get_string(response, "rectangle"),
            "info": self._safe_get_string(response, "info"),
        }

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
            "origin": self._normalize_coordinate_sequence(origin),
            "destination": self._normalize_coordinate_pair(destination),
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
            "origin": self._normalize_coordinate_pair(origin),
            "destination": self._normalize_coordinate_pair(destination),
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
            duration_min=int(int(path.get("duration", 0)) / 60),
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
            "origin": self._normalize_coordinate_pair(origin),
            "destination": self._normalize_coordinate_pair(destination),
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
            if not isinstance(transit, dict):
                continue
            segments = []

            # 解析公交/地铁段。高德 v3 的耗时/距离位于 busline 层（步行段在 walking 层），
            # segment 顶层并无 duration/distance/price；旧实现读顶层导致每段耗时距离恒为 0。
            for step_data in transit.get("segments", []):
                if not isinstance(step_data, dict):
                    continue
                bus_info = step_data.get("bus") or {}
                buslines = bus_info.get("buslines") if isinstance(bus_info, dict) else None
                if not buslines:
                    continue
                for busline in buslines:
                    if not isinstance(busline, dict):
                        continue
                    line_name = self._safe_get_string(busline, "name")
                    departure_stop_obj = busline.get("departure_stop") or {}
                    arrival_stop_obj = busline.get("arrival_stop") or {}

                    # 耗时/距离优先取 busline 层，回退 segment 顶层兼容旧结构
                    duration_sec = self._safe_int(busline.get("duration")) or self._safe_int(step_data.get("duration"))
                    distance_m = self._safe_int(busline.get("distance")) or self._safe_int(step_data.get("distance"))
                    price_yuan = self._safe_int(step_data.get("price")) or self._safe_int(busline.get("price"))

                    try:
                        segments.append(TransitSegment(
                            type="subway" if self._is_subway_line(busline, line_name) else "bus",
                            line_name=line_name,
                            line_id=self._safe_get_string(busline, "id"),
                            departure_stop=self._stop_name(departure_stop_obj),
                            arrival_stop=self._stop_name(arrival_stop_obj),
                            duration_min=max(0, int(duration_sec / 60)),
                            distance_m=max(0, distance_m),
                            price_yuan=max(0, price_yuan),
                            operator=self._safe_get_string(busline, "operator"),
                        ))
                    except Exception as e:
                        logger.debug("解析公交段失败: %s", e)
                        continue

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
            "location": self._normalize_coordinate_pair(location),
            "keywords": keywords,
            "key": self.config.MAP_API_KEY,
            "radius": str(radius),
            "extensions": "all",  # 返回详细信息
            "offset": str(min(page_size, 25)),
            "page": "1",
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
                    "id": self._safe_get_string(poi, "id"),
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
