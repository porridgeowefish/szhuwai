#!/usr/bin/env python3
"""
API端点测试脚本
测试所有API端点的可访问性
"""

import sys
sys.path.append('..')

from src.api.config import APIConfig
from src.api.weather_client import WeatherClient
from src.api.map_client import MapClient
from src.api.search_client import SearchClient
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_weather_api():
    """测试天气API"""
    logger.info("=== 测试天气API ===")
    try:
        config = APIConfig.from_env('.env')
        weather = WeatherClient(config)

        # 测试获取北京3天天气预报
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
        config = APIConfig.from_env('.env')
        map_client = MapClient(config)

        # 测试地理编码
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
        config = APIConfig.from_env('.env')
        search = SearchClient(config)

        # 测试搜索
        results = search.search("北京天气")
        logger.info(f"✓ 搜索API成功，返回了{len(results)}个结果")
        return True
    except Exception as e:
        logger.error(f"✗ 搜索API失败: {e}")
        return False

def test_fastapi_server():
    """测试FastAPI服务器"""
    logger.info("=== 测试FastAPI服务器 ===")
    try:
        import requests

        # 启动测试服务器（如果需要）
        # 这里只是检查端点响应

        # 测试健康检查端点
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("✓ FastAPI服务器健康检查通过")
            return True
        else:
            logger.warning(f"FastAPI服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"无法连接到FastAPI服务器: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始API端点测试...")

    results = {
        'weather': test_weather_api(),
        'map': test_map_api(),
        'search': test_search_api(),
        'fastapi': test_fastapi_server()
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