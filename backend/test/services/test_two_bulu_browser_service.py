"""两步路浏览器授权会话测试。"""

import time
from pathlib import Path

import pytest

from src.schemas.two_bulu import TwoBuluSessionState
from src.services.two_bulu_browser_service import (
    BrowserUnavailableError,
    TwoBuluBrowserSessionManager,
)


def test_rejects_session_when_browser_is_unavailable(tmp_path: Path) -> None:
    manager = TwoBuluBrowserSessionManager(
        workspace=tmp_path,
        browser_locator=lambda: None,
    )

    with pytest.raises(BrowserUnavailableError, match="Chrome"):
        manager.create("https://www.2bulu.com/track/t-abc.htm")


def test_returns_ready_download_path(tmp_path: Path) -> None:
    manager = TwoBuluBrowserSessionManager(
        workspace=tmp_path,
        browser_locator=lambda: Path("chrome.exe"),
    )
    track_path = tmp_path / "track.kml"
    track_path.write_text("<kml />", encoding="utf-8")
    manager._register_for_test(
        session_id="session-1",
        track_id="abc",
        state=TwoBuluSessionState.READY,
        download_path=track_path,
    )

    assert manager.get_download_path("session-1") == track_path


def test_rejects_download_path_before_session_is_ready(tmp_path: Path) -> None:
    manager = TwoBuluBrowserSessionManager(
        workspace=tmp_path,
        browser_locator=lambda: Path("chrome.exe"),
    )
    manager._register_for_test(
        session_id="session-1",
        track_id="abc",
        state=TwoBuluSessionState.WAITING_CAPTCHA,
    )

    with pytest.raises(RuntimeError, match="验证码"):
        manager.get_download_path("session-1")


def test_looks_like_track_classifies_files(tmp_path: Path) -> None:
    """_looks_like_track：合法 KML/GPX 通过；空文件/HTML 错误页被拒。"""
    coords = b"116.0,40.0,100 116.1,40.1,110 116.2,40.2,120 116.3,40.3,130 116.4,40.4,140"
    valid_kml = tmp_path / "ok.kml"
    valid_kml.write_bytes(
        b'<?xml version="1.0"?><kml xmlns="x"><Document><Placemark><LineString>'
        b'<coordinates>' + coords + b'</coordinates></LineString></Placemark></Document></kml>'
    )
    valid_gpx = tmp_path / "ok.gpx"
    valid_gpx.write_bytes(b'<gpx version="1.1"><trk><trkseg><trkpt lat="40" lon="116"></trkpt></trkseg></trk>' + b' ' * 300 + b'</gpx>')
    empty = tmp_path / "empty.kml"
    empty.write_bytes(b"")
    html_error = tmp_path / "err.kml"
    html_error.write_bytes(b"<html><body>403 Forbidden</body></html>" + b"x" * 300)

    assert TwoBuluBrowserSessionManager._looks_like_track(valid_kml) is True
    assert TwoBuluBrowserSessionManager._looks_like_track(valid_gpx) is True
    assert TwoBuluBrowserSessionManager._looks_like_track(empty) is False
    assert TwoBuluBrowserSessionManager._looks_like_track(html_error) is False


def test_mark_ready_rejects_invalid_download(tmp_path: Path) -> None:
    """残缺/错误下载文件不应被标记为 READY。"""
    manager = TwoBuluBrowserSessionManager(
        workspace=tmp_path,
        browser_locator=lambda: Path("chrome.exe"),
    )
    manager._register_for_test(
        session_id="s1",
        track_id="abc",
        state=TwoBuluSessionState.WAITING_CAPTCHA,
    )
    bad = tmp_path / "bad.kml"
    bad.write_bytes(b"<html>download error page</html>" + b"x" * 300)

    with pytest.raises(RuntimeError, match="不完整或格式异常"):
        manager._mark_ready("s1", bad)
    assert manager.get("s1").state is not TwoBuluSessionState.READY


def test_cleanup_stale_removes_old_session_and_dir(tmp_path: Path) -> None:
    """超过 TTL 的旧会话及其下载目录应被清理。"""
    manager = TwoBuluBrowserSessionManager(
        workspace=tmp_path,
        browser_locator=lambda: Path("chrome.exe"),
    )
    manager._register_for_test(
        session_id="old",
        track_id="abc",
        state=TwoBuluSessionState.READY,
    )
    old_dir = tmp_path / "downloads" / "old"
    old_dir.mkdir(parents=True)
    (old_dir / "track.kml").write_bytes(b"<kml/>")
    manager._sessions["old"].download_dir = old_dir
    manager._sessions["old"].created_at = time.monotonic() - 25 * 3600

    manager._cleanup_stale(max_age_seconds=24 * 3600)

    assert "old" not in manager._sessions
    assert not old_dir.exists()
