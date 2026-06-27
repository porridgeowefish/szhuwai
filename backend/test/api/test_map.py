"""
Map API Tests
=============

Tests for the MapClient (Gaode Maps) integration.
"""

import pytest
from unittest.mock import patch
from src.api.config import APIConfig
from src.api.map_client import MapClient
from src.api.utils import APIError
from src.schemas.transport import (
    GeocodeResult, DrivingRoute, TransitRoute
)


class TestMapClient:
    """测试地图 API 客户端"""

    def test_client_initialization(self):
        """测试地图客户端初始化"""
        config = APIConfig()
        client = MapClient(config)

        assert client.base_url == config.MAP_BASE_URL
        assert client.config == config

    @patch('src.api.map_client.MapClient._make_request')
    def test_geocode_address_to_coordinates(self, mock_request):
        """测试地址转坐标"""
        mock_request.return_value = {
            "status": "1",
            "info": "OK",
            "infocode": "10000",
            "count": "1",
            "geocodes": [
                {
                    "formatted_address": "北京市朝阳区",
                    "province": "北京",
                    "city": "北京市",
                    "district": "朝阳区",
                    "street": "",
                    "adcode": "110105",
                    "location": "116.487,39.982"
                }
            ]
        }

        config = APIConfig()
        client = MapClient(config)
        result = client.geocode("北京市朝阳区")

        assert isinstance(result, GeocodeResult)
        assert result.address == "北京市朝阳区"
        assert result.lat == 39.982
        assert result.lon == 116.487

    @patch('src.api.map_client.MapClient._make_request')
    def test_driving_route_planning(self, mock_request):
        """测试驾车路线规划"""
        mock_request.return_value = {
            "status": "1",
            "info": "OK",
            "route": {
                "paths": [
                    {
                        "distance": "15000",
                        "duration": "1800",
                        "tolls": "10",
                        "traffic_lights": 5,
                        "steps": [
                            {
                                "instruction": "出发",
                                "distance": 100,
                                "duration": 60,
                                "action": "出发"
                            }
                        ]
                    }
                ]
            }
        }

        config = APIConfig()
        client = MapClient(config)
        result = client.driving_route("116.487,39.982", "116.4,39.9")

        assert isinstance(result, DrivingRoute)
        assert result.available is True
        assert result.distance_km == 15.0
        assert result.duration_min == 30

    def test_error_code_parsing(self):
        """测试错误码解析"""
        config = APIConfig()
        client = MapClient(config)

        assert client.parse_error({"status": "9"}) == "无相关数据"
        assert client.parse_error({"status": "2"}) == "权限不足"

    @patch('src.api.map_client.MapClient._make_request')
    def test_transit_route_multiple_plans(self, mock_request):
        """测试返回3条公交方案"""
        mock_request.return_value = {
            "status": "1",
            "info": "OK",
            "route": {
                "transits": [
                    {
                        "distance": 10000,
                        "duration": 3600,
                        "cost": "4",
                        "walking_distance": 1000,
                        "segments": [
                            {
                                "bus": {
                                    "buslines": [
                                        {
                                            "name": "地铁1号线",
                                            "id": "1101",
                                            "departure_stop": {"name": "国贸"},
                                            "arrival_stop": {"name": "西直门"},
                                            "operator": "北京地铁"
                                        }
                                    ]
                                },
                                "duration": 3000,
                                "distance": 9000,
                                "price": "3"
                            }
                        ]
                    },
                    {
                        "distance": 12000,
                        "duration": 4200,
                        "cost": "5",
                        "walking_distance": 1500,
                        "segments": [
                            {
                                "bus": {
                                    "buslines": [
                                        {
                                            "name": "特8路",
                                            "id": "T8",
                                            "departure_stop": {"name": "国贸桥"},
                                            "arrival_stop": {"name": "动物园"},
                                            "operator": "北京公交"
                                        }
                                    ]
                                },
                                "duration": 3600,
                                "distance": 10000,
                                "price": "4"
                            }
                        ]
                    },
                    {
                        "distance": 15000,
                        "duration": 4800,
                        "cost": "6",
                        "walking_distance": 2000,
                        "segments": [
                            {
                                "bus": {
                                    "buslines": [
                                        {
                                            "name": "地铁10号线",
                                            "id": "1010",
                                            "departure_stop": {"name": "国贸"},
                                            "arrival_stop": {"name": "知春路"},
                                            "operator": "北京地铁"
                                        }
                                    ]
                                },
                                "duration": 3000,
                                "distance": 8000,
                                "price": "3"
                            }
                        ]
                    }
                ]
            }
        }

        config = APIConfig()
        client = MapClient(config)
        routes = client.transit_route("116.487,39.982", "116.4,39.9", "北京")

        assert len(routes) == 3
        assert all(isinstance(route, TransitRoute) for route in routes)
        assert routes[0].available is True
        assert routes[1].available is True
        assert routes[2].available is True

    @patch('src.api.map_client.MapClient._make_request')
    def test_transit_route_detailed_info(self, mock_request):
        """测试详细公交信息（线路、站点）"""
        mock_request.return_value = {
            "status": "1",
            "info": "OK",
            "route": {
                "transits": [
                    {
                        "distance": 10000,
                        "duration": 3600,
                        "cost": "4",
                        "walking_distance": 1000,
                        "segments": [
                            {
                                "bus": {
                                    "buslines": [
                                        {
                                            "name": "地铁4号线大兴线",
                                            "id": "D4",
                                            "departure_stop": {"name": "宣武门"},
                                            "arrival_stop": {"name": "西单"},
                                            "operator": "北京地铁"
                                        }
                                    ]
                                },
                                "duration": 2400,
                                "distance": 6000,
                                "price": "3"
                            },
                            {
                                "bus": {
                                    "buslines": [
                                        {
                                            "name": "特8路",
                                            "id": "T8",
                                            "departure_stop": {"name": "西单"},
                                            "arrival_stop": {"name": "西直门"},
                                            "operator": "北京公交"
                                        }
                                    ]
                                },
                                "duration": 1200,
                                "distance": 4000,
                                "price": "1"
                            }
                        ]
                    }
                ]
            }
        }

        config = APIConfig()
        client = MapClient(config)
        routes = client.transit_route("116.487,39.982", "116.4,39.9", "北京")

        route = routes[0]
        assert len(route.segments) == 2
        assert route.segments[0].type == "subway"  # 包含"地铁"字样
        assert route.segments[0].line_name == "地铁4号线大兴线"
        assert route.segments[0].departure_stop == "宣武门"
        assert route.segments[0].arrival_stop == "西单"
        assert route.segments[1].type == "bus"
        assert route.segments[1].line_name == "特8路"
        assert route.segments[1].departure_stop == "西单"
        assert route.segments[1].arrival_stop == "西直门"
        assert route.departure_stop == "宣武门"
        assert route.arrival_stop == "西直门"
        assert route.line_name == "地铁4号线大兴线"

    @patch('src.api.map_client.MapClient._make_request')
    def test_transit_route_realistic_structure(self, mock_request):
        """真实高德 v3 结构：耗时/距离在 busline 层，segment 顶层无这些字段。

        旧实现读 segment 顶层 → 每段耗时距离恒为 0；此处锁定字段层级对齐。
        """
        mock_request.return_value = {
            "status": "1",
            "info": "OK",
            "route": {
                "transits": [
                    {
                        "distance": 12000,
                        "duration": 2400,
                        "cost": "5",
                        "walking_distance": 800,
                        "segments": [
                            {"walking": {"distance": 300, "duration": 240}},
                            {"bus": {"buslines": [{
                                "name": "地铁昌平线",
                                "type": "地铁线路",
                                "id": "BC",
                                "departure_stop": {"name": "西二旗"},
                                "arrival_stop": {"name": "生命科学园"},
                                "via_num": 2,
                                "duration": 480,
                                "distance": 4000,
                                "operator": "北京地铁"
                            }]}},
                            {"bus": {"buslines": [{
                                "name": "运通101路",
                                "type": "普通公交",
                                "id": "YM101",
                                "departure_stop": {"name": "生命科学园"},
                                "arrival_stop": {"name": "软件园"},
                                "duration": 600,
                                "distance": 5000,
                                "operator": "北京公交"
                            }]}}
                        ]
                    }
                ]
            }
        }

        config = APIConfig()
        client = MapClient(config)
        routes = client.transit_route("116.3,40.0", "116.4,40.1", "北京")

        assert len(routes) == 1
        route = routes[0]
        # 路线级字段（在 transits[i] 层）
        assert route.duration_min == 40          # 2400s / 60
        assert route.distance_km == 12.0
        assert route.cost_yuan == 5
        assert route.walking_distance == 800
        # 步行段被跳过，只保留 2 个公交/地铁段
        assert len(route.segments) == 2

        seg0 = route.segments[0]
        assert seg0.type == "subway"             # type 字段识别
        assert seg0.line_name == "地铁昌平线"
        assert seg0.departure_stop == "西二旗"
        assert seg0.arrival_stop == "生命科学园"
        assert seg0.duration_min == 8            # 480s 来自 busline，不是 segment 顶层
        assert seg0.distance_m == 4000

        seg1 = route.segments[1]
        assert seg1.type == "bus"
        assert seg1.line_name == "运通101路"
        assert seg1.duration_min == 10           # 600s / 60
        assert seg1.distance_m == 5000

    @patch('src.api.map_client.MapClient._make_request')
    def test_subway_detection_variants(self, mock_request):
        """地铁识别：优先 type 字段，缺失时用线路名正则（机场线/有轨电车）。"""
        mock_request.return_value = {
            "status": "1",
            "info": "OK",
            "route": {
                "transits": [{
                    "distance": 1000,
                    "duration": 600,
                    "cost": "0",
                    "walking_distance": 0,
                    "segments": [
                        {"bus": {"buslines": [{"name": "地铁亦庄线", "type": "地铁线路"}]}},
                        {"bus": {"buslines": [{"name": "机场线"}]}},
                        {"bus": {"buslines": [{"name": "有轨电车T1线"}]}},
                        {"bus": {"buslines": [{"name": "345路"}]}},
                    ]
                }]
            }
        }

        config = APIConfig()
        client = MapClient(config)
        routes = client.transit_route("116.3,40.0", "116.4,40.1", "北京")

        types = [s.type for s in routes[0].segments]
        assert types == ["subway", "subway", "subway", "bus"]

    @patch('src.api.map_client.MapClient._make_request')
    def test_driving_route_with_tolls(self, mock_request):
        """测试驾车路线包含过路费"""
        mock_request.return_value = {
            "status": "1",
            "info": "OK",
            "route": {
                "paths": [
                    {
                        "distance": 50000,
                        "duration": 3600,
                        "tolls": 25,
                        "traffic_lights": 10,
                        "steps": [
                            {
                                "instruction": "上京港澳高速",
                                "distance": 45000,
                                "duration": 3300,
                                "action": "直行",
                                "orientation": "南",
                                "road_name": "京港澳高速"
                            },
                            {
                                "instruction": "到达目的地",
                                "distance": 5000,
                                "duration": 300,
                                "action": "右转",
                                "orientation": "西",
                                "road_name": "出口匝道"
                            }
                        ]
                    }
                ]
            }
        }

        config = APIConfig()
        client = MapClient(config)
        result = client.driving_route("116.487,39.982", "116.4,39.9")

        assert isinstance(result, DrivingRoute)
        assert result.available is True
        assert result.distance_km == 50.0
        assert result.duration_min == 60
        assert result.tolls_yuan == 25

    @patch('src.api.map_client.MapClient._make_request')
    def test_retry_mechanism(self, mock_request):
        """测试重试机制 - 当前版本仅测试handle_api_errors装饰器"""
        # 测试 APIError 被正确捕获并抛出
        mock_request.side_effect = APIError("无相关数据", 9, {"status": "9"})

        config = APIConfig()
        client = MapClient(config)

        with pytest.raises(APIError):
            client.driving_route("116.487,39.982", "116.4,39.9")

    @patch('src.api.map_client.MapClient._make_request')
    def test_api_error_handling(self, mock_request):
        """测试各种API错误场景"""
        # 测试网络错误被 handle_api_errors 捕获
        mock_request.side_effect = APIError("无相关数据", 9, {"status": "9"})

        config = APIConfig()
        client = MapClient(config)

        with pytest.raises(APIError):
            client.driving_route("116.487,39.982", "116.4,39.9")

    @patch('src.api.map_client.MapClient._make_request')
    def test_no_transit_route_available(self, mock_request):
        """测试无公交路线可用的情况"""
        mock_request.return_value = {
            "status": "1",
            "info": "OK",
            "route": {
                "transits": []
            }
        }

        config = APIConfig()
        client = MapClient(config)
        routes = client.transit_route("116.487,39.982", "116.4,39.9", "北京")

        assert routes == []

    @patch('src.api.map_client.MapClient._make_request')
    def test_walking_route_extensions_all(self, mock_request):
        """测试步行路线使用all扩展"""
        mock_request.return_value = {
            "status": "1",
            "info": "OK",
            "route": {
                "paths": [
                    {
                        "distance": 3000,
                        "duration": 1800,
                        "steps": [
                            {
                                "instruction": "步行建国门外大街",
                                "distance": 3000,
                                "duration": 1800,
                                "action": "步行",
                                "orientation": "东",
                                "road_name": "建国门外大街"
                            }
                        ]
                    }
                ]
            }
        }

        config = APIConfig()
        client = MapClient(config)
        result = client.walking_route("116.487,39.982", "116.4,39.9")

        assert isinstance(result, result.__class__)
        # 验证步行路线基本信息
        assert result.available is True
        assert result.distance_m == 3000
        assert result.duration_min == 30
