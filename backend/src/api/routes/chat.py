"""Chat API 端点 — SSE 流式传输"""

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sse_starlette import EventSourceResponse
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from loguru import logger

from src.api.deps import CurrentUser
from src.agent.graph import create_outdoor_agent
from src.agent.system_prompt import AGENT_SYSTEM_PROMPT
from src.agent.session import SessionManager
from src.infrastructure.redis_client import get_redis

router = APIRouter(prefix="/chat", tags=["智能对话"])

TEMP_TRACKS_DIR = Path("temp_tracks")


class CreateSessionResponse(BaseModel):
    session_id: str
    created_at: str


def get_session_manager() -> SessionManager:
    redis = get_redis()
    return SessionManager(redis)


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    user: CurrentUser,
    sm: SessionManager = Depends(get_session_manager),
):
    """创建新的聊天会话"""
    from datetime import datetime

    session_id = str(uuid.uuid4())
    sm.create_session(session_id, user.id)
    return CreateSessionResponse(
        session_id=session_id,
        created_at=datetime.now().isoformat(),
    )


@router.get("/sessions")
async def list_sessions(
    user: CurrentUser,
    sm: SessionManager = Depends(get_session_manager),
):
    """获取用户的会话列表"""
    sessions = sm.get_user_sessions(user.id)
    return {"data": sessions}


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    user: CurrentUser,
    request: Request,
    sm: SessionManager = Depends(get_session_manager),
):
    """发送消息并流式返回 Agent 响应（SSE）"""
    session = sm.get_session(session_id, user.id)
    if not session:
        raise HTTPException(404, "会话不存在")

    body = await request.json()
    user_message = body.get("message", "")
    if not user_message.strip():
        raise HTTPException(400, "消息不能为空")

    sm.append_message(session_id, "user", user_message)

    history = sm.get_messages(session_id)
    messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT)]
    messages.extend(history)

    agent = create_outdoor_agent()
    full_response = []

    async def event_generator():
        try:
            async for event in agent.astream_events(
                {"messages": messages},
                config={"configurable": {"thread_id": session_id}},
                version="v2",
            ):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    token = event["data"]["chunk"].content
                    if token:
                        full_response.append(token)
                        yield {
                            "event": "token",
                            "data": json.dumps({"content": token}, ensure_ascii=False),
                        }
                elif kind == "on_tool_start":
                    yield {
                        "event": "tool_start",
                        "data": json.dumps(
                            {"tool": event["name"], "input": str(event["data"].get("input", ""))[:500]},
                            ensure_ascii=False,
                        ),
                    }
                elif kind == "on_tool_end":
                    yield {
                        "event": "tool_end",
                        "data": json.dumps(
                            {"tool": event["name"], "output": str(event["data"].get("output", ""))[:500]},
                            ensure_ascii=False,
                        ),
                    }

            yield {"event": "done", "data": "{}"}
            sm.append_message(session_id, "assistant", "".join(full_response))
        except Exception as e:
            logger.error(f"SSE 流式传输错误: {e}")
            yield {"event": "error", "data": json.dumps({"message": "生成回复时出错"}, ensure_ascii=False)}

    return EventSourceResponse(event_generator())


@router.post("/sessions/{session_id}/upload")
async def upload_track(
    session_id: str,
    user: CurrentUser,
    file: UploadFile = File(...),
    sm: SessionManager = Depends(get_session_manager),
):
    """上传轨迹文件并关联到会话"""
    session = sm.get_session(session_id, user.id)
    if not session:
        raise HTTPException(404, "会话不存在")

    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in [".gpx", ".kml"]:
        raise HTTPException(400, f"不支持的文件格式: {file_ext}")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "文件大小不能超过 10MB")

    TEMP_TRACKS_DIR.mkdir(exist_ok=True)
    temp_path = TEMP_TRACKS_DIR / f"{session_id}_{uuid.uuid4()}{file_ext}"
    temp_path.write_bytes(content)

    sm.set_attachment(session_id, "track_file", str(temp_path))

    return {"data": {"file_path": str(temp_path), "filename": file.filename}}
