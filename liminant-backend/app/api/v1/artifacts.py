from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.artifact import Artifact, ArtifactChangeType, ArtifactService

router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])

artifact_service = ArtifactService()


class ArtifactCreate(BaseModel):
    session_id: str
    path: str
    type: str = "file"
    summary: str = ""


@router.get("", response_model=dict)
async def list_artifacts(session_id: str | None = None):
    if session_id:
        artifacts = await artifact_service.list_by_session(session_id)
    else:
        artifacts = await artifact_service.list_recent()
    return {"artifacts": [a.to_dict() for a in artifacts]}


@router.post("", response_model=dict)
async def create_artifact(data: ArtifactCreate):
    artifact = Artifact(
        session_id=data.session_id,
        path=data.path,
        type=data.type,
        summary=data.summary,
    )
    saved = await artifact_service.save(artifact)
    return {"artifact": saved.to_dict()}


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: str):
    artifact = await artifact_service.get(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact.to_dict()


@router.delete("/{artifact_id}")
async def delete_artifact(artifact_id: str):
    deleted = await artifact_service.delete(artifact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"deleted": True}


@router.get("/{artifact_id}/history")
async def get_artifact_history(artifact_id: str):
    artifact = await artifact_service.get(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {
        "artifact_id": artifact.id,
        "path": artifact.path,
        "changes": [c.model_dump(mode="json") for c in artifact.changes],
    }


@router.post("/{artifact_id}/restore/{change_index}")
async def restore_change(artifact_id: str, change_index: int):
    artifact = await artifact_service.get(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    if change_index < 0 or change_index >= len(artifact.changes):
        raise HTTPException(status_code=400, detail="Change index out of range")

    change = artifact.changes[change_index]
    if change.type == ArtifactChangeType.DELETE:
        raise HTTPException(status_code=400, detail="Cannot restore a deletion")

    return {
        "artifact_id": artifact.id,
        "change_index": change_index,
        "description": f"Would restore to state after change #{change_index + 1}",
        "diff": change.diff,
    }
