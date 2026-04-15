"""LangGraph Agent 图定义

图结构: agent_node → [有 tool_calls?] → tool_node → agent_node → ...
                                 ↓ [无 tool_calls]
                                END
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI

from src.agent.state import AgentState
from src.agent.tools import get_all_tools
from src.api.config import api_config


def _get_llm():
    """创建 LLM 实例，复用现有 SiliconFlow 配置"""
    base_url = api_config.LLM_BASE_URL
    if base_url.endswith("/chat/completions"):
        base_url = base_url[: -len("/chat/completions")]

    return ChatOpenAI(
        model=api_config.LLM_MODEL,
        temperature=api_config.LLM_TEMPERATURE,
        max_tokens=api_config.LLM_MAX_TOKENS,
        api_key=api_config.LLM_API_KEY,
        base_url=base_url,
    )


def create_outdoor_agent():
    """创建并编译 Outdoor Agent 图"""
    tools = get_all_tools()
    llm = _get_llm()
    llm_with_tools = llm.bind_tools(tools) if tools else llm

    def agent_node(state: AgentState) -> dict:
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    tool_node = ToolNode(tools) if tools else None

    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)

    if tool_node:
        graph.add_node("tools", tool_node)
        graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
        graph.add_edge("tools", "agent")
    else:
        graph.add_conditional_edges("agent", should_continue, {END: END})

    graph.set_entry_point("agent")
    return graph.compile()
