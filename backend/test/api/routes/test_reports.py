"""
报告 API 路由测试
================

注意：完整的集成测试需要 MongoDB 数据库环境。
当前测试仅验证 API 文档和路由注册。
"""

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
