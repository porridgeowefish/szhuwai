#!/usr/bin/env python3
"""
修复后的API测试脚本
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

def test_weather_api():
    """测试天气API"""
    logger.info("=== 测试天气API ===")
    try:
        from src.api.config import APIConfig
        from src.api.weather_client import WeatherClient

        config = APIConfig.from_env('.env')
        logger.info(f"天气API配置 - URL: {config.WEATHER_BASE_URL}")
        logger.info(f"天气API配置 - Host: {getattr(config, 'WEATHER_DEVELOPER_HOST', 'devapi')}")

        weather = WeatherClient(config)
        result = weather.get_weather_3d('北京')
        logger.info(f"✓ 天气API成功，返回了{len(result.daily)}天的预报")
        return True
    except Exception as e:
        logger.error(f"✗ 天气API失败: {e}")
        return False

def test_map_api():
    """测试地图API"""
    logger.info("=== 测试地图API ===")
    try:
        from src.api.config import APIConfig
        from src.api.map_client import MapClient

        config = APIConfig.from_env('.env')
        logger.info(f"地图API配置 - Key: {config.MAP_API_KEY[:10] + '...' if config.MAP_API_KEY else 'Not set'}")

        map_client = MapClient(config)
        result = map_client.geocode('北京市朝阳区')
        logger.info(f"✓ 地图API成功，返回了{len(result.geocodes)}个结果")
        return True
    except Exception as e:
        logger.error(f"✗ 地图API失败: {e}")
        return False

def test_search_api():
    """测试搜索API"""
    logger.info("=== 测试搜索API ===")
    try:
        from src.api.config import APIConfig
        from src.api.search_client import SearchClient

        config = APIConfig.from_env('.env')
        logger.info(f"搜索API配置 - Key: {config.SEARCH_API_KEY[:10] + '...' if config.SEARCH_API_KEY else 'Not set'}")

        search = SearchClient(config)
        result = search.search("北京天气")
        logger.info(f"✓ 搜索API成功")
        return True
    except Exception as e:
        logger.error(f"✗ 搜索API失败: {e}")
        return False

def test_direct_calls():
    """直接测试API调用"""
    logger.info("\n=== 直接API调用测试 ===")

    # 测试天气API
    logger.info("\n1. 测试和风天气API（直接调用）")
    weather_params = {
        'location': '101010100',  # 北京
        'key': os.getenv('QWEATHER_API_KEY'),
        'lang': 'zh'
    }

    try:
        response = requests.get(
            "https://devapi.qweatherapi.com/v7/weather/3d",
            params=weather_params,
            timeout=10
        )
        logger.info(f"天气API响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✓ 天气API成功: {data.get('fxLink', 'N/A')}")
        else:
            logger.error(f"✗ 天气API失败: {response.text}")
    except Exception as e:
        logger.error(f"✗ 天气API异常: {e}")

    # 测试高德地图API
    logger.info("\n2. 测试高德地图API（直接调用）")
    map_params = {
        'address': '北京市朝阳区',
        'key': os.getenv('AMAP_API_KEY'),
        'output': 'JSON'
    }

    try:
        response = requests.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params=map_params,
            timeout=10
        )
        logger.info(f"地图API响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1':
                logger.info(f"✓ 地图API成功: {len(data.get('geocodes', []))}个结果")
            else:
                logger.error(f"✗ 地图API失败: {data.get('info', 'Unknown error')}")
        else:
            logger.error(f"✗ 地图API失败: {response.text}")
    except Exception as e:
        logger.error(f"✗ 地图API异常: {e}")

    # 测试Tavily搜索API
    logger.info("\n3. 测试Tavily搜索API（直接调用）")
    search_data = {
        'query': '北京天气',
        'api_key': os.getenv('TAVILY_API_KEY')
    }

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json=search_data,
            timeout=10
        )
        logger.info(f"搜索API响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✓ 搜索API成功: {len(data.get('results', []))}个结果")
        else:
            logger.error(f"✗ 搜索API失败: {response.text}")
    except Exception as e:
        logger.error(f"✗ 搜索API异常: {e}")

def main():
    """主函数"""
    logger.info("开始API测试（修复版本）...")

    # 直接调用测试
    test_direct_calls()

    # 客户端测试
    results = {
        'weather': test_weather_api(),
        'map': test_map_api(),
        'search': test_search_api()
    }

    logger.info("\n=== 测试结果汇总 ===")
    for api, success in results.items():
        status = "✓ 通过" if success else "✗ 失败"
        logger.info(f"{api.upper()}: {status}")

    total = len(results)
    passed = sum(results.values())
    logger.info(f"\n总计: {passed}/{total} 个API通过测试")

    if passed == total:
        logger.info("🎉 所有API测试通过！")
    else:
        logger.warning(f"⚠️  有{total - passed}个API测试失败")

if __name__ == "__main__":
    main()