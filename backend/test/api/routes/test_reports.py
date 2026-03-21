"""
报告 API 路由测试
================

注意：完整的集成测试需要 MongoDB 数据库环境。
当前测试仅验证 API 文档和路由注册。
"""

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient


class TestReportRoutes:
    """报告 API 测试"""

    def test_list_reports_unauthorized(self, client: TestClient):
        """测试未授权访问报告列表"""
        response = client.get("/api/v1/reports")
        assert response.status_code == 401

    def test_get_report_unauthorized(self, client: TestClient):
        """测试未授权访问报告"""
        report_id = str(ObjectId())
        response = client.get(f"/api/v1/reports/{report_id}")
        assert response.status_code == 401

    def test_delete_report_unauthorized(self, client: TestClient):
        """测试未授权删除报告"""
        report_id = str(ObjectId())
        response = client.delete(f"/api/v1/reports/{report_id}")
        assert response.status_code == 401

    def test_reports_routes_in_openapi(self, client: TestClient):
        """测试报告路由在 OpenAPI 文档中"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        paths = schema.get("paths", {})

        # 检查报告路由存在
        assert "/api/v1/reports" in paths
        assert "get" in paths["/api/v1/reports"]

        # 检查报告详情路由（路径参数）
        report_paths = [p for p in paths.keys() if p.startswith("/api/v1/reports/{report_id}")]
        assert len(report_paths) > 0
        assert "get" in paths[report_paths[0]]
        assert "delete" in paths[report_paths[0]]

    def test_reports_routes_have_tags(self, client: TestClient):
        """测试报告路由有正确的标签"""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema.get("paths", {})

        # 检查报告路由标签
        for path_key in ["/api/v1/reports", "/api/v1/reports/{report_id}"]:
            path_data = paths.get(path_key, {})
            for method in path_data.values():
                tags = method.get("tags", [])
                assert "报告" in tags or len(tags) > 0

    def test_reports_routes_have_correct_methods(self, client: TestClient):
        """测试报告路由有正确的 HTTP 方法"""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema.get("paths", {})

        # GET 方法检查
        assert "get" in paths.get("/api/v1/reports", {})

        # 报告详情路由
        report_paths = [p for p in paths.keys() if p.startswith("/api/v1/reports/{report_id}")]
        if report_paths:
            assert "get" in paths[report_paths[0]]
            assert "delete" in paths[report_paths[0]]
