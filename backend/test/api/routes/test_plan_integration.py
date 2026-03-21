"""
generate-plan 集成测试
=====================

测试改造后的 /api/v1/generate-plan API，包括：
- 认证要求
- 额度检查
- 报告保存
"""

import io
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestGeneratePlanIntegration:
    """generate-plan 集成测试"""

    @pytest.fixture
    def mock_planner(self, mocker):
        """Mock 户外规划器"""
        mock_planner = mocker.MagicMock()
        mock_planner.execute_planning.return_value = _create_mock_plan()
        mocker.patch("src.api.routes.plan.OutdoorPlannerRouter", return_value=mock_planner)
        return mock_planner

    @pytest.fixture
    def sample_gpx_file(self) -> bytes:
        """生成测试用 GPX 文件"""
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test">
  <trk>
    <name>测试轨迹</name>
    <trkseg>
      <trkpt lat="39.9042" lon="116.4074">
        <ele>50</ele>
      </trkpt>
      <trkpt lat="39.9050" lon="116.4080">
        <ele>55</ele>
      </trkpt>
      <trkpt lat="39.9060" lon="116.4090">
        <ele>60</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""
        return gpx_content.encode("utf-8")

    @pytest.fixture
    def auth_headers(self, client: TestClient) -> dict:
        """创建认证头"""
        # 注册并登录普通用户
        client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "password": "Test@123456"
        })

        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "Test@123456"
        })
        data = response.json()
        token = data["data"]["accessToken"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def admin_headers(self, client: TestClient, create_test_user) -> dict:
        """创建管理员认证头"""
        # 创建管理员用户
        _ = create_test_user(
            username="admin",
            password="admin123",
            role="admin",
            status="active"
        )

        # 登录
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        data = response.json()
        token = data["data"]["accessToken"]
        return {"Authorization": f"Bearer {token}"}

    def test_generate_plan_success(
        self,
        client: TestClient,
        mock_planner,
        auth_headers: dict,
        sample_gpx_file: bytes
    ) -> None:
        """测试生成计划成功"""
        files = {"file": ("test.gpx", io.BytesIO(sample_gpx_file), "application/gpx")}
        data = {
            "trip_date": "2024-04-01",
            "departure_point": "北京市朝阳区",
            "additional_info": "测试补充信息",
            "plan_title": "测试路线",
            "key_destinations": "山顶,风景点"
        }

        response = client.post(
            "/api/v1/plan/generate",
            headers=auth_headers,
            files=files,
            data=data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert "report_id" in result
        assert result["message"] == "计划生成成功"

    def test_generate_plan_unauthorized(
        self,
        client: TestClient,
        mock_planner,
        sample_gpx_file: bytes
    ) -> None:
        """测试未登录"""
        files = {"file": ("test.gpx", io.BytesIO(sample_gpx_file), "application/gpx")}
        data = {
            "trip_date": "2024-04-01",
            "departure_point": "北京市朝阳区",
            "plan_title": "测试路线",
            "key_destinations": "山顶"
        }

        response = client.post(
            "/api/v1/plan/generate",
            files=files,
            data=data
        )

        assert response.status_code == 401

    def test_generate_plan_quota_exhausted(
        self,
        client: TestClient,
        mock_planner,
        auth_headers: dict,
        sample_gpx_file: bytes
    ) -> None:
        """测试额度耗尽"""
        files = {"file": ("test.gpx", io.BytesIO(sample_gpx_file), "application/gpx")}
        data = {
            "trip_date": "2024-04-01",
            "departure_point": "北京市朝阳区",
            "plan_title": "测试路线",
            "key_destinations": "山顶"
        }

        # 使用完默认额度（2次）
        for _ in range(2):
            response = client.post(
                "/api/v1/plan/generate",
                headers=auth_headers,
                files=files,
                data=data
            )
            assert response.status_code == 200

        # 第三次请求应该返回额度不足
        response = client.post(
            "/api/v1/plan/generate",
            headers=auth_headers,
            files=files,
            data=data
        )

        assert response.status_code == 403
        result = response.json()
        assert result["detail"]["code"] == 403003

    def test_generate_plan_quota_consumed(
        self,
        client: TestClient,
        mock_planner,
        auth_headers: dict,
        sample_gpx_file: bytes
    ) -> None:
        """测试额度被消耗（简化版：验证 API 调用成功）"""
        # 生成计划
        files = {"file": ("test.gpx", io.BytesIO(sample_gpx_file), "application/gpx")}
        data = {
            "trip_date": "2024-04-01",
            "departure_point": "北京市朝阳区",
            "plan_title": "测试路线",
            "key_destinations": "山顶"
        }

        # 第一次请求应该成功
        response = client.post(
            "/api/v1/plan/generate",
            headers=auth_headers,
            files=files,
            data=data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "report_id" in result

        # 第二次请求也应该成功（默认额度是 2）
        response2 = client.post(
            "/api/v1/plan/generate",
            headers=auth_headers,
            files=files,
            data=data
        )

        assert response2.status_code == 200

        # 第三次请求应该返回额度不足
        response3 = client.post(
            "/api/v1/plan/generate",
            headers=auth_headers,
            files=files,
            data=data
        )

        assert response3.status_code == 403
        result3 = response3.json()
        assert result3["detail"]["code"] == 403003

    def test_generate_plan_report_saved(
        self,
        client: TestClient,
        mock_planner,
        auth_headers: dict,
        sample_gpx_file: bytes
    ) -> None:
        """测试报告返回 report_id"""
        # 生成计划
        files = {"file": ("test.gpx", io.BytesIO(sample_gpx_file), "application/gpx")}
        data = {
            "trip_date": "2024-04-01",
            "departure_point": "北京市朝阳区",
            "plan_title": "测试路线",
            "key_destinations": "山顶"
        }

        response = client.post(
            "/api/v1/plan/generate",
            headers=auth_headers,
            files=files,
            data=data
        )

        assert response.status_code == 200
        result = response.json()
        report_id = result.get("report_id")

        # 验证响应包含 report_id
        assert report_id is not None
        assert isinstance(report_id, str)
        assert len(report_id) > 0

    def test_generate_plan_admin_unlimited(
        self,
        client: TestClient,
        mock_planner,
        admin_headers: dict,
        sample_gpx_file: bytes
    ) -> None:
        """测试管理员无额度限制"""
        # 管理员应该可以无限次生成计划
        files = {"file": ("test.gpx", io.BytesIO(sample_gpx_file), "application/gpx")}
        data = {
            "trip_date": "2024-04-01",
            "departure_point": "北京市朝阳区",
            "plan_title": "测试路线",
            "key_destinations": "山顶"
        }

        # 多次请求都应该成功
        for _ in range(5):
            response = client.post(
                "/api/v1/plan/generate",
                headers=admin_headers,
                files=files,
                data=data
            )
            assert response.status_code == 200


# ============ 辅助函数 ============

def _create_mock_plan():
    """创建 mock 规划结果"""
    from src.schemas.output import (
        OutdoorActivityPlan,
        ItineraryItem,
        EquipmentItem,
        SafetyAssessment,
        EmergencyRescueContact,
        CityWeatherDaily,
        ScenicSpot,
    )
    from src.schemas.base import Point3D

    return OutdoorActivityPlan(
        plan_id="test-plan-123",
        created_at=datetime.now(timezone.utc),
        plan_name="测试路线",
        overall_rating="推荐",
        track_overview="10.5km/爬升250m",
        weather_overview="晴朗，15~25°C",
        transport_overview="驾车约1.5小时",
        trip_date_weather=CityWeatherDaily(
            fxDate="2024-04-01",
            tempMax=25,
            tempMin=15,
            textDay="晴",
            windScaleDay="3",
            windSpeedDay=15,
            humidity=65,
            precip=0,
            pressure=1013,
            uvIndex=6
        ),
        hourly_weather=[],
        critical_grid_weather=[],
        itinerary=[
            ItineraryItem(
                time="08:00",
                activity="出发",
                location="北京市朝阳区"
            )
        ],
        equipment_recommendations=[
            EquipmentItem(
                name="登山杖",
                category="安全装备",
                priority="推荐"
            )
        ],
        scenic_spots=[
            ScenicSpot(
                name="山顶观景台",
                spot_type="自然风光",
                description="壮观的景色",
                location=Point3D(lat=39.9042, lon=116.4074, elevation=100)
            )
        ],
        precautions=["注意天气变化", "携带足够饮水"],
        hiking_advice="建议早上出发，避开正午高温",
        safety_assessment=SafetyAssessment(
            overall_risk="低风险",
            conditions="天气良好",
            recommendation="推荐"
        ),
        safety_issues=[],
        risk_factors=[],
        emergency_rescue_contacts=[
            EmergencyRescueContact(
                name="急救中心",
                phone="120",
                type="医疗"
            )
        ]
    )
