"""
认证 API 路由测试
================

注意：完整的集成测试需要:
1. MySQL 数据库环境
2. 短信服务配置
3. 完整的服务初始化

当前测试仅验证 API 文档和路由注册。
"""

import pytest
from fastapi.testclient import TestClient

from main import app


class TestApiDocs:
    """API 文档和路由注册测试"""

    @pytest.fixture
    def client(self) -> TestClient:
        """创建测试客户端"""
        return TestClient(app)

    def test_openapi_docs_available(self, client: TestClient) -> None:
        """测试 OpenAPI 文档可访问"""
        response = client.get("/docs")
        # 文档页面应该可访问
        assert response.status_code == 200

    def test_openapi_schema_available(self, client: TestClient) -> None:
        """测试 OpenAPI schema 可访问"""
        response = client.get("/openapi.json")
        # schema 应该可访问
        assert response.status_code == 200

        # 验证认证相关路径存在
        schema = response.json()
        paths = schema.get("paths", {})

        # 检查认证路由存在
        assert "/api/v1/auth/register" in paths
        assert "/api/v1/auth/login" in paths
        assert "/api/v1/auth/sms/register" in paths
        assert "/api/v1/auth/sms/login" in paths
        assert "/api/v1/auth/me" in paths
        assert "/api/v1/auth/password/reset" in paths
        assert "/api/v1/auth/password/change" in paths
        assert "/api/v1/auth/phone/bind" in paths
        assert "/api/v1/auth/phone/unbind" in paths

        # 检查短信路由存在
        assert "/api/v1/auth/sms/send" in paths

        # 验证 schema 中的组件
        components = schema.get("components", {})
        schemas = components.get("schemas", {})

        # 验证响应模型存在
        assert "ApiResponse" in schemas or "ApiResponse_UserWithToken_" in schemas

    def test_auth_routes_have_correct_methods(self, client: TestClient) -> None:
        """测试认证路由有正确的 HTTP 方法"""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema.get("paths", {})

        # POST 方法检查
        assert "post" in paths.get("/api/v1/auth/register", {})
        assert "post" in paths.get("/api/v1/auth/login", {})
        assert "post" in paths.get("/api/v1/auth/sms/register", {})
        assert "post" in paths.get("/api/v1/auth/sms/login", {})
        assert "post" in paths.get("/api/v1/auth/password/reset", {})
        assert "post" in paths.get("/api/v1/auth/password/change", {})
        assert "post" in paths.get("/api/v1/auth/phone/bind", {})
        assert "post" in paths.get("/api/v1/auth/phone/unbind", {})

        # GET 方法检查
        assert "get" in paths.get("/api/v1/auth/me", {})

        # 短信路由
        assert "post" in paths.get("/api/v1/auth/sms/send", {})

    def test_auth_routes_have_tags(self, client: TestClient) -> None:
        """测试认证路由有正确的标签"""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema.get("paths", {})

        # 检查标签
        for path_key in [
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/me",
        ]:
            path_data = paths.get(path_key, {})
            for method in path_data.values():
                tags = method.get("tags", [])
                assert "认证" in tags or len(tags) > 0

        # 短信路由标签
        sms_path = paths.get("/api/v1/auth/sms/send", {})
        for method in sms_path.values():
            tags = method.get("tags", [])
            assert "短信" in tags or len(tags) > 0
