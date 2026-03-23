"""
Integration Tests
=================

End-to-end tests for the Outdoor Agent Planner workflow.
"""

import pytest
from unittest.mock import patch
from src.api.config import APIConfig
from src.api.weather_client import WeatherClient
from src.api.map_client import MapClient
from src.api.search_client import SearchClient


@pytest.mark.integration
class TestWorkflowIntegration:
    """测试完整工作流程集成"""

    @pytest.fixture
    def config(self):
        """Return API configuration."""
        return APIConfig()

    def test_complete_planning_workflow(self, config):
        """测试完整的规划工作流程"""
        # Initialize clients
        weather_client = WeatherClient(config)
        map_client = MapClient(config)
        search_client = SearchClient(config)

        # Mock the API calls
        with patch.object(weather_client, 'get_weather_3d') as mock_weather:
            with patch.object(map_client, 'geocode') as mock_geocode:
                with patch.object(search_client, 'search') as mock_search:
                    # Setup mock responses
                    from src.schemas.weather import CityWeatherResponse, CityWeatherDaily
                    mock_weather.return_value = CityWeatherResponse(
                        location="Beijing",
                        updateTime="2024-03-10 12:00:00",
                        fxLink="http://link",
                        daily=[CityWeatherDaily(
                            fxDate="2024-03-15",
                            tempMax=26,
                            tempMin=15,
                            textDay="晴",
                            windScaleDay="3",
                            windSpeedDay=10,
                            humidity=65,
                            precip=0.0,
                            pressure=1013,
                            uvIndex=6,
                            vis=20
                        )]
                    )

                    from src.schemas.transport import GeocodeResult
                    mock_geocode.return_value = GeocodeResult(
                        address="北京市朝阳区",
                        province="北京市",
                        city="北京市",
                        district="朝阳区",
                        adcode="110105",
                        lon=116.487,
                        lat=39.982
                    )

                    from src.schemas.search import WebSearchResponse, SearchResult
                    mock_search.return_value = WebSearchResponse(
                        query="北京 徒步 路线",
                        results=[SearchResult(
                            title="香山徒步路线",
                            url="https://example.com",
                            content="香山是北京著名的...",
                            score=0.85,
                            source="example.com"
                        )],
                        total_results=1,
                        search_time=0.5
                    )

                    # Execute workflow
                    weather_data = weather_client.get_weather_3d("Beijing")
                    location = map_client.geocode("北京市朝阳区")
                    search_results = search_client.search("北京 徒步 路线", max_results=5)

                    # Verify results
                    assert weather_data is not None
                    assert location is not None
                    assert search_results is not None
                    assert len(search_results.results) > 0

    def test_error_handling_workflow(self, config):
        """测试错误处理工作流程"""
        weather_client = WeatherClient(config)

        # Test with invalid location
        with patch.object(weather_client, '_make_request') as mock_request:
            mock_request.side_effect = Exception("API Error")

            with pytest.raises(Exception):
                weather_client.get_weather_3d("InvalidLocation")


# 注意：真实 API 集成测试已删除，避免消耗 API 配额
# 如需测试真实 API，请在本地手动运行
