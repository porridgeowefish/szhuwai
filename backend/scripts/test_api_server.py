"""
测试 FastAPI 服务器启动

使用方法:
    python test_api_server.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# 测试导入
print("测试模块导入...")

try:
    from fastapi import FastAPI  # noqa: F401
    from fastapi.middleware.cors import CORSMiddleware  # noqa: F401
    print("  - FastAPI: OK")
except ImportError as e:
    print(f"  - FastAPI: FAILED - {e}")
    sys.exit(1)

try:
    from src.domain.orchestrator import OutdoorPlannerRouter  # noqa: F401
    print("  - OutdoorPlannerRouter: OK")
except ImportError as e:
    print(f"  - OutdoorPlannerRouter: FAILED - {e}")
    sys.exit(1)

try:
    from src.schemas.output import OutdoorActivityPlan  # noqa: F401
    print("  - OutdoorActivityPlan: OK")
except ImportError as e:
    print(f"  - OutdoorActivityPlan: FAILED - {e}")
    sys.exit(1)

# 测试应用创建
print("\n测试应用创建...")
try:
    from main import app
    print("  - FastAPI app: OK")

    # 检查路由
    routes = [route.path for route in app.routes if hasattr(route, 'path')]
    print(f"  - 已注册路由: {len(routes)}")
    for route in routes:
        print(f"    - {route}")

except Exception as e:
    print(f"  - FastAPI app: FAILED - {e}")
    sys.exit(1)

print("\n所有测试通过!")
print("\n启动服务器命令:")
print("  uvicorn main:app --reload --port 8000")