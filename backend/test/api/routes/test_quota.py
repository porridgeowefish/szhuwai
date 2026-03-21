"""
额度 API 路由测试
================
"""


from fastapi.testclient import TestClient


class TestQuotaRoutes:
    """额度 API 测试"""

    def test_get_quota_normal_user(self, client: TestClient, create_test_user):
        """测试普通用户获取额度"""
        # 创建普通用户
        _ = create_test_user(username="normaluser", password="pass123", role="user")

        # 登录获取 token
        response = client.post("/api/v1/auth/login", json={
            "username": "normaluser",
            "password": "pass123"
        })
        assert response.status_code == 200
        token = response.json()["data"]["accessToken"]

        # 获取额度
        response = client.get("/api/v1/quota", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "success"
        assert "data" in data

        quota = data["data"]
        assert "used" in quota
        assert "total" in quota
        assert "remaining" in quota
        assert "resetAt" in quota

        # 普通用户应该有总额度限制
        assert quota["total"] == 2
        assert quota["remaining"] >= 0

    def test_get_quota_admin_user(self, client: TestClient, create_test_user):
        """测试管理员获取额度（无限制）"""
        # 创建管理员用户
        _ = create_test_user(username="admin", password="admin123", role="admin")

        # 登录获取 token
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        token = response.json()["data"]["accessToken"]

        # 获取额度
        response = client.get("/api/v1/quota", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200

        quota = data["data"]
        # 管理员应该显示无限制额度
        assert quota["total"] == -1
        assert quota["remaining"] == -1

    def test_get_quota_unauthorized(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/v1/quota")
        assert response.status_code == 401

        data = response.json()
        assert "detail" in data

    def test_get_quota_invalid_token(self, client: TestClient):
        """测试无效 Token"""
        response = client.get("/api/v1/quota", headers={
            "Authorization": "Bearer invalid_token_12345"
        })
        assert response.status_code == 401

    def test_quota_routes_in_openapi(self, client: TestClient):
        """测试额度路由在 OpenAPI 文档中"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        paths = schema.get("paths", {})

        # 检查额度路由存在
        assert "/api/v1/quota" in paths
        assert "get" in paths["/api/v1/quota"]
