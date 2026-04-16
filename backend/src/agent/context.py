"""上下文构建与摘要压缩"""

import json
from typing import List, Optional
from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, BaseMessage
)
from src.agent.session import SessionManager


class ContextManager:
    """管理对话上下文，处理摘要压缩"""

    def __init__(self, session_manager: SessionManager, max_turns: int = 20, summary_threshold: int = 10):
        self.session_manager = session_manager
        self.max_turns = max_turns
        self.summary_threshold = summary_threshold

    def build_messages_for_llm(
        self,
        session_id: str,
        new_user_message: str,
        system_prompt: str,
    ) -> List[BaseMessage]:
        """构建完整的 LLM 消息列表

        结构：[SystemPrompt] + [摘要（如果压缩）] + [最近N轮] + [新消息]
        """
        messages = [SystemMessage(content=system_prompt)]

        raw_history = self.session_manager.get_messages(session_id)

        if len(raw_history) > self.summary_threshold:
            old_turns = raw_history[: -self.max_turns]
            recent_turns = raw_history[-self.max_turns:]

            summary = self._summarize_old_turns(old_turns)
            if summary:
                messages.append(SystemMessage(content=f"以下是之前对话的摘要：\n{summary}"))

            messages.extend(recent_turns)
        else:
            messages.extend(raw_history)

        messages.append(HumanMessage(content=new_user_message))
        return messages

    def _summarize_old_turns(self, turns: List[BaseMessage]) -> str:
        """压缩旧轮次为摘要（简单实现，后续可替换为 LLM 摘要）"""
        parts = []
        for msg in turns[-10:]:
            if isinstance(msg, HumanMessage):
                parts.append(f"用户: {msg.content[:100]}")
            elif isinstance(msg, AIMessage):
                parts.append(f"助手: {msg.content[:100]}")
        return "\n".join(parts)
