"""
获取短信验证码脚本
==================

从 Redis 中读取指定手机号和场景的验证码，用于开发测试。

用法:
    python scripts/get_sms_code.py 13800138000 login
    python scripts/get_sms_code.py 13800138000 register
"""

import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.api.config import api_config
from src.infrastructure.redis_client import init_redis


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/get_sms_code.py <手机号> [场景]")
        print("场景: login, register, bind, unbind, reset_password")
        sys.exit(1)

    phone = sys.argv[1]
    scene = sys.argv[2] if len(sys.argv) > 2 else "login"

    # 初始化 Redis
    redis_client = init_redis(api_config)

    # 查询验证码
    key = f"sms:code:{phone}:{scene}"
    code = redis_client.get(key)

    if code:
        print(f"验证码: {code}")
        print(f"手机号: {phone}")
        print(f"场景: {scene}")

        # 查询剩余 TTL
        ttl = redis_client.ttl(key)
        if isinstance(ttl, int) and ttl > 0:
            print(f"剩余有效时间: {ttl} 秒")
    else:
        print(f"未找到验证码 (手机: {phone}, 场景: {scene})")
        print("可能原因:")
        print("  1. 验证码已过期")
        print("  2. 验证码已被使用")
        print("  3. 验证码尚未发送")
        sys.exit(1)


if __name__ == "__main__":
    main()
