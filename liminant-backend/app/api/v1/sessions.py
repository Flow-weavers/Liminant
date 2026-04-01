import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, AsyncIterator
from starlette.responses import StreamingResponse

from app.models.session import Session, SessionCreate, SessionUpdateConstraints
from app.models.message import Message, MessageCreate, MessageRole
from app.services.session_manager import SessionManager
from app.services.pipeline_event_bus import PipelineEventBus, PipelineStageEvent

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
    tools_used: list = []
    reasoning: dict = {}
    phase: str = "idle"


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

    session = await sm.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = await sm.add_message(session_id, MessageCreate(
        content=req.content,
        role=req.role,
        attachments=req.attachments,
    ))

    agent = CoordinatorAgent()

    agent_input = {
        "messages": [m.to_dict() for m in (await sm.get_messages(session_id) or [])],
        "session": session.to_dict(),
    }

    agent_output = await agent.run(agent_input)
    response_text = agent_output.get("response", "")
    tools_used = agent_output.get("tools_used", [])
    reasoning = agent_output.get("reasoning", {})
    phase = agent_output.get("phase", "idle")

    assistant_msg = await sm.add_message(session_id, MessageCreate(
        content=response_text,
        role=MessageRole.ASSISTANT,
    ))

    if assistant_msg and reasoning:
        session = await sm.get(session_id)
        if session and session.messages:
            last = session.messages[-1]
            last["ancestry"] = {
                "kb_entries": reasoning.get("kb_entries", []),
                "applied_constraints": reasoning.get("applied_constraints", []),
                "pipeline_stage": reasoning.get("pipeline_stage", 0),
                "phase": reasoning.get("phase", "idle"),
                "pipeline_complete": reasoning.get("pipeline_complete", False),
                "tools_used": tools_used,
            }
            session.updated_at = datetime.utcnow()
            await sm.storage.write("sessions", session.id, session.to_dict())

    session = await sm.get(session_id)
    return SendMessageResponse(
        message=assistant_msg,
        response_content=response_text,
        session=session,
        tools_used=tools_used,
        reasoning=reasoning,
        phase=phase,
    )


@router.get("/{session_id}/stream")
async def stream_session(session_id: str):
    session = await sm.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    event_queue: list[PipelineStageEvent] = []
    queue_lock_event = asyncio.Event()

    bus = PipelineEventBus.get_instance()

    def enqueue(event: PipelineStageEvent) -> None:
        event_queue.append(event)
        queue_lock_event.set()

    bus.subscribe(session_id, enqueue)

    async def event_generator() -> AsyncIterator[str]:
        import json
        yield f"event: connected\ndata: {json.dumps({'session_id': session_id})}\n\n"

        try:
            while True:
                await queue_lock_event.wait()
                queue_lock_event.clear()

                while event_queue:
                    event = event_queue.pop(0)
                    yield f"event: pipeline\ndata: {json.dumps(event.to_dict())}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            bus.unsubscribe(session_id, enqueue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.patch("/{session_id}/constraints")
async def update_constraints(session_id: str, data: SessionUpdateConstraints):
    session = await sm.update_constraints(session_id, data)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@router.get("/{session_id}/export")
async def export_session(session_id: str):
    session = await sm.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    from app.models.artifact import ArtifactService
    artifact_service = ArtifactService()
    artifacts = await artifact_service.list_by_session(session_id)

    from app.models.knowledge import KnowledgeEntry
    from app.services.knowledge_base import KnowledgeBase
    kb = KnowledgeBase()

    session_data = session.to_dict()
    session_data["artifacts"] = [a.to_dict() for a in artifacts]

    kb_entries = []
    for kb_id in session.constraints.knowledge_refs:
        entry = await kb.get(kb_id)
        if entry:
            kb_entries.append(entry.to_dict())

    return {
        "version": "1.0",
        "exported_at": session.updated_at.isoformat(),
        "session": session_data,
        "knowledge_base_entries": kb_entries,
    }


class ImportPayload(BaseModel):
    session: dict
    knowledge_base_entries: list[dict] | None = None


@router.post("/import")
async def import_session(payload: ImportPayload):
    from app.models.artifact import ArtifactService
    artifact_service = ArtifactService()

    imported_session = await sm.create(None)
    session_dict = payload.session

    imported_session.state.phase = session_dict.get("state", {}).get("phase", "planning")
    imported_session.context.working_directory = session_dict.get("context", {}).get("working_directory", "/workspace/default")
    imported_session.context.language = session_dict.get("context", {}).get("language", "en-US")
    imported_session.messages = session_dict.get("messages", [])
    imported_session.artifacts = session_dict.get("artifacts", [])

    await sm.storage.write("sessions", imported_session.id, imported_session.to_dict())

    for art_data in imported_session.artifacts:
        from app.models.artifact import Artifact
        art = Artifact(**art_data)
        await artifact_service.save(art)

    if payload.knowledge_base_entries:
        from app.services.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        id_map: dict[str, str] = {}
        for entry_data in payload.knowledge_base_entries:
            old_id = entry_data.get("id", "")
            entry_data.pop("id", None)
            new_entry = await kb.create(type=entry_data.get("type"), title=entry_data.get("content", {}).get("title", ""), body=entry_data.get("content", {}).get("body", ""), tags=entry_data.get("metadata", {}).get("tags", []), keywords=entry_data.get("triggers", {}).get("keywords", []))
            id_map[old_id] = new_entry.id

        for rule_id in imported_session.constraints.knowledge_refs:
            if rule_id in id_map:
                await imported_session.add_knowledge_ref(id_map[rule_id])

    return {"session_id": imported_session.id, "status": "imported"}
