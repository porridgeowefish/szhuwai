"""通过可见浏览器完成两步路登录与轨迹下载。

系统不会识别、绕过或代替用户完成验证码。用户在独立浏览器窗口中完成
扫码登录和验证码后，服务仅监听浏览器产生的 KML/GPX 下载文件。

使用 nodriver（反检测浏览器）替代 Selenium，规避"用户异常"风控；
登录态通过持久化 user-data-dir 复用，多数情况下免重复扫码。
"""

from __future__ import annotations

import asyncio
import os
import shutil
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import Future
from dataclasses import dataclass, field
from pathlib import Path

import nodriver as uc

from src.schemas.two_bulu import TwoBuluSessionState, TwoBuluSessionStatus
from src.services.two_bulu_service import TwoBuluService


class BrowserUnavailableError(RuntimeError):
    """本机没有可用于交互授权的浏览器。"""


@dataclass
class _BrowserSession:
    session_id: str
    source_url: str
    track_id: str
    state: TwoBuluSessionState
    message: str
    download_dir: Path
    download_path: Path | None = None
    created_at: float = field(default_factory=time.monotonic)

    def to_status(self) -> TwoBuluSessionStatus:
        return TwoBuluSessionStatus(
            session_id=self.session_id,
            track_id=self.track_id,
            state=self.state,
            message=self.message,
            file_name=self.download_path.name if self.download_path else None,
        )


def locate_chromium_browser() -> Path | None:
    """查找 Windows 上常见的 Chrome 或 Edge。"""

    configured = os.getenv("TWO_BULU_BROWSER_PATH")
    candidates = [
        Path(configured) if configured else None,
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    ]
    return next((path for path in candidates if path and path.is_file()), None)


