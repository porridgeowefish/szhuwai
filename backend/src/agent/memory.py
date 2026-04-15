"""MongoDB 长期记忆 — 用户偏好存储"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger


class UserMemoryStore:
    """存储长期用户偏好和历史到 MongoDB

    Collection: user_memory
    Document: {user_id, preferences, extracted_facts, updated_at}
    """

    COLLECTION = "user_memory"

    def __init__(self, mongo_db):
        self.collection = mongo_db[self.COLLECTION]

    def get_preferences(self, user_id: int) -> Dict[str, Any]:
        doc = self.collection.find_one({"user_id": user_id})
        if doc:
            return doc.get("preferences", {})
        return {}

    def update_preferences(self, user_id: int, preferences: Dict[str, Any]) -> None:
        self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"preferences": preferences, "updated_at": datetime.now()}},
            upsert=True,
        )

    def add_extracted_fact(self, user_id: int, fact: str) -> None:
        self.collection.update_one(
            {"user_id": user_id},
            {"$push": {"extracted_facts": {"fact": fact, "at": datetime.now().isoformat()}}},
            upsert=True,
        )

    def get_context_for_prompt(self, user_id: int) -> str:
        prefs = self.get_preferences(user_id)
        if not prefs:
            return ""
        parts = ["已知用户偏好："]
        for k, v in prefs.items():
            parts.append(f"- {k}: {v}")
        return "\n".join(parts)
