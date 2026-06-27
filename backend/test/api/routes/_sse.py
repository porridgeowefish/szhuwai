"""解析 /plan/generate SSE 事件流的测试辅助函数。"""

import json
from typing import Any


def parse_sse_event(text: str, event: str) -> dict[str, Any]:
    """从 SSE 事件流文本中提取指定事件的 data 字典；找不到则抛 AssertionError。"""
    for block in text.split("\n\n"):
        name = ""
        data_lines: list[str] = []
        for line in block.split("\n"):
            if line.startswith("event:"):
                name = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:"):].strip())
        if name == event and data_lines:
            return json.loads("\n".join(data_lines))
    raise AssertionError(f"SSE 流中未找到 {event} 事件")
