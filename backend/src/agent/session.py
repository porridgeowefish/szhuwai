"""Redis 会话管理器"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage


MESSAGE_TYPES = {
    "user": HumanMessage,
    "assistant": AIMessage,
    "system": SystemMessage,
}

DEFAULT_SESSION_TTL = 86400  # 24 小时


class SessionManager:
    """管理 Redis 中的聊天会话"""

    def __init__(self, redis_client, ttl: int = DEFAULT_SESSION_TTL):
        self.redis = redis_client
        self.ttl = ttl

    def create_session(self, session_id: str, user_id: int) -> None:
        meta = json.dumps(
            {"user_id": user_id, "created_at": datetime.now().isoformat()},
            ensure_ascii=False,
        )
        self.redis.set(f"session:{session_id}:meta", meta, ex=self.ttl)
        self.redis.set(
            f"user:{user_id}:sessions:{session_id}", meta, ex=self.ttl
        )
        self.redis.set(
            f"session:{session_id}:messages", json.dumps([]), ex=self.ttl
        )

    def get_session(self, session_id: str, user_id: int) -> Optional[Dict]:
        raw = self.redis.get(f"session:{session_id}:meta")
        if not raw:
            return None
        meta = json.loads(raw)
        if meta.get("user_id") != user_id:
            return None
        return meta

    def get_user_sessions(self, user_id: int) -> List[Dict]:
        return []

    def get_messages(self, session_id: str) -> List[BaseMessage]:
        raw = self.redis.get(f"session:{session_id}:messages")
        if not raw:
            return []
        messages_data = json.loads(raw)
        return self._deserialize_messages(messages_data)

    def append_message(self, session_id: str, role: str, content: str) -> None:
        raw = self.redis.get(f"session:{session_id}:messages")
        messages = json.loads(raw) if raw else []
        messages.append({"role": role, "content": content})
        self.redis.set(
            f"session:{session_id}:messages",
            json.dumps(messages, ensure_ascii=False),
            ex=self.ttl,
        )

    def set_attachment(self, session_id: str, key: str, value: str) -> None:
        self.redis.set(f"session:{session_id}:attachment:{key}", value, ex=self.ttl)

    def get_attachment(self, session_id: str, key: str) -> Optional[str]:
        return self.redis.get(f"session:{session_id}:attachment:{key}")

    def delete_session(self, session_id: str) -> None:
        for suffix in ["meta", "messages"]:
            self.redis.delete(f"session:{session_id}:{suffix}")

    def _deserialize_messages(self, messages_data: List[Dict]) -> List[BaseMessage]:
        result = []
        for msg in messages_data:
            cls = MESSAGE_TYPES.get(msg.get("role", "user"), HumanMessage)
            result.append(cls(content=msg["content"]))
        return result
