"""核心策划系统测试夹具。"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def client() -> TestClient:
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """为轨迹解析测试提供隔离目录。"""

    return tmp_path


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "api: 外部 API 相关测试")
    config.addinivalue_line("markers", "integration: 集成测试")
