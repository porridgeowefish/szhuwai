"""两步路线路解析测试。"""

import pytest

from src.services.two_bulu_service import TwoBuluError, TwoBuluService


def test_extracts_multiply_encoded_track_id() -> None:
    url = "https://www.2bulu.com/track/t-PFdvTj7brIjp%25252FR2KBg5Tzw%25253D%25253D.htm#"

    assert TwoBuluService.extract_track_id(url) == "PFdvTj7brIjp/R2KBg5Tzw=="


def test_builds_stable_track_information() -> None:
    result = TwoBuluService().inspect(
        "https://www.2bulu.com/track/t-PFdvTj7brIjp%25252FR2KBg5Tzw%25253D%25253D.htm#"
    )

    assert result.authorization_required is True
    assert result.track_id == "PFdvTj7brIjp/R2KBg5Tzw=="
    assert "授权窗口" in result.message


def test_rejects_non_two_bulu_url() -> None:
    with pytest.raises(TwoBuluError):
        TwoBuluService.extract_track_id("https://example.com/track/t-abc.htm")
