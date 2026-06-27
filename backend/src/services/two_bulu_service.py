"""两步路线路 URL 解析。"""

from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

from src.schemas.two_bulu import TwoBuluTrackInfo


class TwoBuluError(ValueError):
    """两步路线路无法解析。"""


class TwoBuluService:
    """只解析稳定信息，不假定二维码能够授权下载。"""

    base_url = "https://www.2bulu.com"

    @staticmethod
    def extract_track_id(raw_url: str) -> str:
        """从详情页或 App URL 中还原多层编码的 trackId。"""

        parsed = urlparse(raw_url.strip())
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "2bulu.com",
            "www.2bulu.com",
        }:
            raise TwoBuluError("请输入 www.2bulu.com 的线路页面 URL")

        query_match = re.search(r"(?:[?&]trackId=)([^&#]+)", raw_url, re.IGNORECASE)
        if query_match:
            candidate = query_match.group(1)
        else:
            path_match = re.search(r"/track/t-(.+?)\.htm", parsed.path, re.IGNORECASE)
            if not path_match:
                raise TwoBuluError("未在线路 URL 中找到 trackId")
            candidate = path_match.group(1)

        for _ in range(6):
            decoded = unquote(candidate)
            if decoded == candidate:
                break
            candidate = decoded

        candidate = candidate.strip()
        if not candidate or len(candidate) > 256:
            raise TwoBuluError("trackId 无效")
        return candidate

    def inspect(self, raw_url: str) -> TwoBuluTrackInfo:
        """返回线路入口；轨迹必须通过真实浏览器会话取得。"""

        track_id = self.extract_track_id(raw_url)
        return TwoBuluTrackInfo(
            source_url=raw_url,
            track_id=track_id,
            message="线路已识别。打开授权窗口，扫码登录并按页面提示完成人工验证。",
        )
