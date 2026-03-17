"""
提示词管理模块
==============

集中管理所有 LLM 提示词，支持灵活配置和修改。

使用方式：
    from src.prompts import get_prompt_manager, get_system_prompt, get_user_prompt

    # 获取提示词管理器
    manager = get_prompt_manager()

    # 获取系统提示词
    system_prompt = get_system_prompt()

    # 获取用户提示词
    user_prompt = get_user_prompt(
        raw_request="...",
        track_info={...},
        hourly_weather_data="...",
        grid_points_data="...",
        search_content="...",
        rescue_content="..."
    )
"""

from .prompt_manager import (
    PromptManager,
    get_prompt_manager,
    get_system_prompt,
    get_user_prompt
)

__all__ = [
    "PromptManager",
    "get_prompt_manager",
    "get_system_prompt",
    "get_user_prompt",
]
