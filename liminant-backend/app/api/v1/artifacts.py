from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])


class SaveArtifactRequest(BaseModel):
    session_id: str
    path: str
    content: str
    artifact_type: str = "file"
    summary: str = ""


@router.post("")
async def save_artifact(req: SaveArtifactRequest):
    from app.utils.artifact_store import get_artifact_storage
    storage = get_artifact_storage()
    result = await storage.save(
        session_id=req.session_id,
        path=req.path,
        content=req.content,
        artifact_type=req.artifact_type,
        summary=req.summary,
    )
    return {"artifact": result}


@router.get("/session/{session_id}")
async def list_session_artifacts(session_id: str):
    from app.utils.artifact_store import get_artifact_storage
    storage = get_artifact_storage()
    artifacts = await storage.list_session(session_id)
    return {"artifacts": artifacts}


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: str):
    from app.utils.artifact_store import get_artifact_storage
    storage = get_artifact_storage()
    result = await storage.load(artifact_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    content, meta = result
    return {"content": content, "meta": meta}


@router.get("/{artifact_id}/versions")
async def get_artifact_versions(artifact_id: str):
    from app.utils.artifact_store import get_artifact_storage
    storage = get_artifact_storage()
    versions = await storage.diff_versions(artifact_id)
    return {"versions": versions}


@router.get("/path/{session_id}")
async def get_artifact_by_path(session_id: str, path: str):
    from app.utils.artifact_store import get_artifact_storage
    storage = get_artifact_storage()
    result = await storage.load_by_path(session_id, path)
    if result is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    content, meta = result
    return {"content": content, "meta": meta}
