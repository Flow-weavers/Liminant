from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.timeline import SessionTimeline
from app.utils.json_storage import get_storage

router = APIRouter(prefix="/api/v1/timeline", tags=["timeline"])

storage = get_storage()


class AddEventRequest(BaseModel):
    event_type: str
    description: str
    metadata: dict = {}


@router.get("/session/{session_id}")
async def get_timeline(session_id: str):
    data = await storage.read("timelines", session_id)
    if data is None:
        return {"session_id": session_id, "events": [], "total_events": 0}
    timeline = SessionTimeline.from_dict(data)
    return timeline.to_dict()


@router.post("/session/{session_id}/events")
async def add_event(session_id: str, req: AddEventRequest):
    data = await storage.read("timelines", session_id)
    if data is None:
        timeline = SessionTimeline(session_id=session_id)
    else:
        timeline = SessionTimeline.from_dict(data)

    event = timeline.add(req.event_type, req.description, req.metadata)
    await storage.write("timelines", session_id, timeline.to_dict())
    return {"event": event}


@router.delete("/session/{session_id}")
async def clear_timeline(session_id: str):
    await storage.delete("timelines", session_id)
    return {"deleted": True}
