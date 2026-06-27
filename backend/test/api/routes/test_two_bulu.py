"""两步路授权 API 测试。"""

from pathlib import Path

from fastapi.testclient import TestClient

from src.schemas.base import Point3D
from src.schemas.track import TrackAnalysisResult
from src.schemas.two_bulu import TwoBuluSessionState, TwoBuluSessionStatus


def test_inspect_two_bulu_url(client: TestClient) -> None:
    response = client.post(
        "/api/v1/two-bulu/inspect",
        json={
            "url": "https://www.2bulu.com/track/t-PFdvTj7brIjp%25252FR2KBg5Tzw%25253D%25253D.htm#"
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["track_id"] == "PFdvTj7brIjp/R2KBg5Tzw=="
    assert data["authorization_required"] is True


def test_create_browser_authorization_session(client: TestClient, mocker) -> None:
    status = TwoBuluSessionStatus(
        session_id="session-1",
        track_id="PFdvTj7brIjp/R2KBg5Tzw==",
        state=TwoBuluSessionState.WAITING_LOGIN,
        message="授权窗口已打开，请扫码登录",
    )
    mocker.patch(
        "src.api.routes.two_bulu.session_manager.create",
        return_value=status,
    )

    response = client.post(
        "/api/v1/two-bulu/sessions",
        json={
            "url": "https://www.2bulu.com/track/t-PFdvTj7brIjp%25252FR2KBg5Tzw%25253D%25253D.htm#"
        },
    )

    assert response.status_code == 201
    assert response.json()["state"] == "waiting_login"


def test_plan_rejects_unfinished_browser_session(client: TestClient, mocker) -> None:
    mocker.patch(
        "src.api.routes.plan.session_manager.get_download_path",
        side_effect=RuntimeError("授权尚未完成"),
    )

    response = client.post(
        "/api/v1/plan/generate",
        json={
            "two_bulu_url": "https://www.2bulu.com/track/t-PFdvTj7brIjp%25252FR2KBg5Tzw%25253D%25253D.htm#",
            "two_bulu_session_id": "session-1",
            "trip_date": None,
            "departure_point": None,
            "api_config": {},
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "授权尚未完成"


def test_plan_uses_downloaded_session_file(client: TestClient, mocker, tmp_path: Path) -> None:
    track_path = tmp_path / "track.gpx"
    track_path.write_text("<gpx></gpx>", encoding="utf-8")
    point = Point3D(lat=30.0, lon=120.0, elevation=100.0)
    analysis = TrackAnalysisResult(
        track_name="测试线路",
        total_distance_km=1.0,
        total_ascent_m=10.0,
        total_descent_m=10.0,
        max_elevation_m=100.0,
        min_elevation_m=90.0,
        avg_elevation_m=95.0,
        start_point=point,
        end_point=point,
        max_elev_point=point,
        min_elev_point=point,
        terrain_analysis=[],
        difficulty_score=10.0,
        difficulty_level="简单",
        estimated_duration_hours=1.0,
        safety_risk="低风险",
        track_points_count=2,
    )
    mocker.patch(
        "src.api.routes.plan.session_manager.get_download_path",
        return_value=track_path,
    )
    mocker.patch("src.api.routes.plan.TrackService.analyze", return_value=analysis)

    response = client.post(
        "/api/v1/plan/generate",
        json={
            "two_bulu_url": "https://www.2bulu.com/track/t-PFdvTj7brIjp%25252FR2KBg5Tzw%25253D%25253D.htm#",
            "two_bulu_session_id": "session-1",
            "trip_date": None,
            "departure_point": None,
            "api_config": {},
        },
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "track_only"
