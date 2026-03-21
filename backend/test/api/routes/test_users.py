"""
用户管理 API 路由测试
===================
"""

from fastapi.testclient import TestClient


class TestUsersRoutes:
    """用户管理 API 测试"""

    def test_list_users_as_admin(self, client: TestClient, create_test_user):
        """测试管理员获取用户列表"""
        # 创建管理员用户
        _ = create_test_user(username="admin", password="admin123", role="admin")

        # 创建一些普通用户
        create_test_user(username="user1", password="pass123")
        create_test_user(username="user2", password="pass123")

        # 管理员登录
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        token = response.json()["data"]["accessToken"]

        # 获取用户列表
        response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert "data" in data

        users_data = data["data"]
        assert "list" in users_data
        assert "pagination" in users_data

        # 应该至少有 3 个用户（admin + user1 + user2）
        assert len(users_data["list"]) >= 3
        assert users_data["pagination"]["total"] >= 3

    def test_list_users_as_normal_user(self, client: TestClient, create_test_user):
        """测试普通用户获取用户列表（应失败）"""
        # 创建普通用户
        _ = create_test_user(username="normaluser", password="pass123", role="user")

        # 登录
        response = client.post("/api/v1/auth/login", json={
            "username": "normaluser",
            "password": "pass123"
        })
        assert response.status_code == 200
        token = response.json()["data"]["accessToken"]

        # 尝试获取用户列表
        response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    def test_list_users_unauthorized(self, client: TestClient):
        """测试未授权访问用户列表"""
        response = client.get("/api/v1/users")
        assert response.status_code == 401

    def test_update_status_success(self, client: TestClient, create_test_user):
        """测试更新用户状态成功"""
        # 创建管理员
        _ = create_test_user(username="admin", password="admin123", role="admin")

        # 创建普通用户
        target_user = create_test_user(username="targetuser", password="pass123", status="active")

        # 管理员登录
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = response.json()["data"]["accessToken"]

        # 禁用用户
        response = client.patch(
            f"/api/v1/users/{target_user.id}/status",
            json={"status": "disabled"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "disabled"

    def test_update_status_cannot_disable_self(self, client: TestClient, create_test_user):
        """测试不能禁用自己"""
        # 创建管理员
        admin = create_test_user(username="admin", password="admin123", role="admin")

        # 管理员登录
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = response.json()["data"]["accessToken"]

        # 尝试禁用自己
        response = client.patch(
            f"/api/v1/users/{admin.id}/status",
            json={"status": "disabled"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400

        data = response.json()
        assert "不能禁用自己" in data["detail"]["message"]

    def test_update_status_invalid_status(self, client: TestClient, create_test_user):
        """测试无效状态值"""
        # 创建管理员
        _ = create_test_user(username="admin", password="admin123", role="admin")

        # 创建普通用户
        target_user = create_test_user(username="targetuser", password="pass123")

        # 管理员登录
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = response.json()["data"]["accessToken"]

        # 尝试设置无效状态
        response = client.patch(
            f"/api/v1/users/{target_user.id}/status",
            json={"status": "invalid_status"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400

    def test_update_status_user_not_found(self, client: TestClient, create_test_user):
        """测试更新不存在的用户"""
        # 创建管理员
        _ = create_test_user(username="admin", password="admin123", role="admin")

        # 管理员登录
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = response.json()["data"]["accessToken"]

        # 尝试更新不存在的用户
        response = client.patch(
            "/api/v1/users/99999/status",
            json={"status": "disabled"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    def test_update_status_unauthorized(self, client: TestClient, create_test_user):
        """测试未授权更新用户状态"""
        response = client.patch("/api/v1/users/1/status", json={"status": "disabled"})
        assert response.status_code == 401

    def test_users_routes_in_openapi(self, client: TestClient):
        """测试用户管理路由在 OpenAPI 文档中"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        paths = schema.get("paths", {})

        # 检查用户路由存在
        assert "/api/v1/users" in paths
        assert "get" in paths["/api/v1/users"]

        # 检查更新状态路由
        status_paths = [p for p in paths.keys() if p.startswith("/api/v1/users/{user_id}/status")]
        assert len(status_paths) > 0
        assert "patch" in paths[status_paths[0]]

    def test_users_routes_have_tags(self, client: TestClient):
        """测试用户管理路由有正确的标签"""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema.get("paths", {})

        # 检查用户路由标签
        for path_key in ["/api/v1/users", "/api/v1/users/{user_id}/status"]:
            path_data = paths.get(path_key, {})
            for method in path_data.values():
                tags = method.get("tags", [])
                assert "用户管理" in tags or len(tags) > 0
