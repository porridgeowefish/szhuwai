#!/usr/bin/env python3
"""
禁用代理的API测试脚本
"""

import sys
import os
sys.path.append('..')

import requests
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env')

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_without_proxy():
    """测试不使用代理的API调用"""
    logger.info("=== 不使用代理的API测试 ===")

    # 设置不使用代理
    proxies = None

    # 1. 测试天气API
    logger.info("\n1. 测试和风天气API")
    weather_params = {
        'location': '101010100',  # 北京
        'key': os.getenv('QWEATHER_API_KEY'),
        'lang': 'zh'
    }

    try:
        response = requests.get(
            "https://devapi.qweatherapi.com/v7/weather/3d",
            params=weather_params,
            timeout=10,
            proxies=proxies
        )
        logger.info(f"天气API响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logger.info("✓ 天气API成功")
            logger.info(f"   - 城市名: {data.get('location', {}).get('name', 'N/A')}")
            logger.info(f"   - 预报天数: {len(data.get('daily', []))}")
        else:
            logger.error(f"✗ 天气API失败: {response.text}")
    except Exception as e:
        logger.error(f"✗ 天气API异常: {e}")

    # 2. 测试高德地图API
    logger.info("\n2. 测试高德地图API")
    map_params = {
        'address': '北京市朝阳区',
        'key': os.getenv('AMAP_API_KEY'),
        'output': 'JSON'
    }

    try:
        response = requests.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params=map_params,
            timeout=10,
            proxies=proxies
        )
        logger.info(f"地图API响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1':
                logger.info("✓ 地图API成功")
                logger.info(f"   - 结果数量: {len(data.get('geocodes', []))}")
                if data.get('geocodes'):
                    location = data['geocodes'][0]
                    logger.info(f"   - 坐标: {location.get('location', 'N/A')}")
            else:
                logger.error(f"✗ 地图API失败: {data.get('info', 'Unknown error')}")
        else:
            logger.error(f"✗ 地图API失败: {response.text}")
    except Exception as e:
        logger.error(f"✗ 地图API异常: {e}")

    # 3. 测试Tavily搜索API
    logger.info("\n3. 测试Tavily搜索API")
    search_data = {
        'query': '北京天气',
        'api_key': os.getenv('TAVILY_API_KEY')
    }

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json=search_data,
            timeout=10,
            proxies=proxies
        )
        logger.info(f"搜索API响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logger.info("✓ 搜索API成功")
            logger.info(f"   - 结果数量: {len(data.get('results', []))}")
        else:
            logger.error(f"✗ 搜索API失败: {response.text}")
    except Exception as e:
        logger.error(f"✗ 搜索API异常: {e}")

def test_clients_without_proxy():
    """测试客户端但不使用代理"""
    logger.info("\n=== 客户端测试（不使用代理）===")

    # 临时禁用代理
    import os
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''

    # 1. 测试天气客户端
    logger.info("\n1. 测试WeatherClient")
    try:
        from src.api.config import APIConfig
        from src.api.weather_client import WeatherClient

        config = APIConfig.from_env('../.env')
        weather = WeatherClient(config)
        result = weather.get_weather_3d('北京')
        logger.info(f"✓ WeatherClient成功: {len(result.daily)}天预报")
    except Exception as e:
        logger.error(f"✗ WeatherClient失败: {e}")

    # 2. 测试地图客户端
    logger.info("\n2. 测试MapClient")
    try:
        from src.api.config import APIConfig
        from src.api.map_client import MapClient

        config = APIConfig.from_env('../.env')
        map_client = MapClient(config)
        result = map_client.geocode('北京市朝阳区')
        logger.info(f"✓ MapClient成功: {len(result.geocodes)}个结果")
    except Exception as e:
        logger.error(f"✗ MapClient失败: {e}")

    # 3. 测试搜索客户端
    logger.info("\n3. 测试SearchClient")
    try:
        from src.api.config import APIConfig
        from src.api.search_client import SearchClient

        config = APIConfig.from_env('../.env')
        search = SearchClient(config)
        result = search.search("北京天气")
        logger.info("✓ SearchClient成功")
    except Exception as e:
        logger.error(f"✗ SearchClient失败: {e}")

if __name__ == "__main__":
    test_without_proxy()
    test_clients_without_proxy()