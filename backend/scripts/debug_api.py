#!/usr/bin/env python3
"""
API调试脚本
详细调试每个API的调用过程
"""

import sys
import os
sys.path.append('..')

import requests
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env')

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def test_direct_api_call():
    """直接测试API调用"""
    logger.info("=== 直接API调用测试 ===")

    # 测试天气API
    logger.info("\n1. 测试和风天气API")
    weather_params = {
        'location': '101010100',  # 北京的location code
        'key': os.getenv('QWEATHER_API_KEY'),
        'lang': 'zh'
    }

    try:
        # 使用商业主机
        weather_url = "https://p25khw5ygp.re.qweatherapi.com/v7/weather/3d"
        response = requests.get(weather_url, params=weather_params, timeout=10)
        logger.info(f"天气API响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"天气API返回数据: {list(data.keys())}")
        else:
            logger.error(f"天气API错误: {response.text}")
    except Exception as e:
        logger.error(f"天气API异常: {e}")

    # 测试高德地图API
    logger.info("\n2. 测试高德地图API")
    map_params = {
        'address': '北京市朝阳区',
        'key': os.getenv('AMAP_API_KEY'),
        'output': 'JSON'
    }

    try:
        map_url = "https://restapi.amap.com/v3/geocode/geo"
        response = requests.get(map_url, params=map_params, timeout=10)
        logger.info(f"地图API响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"地图API返回数据: {list(data.keys())}")
        else:
            logger.error(f"地图API错误: {response.text}")
    except Exception as e:
        logger.error(f"地图API异常: {e}")

    # 测试Tavily搜索API
    logger.info("\n3. 测试Tavily搜索API")
    search_params = {
        'query': '北京天气',
        'api_key': os.getenv('TAVILY_API_KEY')
    }

    try:
        search_url = "https://api.tavily.com/search"
        response = requests.post(search_url, json=search_params, timeout=10)
        logger.info(f"搜索API响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"搜索API返回数据: {list(data.keys())}")
        else:
            logger.error(f"搜索API错误: {response.text}")
    except Exception as e:
        logger.error(f"搜索API异常: {e}")

def test_proxy():
    """测试代理连接"""
    logger.info("\n=== 代理连接测试 ===")

    proxies = {
        'http': 'http://127.0.0.1:7890',
        'https': 'http://127.0.0.1:7890'
    }

    try:
        # 测试通过代理访问百度
        response = requests.get(
            'https://www.baidu.com',
            proxies=proxies,
            timeout=10
        )
        logger.info(f"代理连接测试成功: {response.status_code}")
    except Exception as e:
        logger.error(f"代理连接失败: {e}")

def test_client_with_debug():
    """使用客户端并启用详细调试"""
    logger.info("\n=== 客户端调试测试 ===")

    # 导入客户端
    from src.api.config import APIConfig
    from src.api.weather_client import WeatherClient
    from src.api.map_client import MapClient
    from src.api.search_client import SearchClient

    # 配置日志
    logging.getLogger('src.api').setLevel(logging.DEBUG)
    logging.getLogger('src.api.utils').setLevel(logging.DEBUG)

    # 测试天气客户端
    logger.info("\n1. 测试WeatherClient")
    try:
        config = APIConfig.from_env('.env')
        weather = WeatherClient(config)
        result = weather.get_weather_3d('北京')
        logger.info(f"WeatherClient成功获取数据: {type(result)}")
    except Exception as e:
        logger.error(f"WeatherClient失败: {e}")

    # 测试地图客户端
    logger.info("\n2. 测试MapClient")
    try:
        config = APIConfig.from_env('.env')
        map_client = MapClient(config)
        result = map_client.geocode('北京市朝阳区')
        logger.info(f"MapClient成功获取数据: {type(result)}")
    except Exception as e:
        logger.error(f"MapClient失败: {e}")

if __name__ == "__main__":
    test_direct_api_call()
    test_proxy()
    test_client_with_debug()