class TwoBuluBrowserSessionManager:
    """维护单个可见浏览器授权任务，避免资料目录并发冲突。

    nodriver 为 async-only，故在后台守护线程内运行独立事件循环，通过
    run_coroutine_threadsafe 桥接同步的公开 API（create/get/shutdown）。
    """

    def __init__(
        self,
        workspace: Path,
        browser_locator: Callable[[], Path | None] = locate_chromium_browser,
        timeout_seconds: int = 900,
    ) -> None:
        self.workspace = workspace
        self.browser_locator = browser_locator
        self.timeout_seconds = timeout_seconds
        self._sessions: dict[str, _BrowserSession] = {}
        self._browsers: dict[str, uc.Browser] = {}
        self._futures: dict[str, Future[None]] = {}
        self._lock = threading.Lock()
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._loop.run_forever,
            daemon=True,
            name="two-bulu-loop",
        )
        self._loop_thread.start()

    def create(self, raw_url: str) -> TwoBuluSessionStatus:
        browser_path = self.browser_locator()
        if browser_path is None:
            raise BrowserUnavailableError(
                "未找到 Chrome 或 Edge。浏览器授权仅支持带桌面的本地运行环境。"
            )

        track_id = TwoBuluService.extract_track_id(raw_url)
        self._cleanup_stale()  # 顺带清理过期会话与下载目录，防泄漏
        session_id = uuid.uuid4().hex
        download_dir = self.workspace / "downloads" / session_id
        download_dir.mkdir(parents=True, exist_ok=True)
        session = _BrowserSession(
            session_id=session_id,
            source_url=raw_url,
            track_id=track_id,
            state=TwoBuluSessionState.STARTING,
            message="正在打开两步路授权窗口…",
            download_dir=download_dir,
        )
        with self._lock:
            if any(
                item.state
                not in {TwoBuluSessionState.READY, TwoBuluSessionState.FAILED}
                for item in self._sessions.values()
            ):
                raise RuntimeError("已有一个授权窗口正在运行，请先完成当前线路")
            self._sessions[session_id] = session

        future = asyncio.run_coroutine_threadsafe(
            self._run_async(session_id, browser_path),
            self._loop,
        )
        with self._lock:
            self._futures[session_id] = future
        return session.to_status()

    def get(self, session_id: str) -> TwoBuluSessionStatus:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError("授权会话不存在或已失效")
            return session.to_status()

    def get_download_path(self, session_id: str, expected_track_id: str | None = None) -> Path:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise RuntimeError("授权会话不存在或已失效，请重新打开授权窗口")
            if expected_track_id and session.track_id != expected_track_id:
                raise RuntimeError("授权会话与当前两步路线路不匹配")
            if session.state is not TwoBuluSessionState.READY or not session.download_path:
                raise RuntimeError(session.message)
            if not session.download_path.is_file():
                raise RuntimeError("轨迹下载文件已失效，请重新授权")
            return session.download_path

    def _cleanup_stale(self, max_age_seconds: int = 24 * 3600) -> None:
        """清理超过 max_age 的旧会话并删除其下载目录，防止磁盘/内存无限增长。"""
        cutoff = time.monotonic() - max_age_seconds
        with self._lock:
            stale_ids = [sid for sid, s in self._sessions.items() if s.created_at < cutoff]
            stale_sessions = [self._sessions.pop(sid, None) for sid in stale_ids]
        for session in stale_sessions:
            if session is not None:
                shutil.rmtree(session.download_dir, ignore_errors=True)

    def shutdown(self) -> None:
        """关闭本服务创建的浏览器并停止事件循环，不影响用户自己的浏览器窗口。"""

        with self._lock:
            browsers = list(self._browsers.values())
            self._browsers.clear()
            self._futures.clear()
        for browser in browsers:
            try:
                browser.stop()
            except Exception:  # noqa: BLE001 - 清理期间任何异常都不应阻断后续关闭
                pass
        # 停事件循环并等待线程退出，避免僵尸 Chrome 与多 worker profile 锁冲突
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._loop_thread.join(timeout=5)

    def _update(
        self,
        session_id: str,
        state: TwoBuluSessionState,
        message: str,
        download_path: Path | None = None,
    ) -> None:
        with self._lock:
            session = self._sessions[session_id]
            session.state = state
            session.message = message
            if download_path is not None:
                session.download_path = download_path

    async def _run_async(self, session_id: str, browser_path: Path) -> None:
        browser: uc.Browser | None = None
        try:
            session = self._sessions[session_id]
            browser = await self._start_browser(browser_path)
            with self._lock:
                self._browsers[session_id] = browser
            tab = await browser.get(session.source_url)
            await tab.set_download_path(str(session.download_dir.resolve()))

            if not await self._is_logged_in(tab):
                self._update(
                    session_id,
                    TwoBuluSessionState.WAITING_LOGIN,
                    "请在已打开的浏览器中扫码登录两步路；窗口会保留登录状态。",
                )
                await self._click_download_entry(tab)

            deadline = time.monotonic() + self.timeout_seconds
            while time.monotonic() < deadline and not await self._is_logged_in(tab):
                downloaded = self._find_download(session.download_dir)
                if downloaded:
                    self._mark_ready(session_id, downloaded)
                    return
                await asyncio.sleep(1)

            if not await self._is_logged_in(tab):
                raise TimeoutError("等待扫码登录超时，请重新打开授权窗口")

            self._update(
                session_id,
                TwoBuluSessionState.DOWNLOADING,
                "登录成功，正在请求 KML 轨迹…",
            )
            await self._click_download_entry(tab)
            await self._click_track_download_tab(tab)
            await self._click_kml_option(tab)
            self._update(
                session_id,
                TwoBuluSessionState.WAITING_CAPTCHA,
                "如页面出现滑块，请在浏览器中手动完成；系统不会绕过验证码。",
            )

            while time.monotonic() < deadline:
                downloaded = self._find_download(session.download_dir)
                if downloaded:
                    self._mark_ready(session_id, downloaded)
                    return
                await asyncio.sleep(1)
            raise TimeoutError("等待轨迹下载超时，请重新授权")
        except Exception as exc:  # noqa: BLE001 - 守护任务不得静默崩溃，必须记录 FAILED
            self._update(session_id, TwoBuluSessionState.FAILED, f"授权失败：{exc}")
        finally:
            with self._lock:
                self._browsers.pop(session_id, None)
                self._futures.pop(session_id, None)
            if browser is not None:
                try:
                    browser.stop()
                except Exception:  # noqa: BLE001
                    pass

    async def _start_browser(self, browser_path: Path) -> uc.Browser:
        """启动反检测浏览器，复用持久化 profile 以保留登录态。"""

        return await uc.start(
            browser_executable_path=str(browser_path),
            user_data_dir=str(self.workspace / "browser-profile"),
            headless=False,
            lang="zh-CN",
        )

    @staticmethod
    async def _js_click(tab: uc.Tab, selector: str, timeout: float) -> bool:
        """等待选择器出现后用 JS 触发点击（稳健，规避"元素不可交互"）。"""

        try:
            await tab.wait_for(selector=selector, timeout=timeout)
        except Exception:  # noqa: BLE001 - 元素未出现视为未命中，交由调用方决定
            return False
        try:
            await tab.evaluate(
                f"(()=>{{const el=document.querySelector({selector!r}); if(el) el.click();}})()"
            )
            return True
        except Exception:  # noqa: BLE001
            return False

    @staticmethod
    async def _click_download_entry(tab: uc.Tab) -> None:
        await TwoBuluBrowserSessionManager._js_click(
            tab, "#pointPannel a.btn_orange", timeout=5
        )

    @staticmethod
    async def _click_track_download_tab(tab: uc.Tab) -> None:
        await TwoBuluBrowserSessionManager._js_click(
            tab, ".alert > .tab li:nth-child(2)", timeout=10
        )

    @staticmethod
    async def _click_kml_option(tab: uc.Tab) -> None:
        """触发 KML 下载。

        优先直接调用页面函数 downloadTrack(1)（比点击选择器更稳，不依赖 DOM 结构），
        会弹出阿里云滑块验证码，由用户在浏览器窗口手动完成。
        """

        called = await tab.evaluate(
            "(() => { if (typeof downloadTrack === 'function') { downloadTrack(1);"
            " return true; } return false; })()",
            return_by_value=True,
        )
        if called:
            return
        if not await TwoBuluBrowserSessionManager._js_click(
            tab, ".alert .download p.p2", timeout=20
        ):
            raise RuntimeError("未找到 KML 下载入口，可能是两步路页面结构已变化")

    @staticmethod
    async def _is_logged_in(tab: uc.Tab) -> bool:
        try:
            result = await tab.evaluate(
                "(() => (typeof userId !== 'undefined' && String(userId).length > 0))()",
                return_by_value=True,
            )
        except Exception:  # noqa: BLE001 - 页面未就绪等异常一律视为未登录
            return False
        return bool(result)

    @staticmethod
    def _find_download(download_dir: Path) -> Path | None:
        if any(download_dir.glob("*.crdownload")):
            return None
        files = [
            *download_dir.glob("*.kml"),
            *download_dir.glob("*.gpx"),
        ]
        return max(files, key=lambda path: path.stat().st_mtime) if files else None

    def _mark_ready(self, session_id: str, path: Path) -> None:
        if path.stat().st_size > 20 * 1024 * 1024:
            raise RuntimeError("轨迹文件超过 20MB 限制")
        if not self._looks_like_track(path):
            raise RuntimeError("下载文件不完整或格式异常，请重新授权下载")
        self._update(
            session_id,
            TwoBuluSessionState.READY,
            "轨迹已自动下载，可以开始分析。",
            path,
        )

    @staticmethod
    def _looks_like_track(path: Path) -> bool:
        """快速校验：文件非空且根元素是 <kml>/<gpx>，过滤残缺/错误下载。"""
        try:
            if path.stat().st_size < 200:
                return False
            head = path.read_bytes()[:4096]
        except OSError:
            return False
        return b"<kml" in head or b"<gpx" in head

    def _register_for_test(
        self,
        session_id: str,
        track_id: str,
        state: TwoBuluSessionState,
        download_path: Path | None = None,
    ) -> None:
        """仅供单元测试注册无浏览器会话。"""

        messages = {
            TwoBuluSessionState.READY: "轨迹已自动下载，可以开始分析。",
            TwoBuluSessionState.WAITING_CAPTCHA: "请在浏览器中手动完成验证码。",
        }
        self._sessions[session_id] = _BrowserSession(
            session_id=session_id,
            source_url="https://www.2bulu.com/track/t-test.htm",
            track_id=track_id,
            state=state,
            message=messages.get(state, "授权处理中"),
            download_dir=self.workspace,
            download_path=download_path,
        )


session_manager = TwoBuluBrowserSessionManager(
    workspace=Path(__file__).resolve().parents[3] / ".tmp" / "two-bulu",
)
