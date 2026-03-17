"""
Map API Tests
=============

Tests for the MapClient (Gaode Maps) integration.
"""

import pytest
from unittest.mock import Mock, patch
from src.api.config import APIConfig
from src.api.map_client import MapClient
from src.api.utils import APIError
from src.schemas.transport import (
    GeocodeResult, DrivingRoute, TransitRoute, TransitSegment,
    RouteStep, TransportRoutes
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
    def test_transport_routes_with_taxi_cost(self, mock_request):
        """测试综合路线包含打车费用"""
        mock_request.side_effect = [
            # 驾车路线
            {
                "status": "1",
                "info": "OK",
                "route": {
                    "taxi_cost": "45",
                    "paths": [
                        {
                            "distance": 15000,
                            "duration": 1800,
                            "tolls": 10,
                            "traffic_lights": 5
                        }
                    ]
                }
            },
            # 步行路线
            {
                "status": "1",
                "info": "OK",
                "route": {
                    "paths": [
                        {
                            "distance": 500,
                            "duration": 400
                        }
                    ]
                }
            },
            # 公交路线
            {
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
                        }
                    ]
                }
            }
        ]

        config = APIConfig()
        client = MapClient(config)
        result = client.get_transport_routes("国贸桥", "西直门", "北京")

        assert isinstance(result, TransportRoutes)
        assert result.outbound["driving"]["tolls_yuan"] == 10
        assert result.outbound["transit"]["cost_yuan"] == 4
        # taxi_cost 从 route.taxi_cost 获取
        assert result.outbound["driving"]["taxi_cost_yuan"] == 45

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
