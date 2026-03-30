from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.models.session import Session, SessionCreate, SessionUpdateConstraints
from app.models.message import Message, MessageCreate, MessageRole
from app.services.session_manager import SessionManager

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])

sm = SessionManager()


class SendMessageRequest(BaseModel):
    content: str
    role: MessageRole = MessageRole.USER
    attachments: list[str] = []


class SendMessageResponse(BaseModel):
    message: Message
    response_content: str
    session: Session


@router.post("", response_model=dict)
async def create_session(data: SessionCreate | None = None):
    session = await sm.create(data or SessionCreate())
    return {"session": session.to_dict()}


@router.get("")
async def list_sessions():
    sessions = await sm.list_sessions()
    return {"sessions": [s.to_dict() for s in sessions]}


@router.get("/{session_id}")
async def get_session(session_id: str):
    session = await sm.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    deleted = await sm.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}


@router.get("/{session_id}/messages")
async def get_messages(session_id: str):
    messages = await sm.get_messages(session_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"messages": [m.to_dict() for m in messages]}


@router.post("/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(session_id: str, req: SendMessageRequest):
    from app.agents.coordinator import CoordinatorAgent
    from app.services.tool_executor import ToolExecutor

    session = await sm.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = await sm.add_message(session_id, MessageCreate(
        content=req.content,
        role=req.role,
        attachments=req.attachments,
    ))

    tool_executor = ToolExecutor()
    agent = CoordinatorAgent()

    tool_names = [t["name"] for t in tool_executor.list_tools()]
    agent_input = {
        "messages": [m.to_dict() for m in (await sm.get_messages(session_id) or [])],
        "context": session.context.model_dump(),
        "tools": tool_names,
    }

    agent_output = await agent.run(agent_input)
    response_text = agent_output.get("response", "")

    assistant_msg = await sm.add_message(session_id, MessageCreate(
        content=response_text,
        role=MessageRole.ASSISTANT,
    ))

    session = await sm.get(session_id)
    return SendMessageResponse(
        message=assistant_msg,
        response_content=response_text,
        session=session,
    )


@router.patch("/{session_id}/constraints")
async def update_constraints(session_id: str, data: SessionUpdateConstraints):
    session = await sm.update_constraints(session_id, data)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@router.get("/{session_id}/artifacts")
async def get_artifacts(session_id: str):
    session = await sm.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"artifacts": session.artifacts}
