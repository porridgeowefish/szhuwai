"""
提示词管理模块
==============

集中管理所有 LLM 提示词，支持灵活配置和修改。
"""

from .equipment_prompts import EquipmentPromptManager, get_equipment_prompt
from .llm_prompts import LLMPromptManager, get_system_prompt, get_user_prompt

__all__ = [
    "EquipmentPromptManager",
    "get_equipment_prompt",
    "LLMPromptManager",
    "get_system_prompt",
    "get_user_prompt",
]
