from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.knowledge import KnowledgeEntry, KnowledgeCreate
from app.services.knowledge_base import KnowledgeBase

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

kb = KnowledgeBase()


class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    session_type: str | None = None


@router.post("", response_model=dict)
async def create_knowledge(data: KnowledgeCreate):
    entry = await kb.create(data)
    return {"entry": entry.to_dict()}


@router.get("")
async def list_knowledge(pending: bool | None = None):
    all_entries = await kb.list_entries()
    if pending is not None:
        all_entries = [e for e in all_entries if e.metadata.pending_review == pending]
    return {"entries": [e.to_dict() for e in all_entries]}


@router.get("/search")
async def search_knowledge(query: str, limit: int = 10, session_type: str | None = None):
    results = await kb.search(query, limit, session_type)
    return {"results": [r.to_dict() for r in results]}


@router.get("/{kb_id}")
async def get_knowledge(kb_id: str):
    entry = await kb.get(kb_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return entry.to_dict()


@router.put("/{kb_id}")
async def update_knowledge(kb_id: str, data: dict):
    entry = await kb.update(kb_id, data)
    if entry is None:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return {"entry": entry.to_dict()}


@router.post("/{kb_id}/confirm")
async def confirm_knowledge(kb_id: str):
    entry = await kb.update(kb_id, {
        "metadata": {"pending_review": False, "confidence": 0.9}
    })
    if entry is None:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return {"entry": entry.to_dict()}


@router.delete("/{kb_id}")
async def delete_knowledge(kb_id: str):
    deleted = await kb.delete(kb_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return {"deleted": True}


@router.get("/statistics")
async def get_knowledge_statistics():
    stats = await kb.get_statistics()
    return stats
