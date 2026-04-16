"""LangGraph Agent 状态定义"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class ConversationMeta(TypedDict):
    session_id: str
    user_id: int
    created_at: str
    plan_title: Optional[str]


class ToolResult(TypedDict):
    tool_name: str
    status: str  # "success" | "error"
    data: Any
    display_type: Optional[str]


class AgentState(TypedDict):
    """LangGraph Agent 状态"""
    messages: Annotated[List[BaseMessage], add_messages]
    conversation_meta: ConversationMeta
    tool_results: List[ToolResult]
    active_plan: Optional[Dict[str, Any]]
    user_preferences: Optional[Dict[str, Any]]
