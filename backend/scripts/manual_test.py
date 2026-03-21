#!/usr/bin/env python3
"""
手动API测试
用于逐个测试API
"""

import sys
import requests
sys.path.append('..')

# 直接读取.env文件获取API密钥
def load_env(file_path='../.env'):
    env_vars = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                env_vars[key] = value.strip()
    return env_vars

env = load_env()

def test_weather_api():
    """测试天气API"""
    print("\n=== 测试和风天气API ===")
    print(f"API Key: {env.get('QWEATHER_API_KEY', 'Not set')}")
    print(f"Host: {env.get('WEATHER_DEVELOPER_HOST', 'devapi')}")

    params = {
        'location': '101010100',  # 北京
        'key': env.get('QWEATHER_API_KEY'),
        'lang': 'zh'
    }

    url = f"https://{env.get('WEATHER_DEVELOPER_HOST', 'devapi')}.qweatherapi.com/v7/weather/3d"
    print(f"URL: {url}")
    print(f"请求参数: {params}")

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_map_api():
    """测试高德地图API"""
    print("\n=== 测试高德地图API ===")
    print(f"API Key: {env.get('AMAP_API_KEY', 'Not set')}")

    params = {
        'address': '北京市朝阳区',
        'key': env.get('AMAP_API_KEY'),
        'output': 'JSON'
    }

    url = "https://restapi.amap.com/v3/geocode/geo"
    print(f"URL: {url}")
    print(f"请求参数: {params}")

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_tavily_api():
    """测试Tavily搜索API"""
    print("\n=== 测试Tavily搜索API ===")
    print(f"API Key: {env.get('TAVILY_API_KEY', 'Not set')}")

    data = {
        'query': '北京天气',
        'api_key': env.get('TAVILY_API_KEY')
    }

    url = "https://api.tavily.com/search"
    print(f"URL: {url}")
    print(f"请求数据: query={data['query']}")

    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    print("=" * 50)
    print("手动API测试")
    print("=" * 50)

    # 可以选择性地测试
    print("\n选择要测试的API:")
    print("1. 天气API")
    print("2. 地图API")
    print("3. Tavily搜索API")
    print("4. 全部测试")
    print("0. 退出")

    choice = input("\n请输入选项 (0-4): ").strip()

    if choice == '1':
        test_weather_api()
    elif choice == '2':
        test_map_api()
    elif choice == '3':
        test_tavily_api()
    elif choice == '4':
        results = {
            '天气API': test_weather_api(),
            '地图API': test_map_api(),
            'TavilyAPI': test_tavily_api()
        }
        print("\n=== 测试结果 ===")
        for api, success in results.items():
            print(f"{api}: {'✓ 成功' if success else '✗ 失败'}")
    elif choice == '0':
        print("退出")
    else:
        print("无效选项")

if __name__ == "__main__":
    main()