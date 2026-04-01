from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class ArtifactChangeType(str, Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class ArtifactChange(BaseModel):
    type: ArtifactChangeType = ArtifactChangeType.CREATE
    description: str = ""
    diff: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: f"art_{uuid.uuid4().hex[:12]}")
    type: str = "file"
    path: str = ""
    summary: str = ""
    session_id: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    changes: list[ArtifactChange] = Field(default_factory=list)

    def to_dict(self) -> dict:
        data = self.model_dump(mode="json")
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        for c in data.get("changes", []):
            if isinstance(c.get("timestamp"), datetime):
                c["timestamp"] = c["timestamp"].isoformat()
        return data

    def add_change(self, change_type: ArtifactChangeType, description: str, diff: str) -> None:
        self.changes.append(ArtifactChange(
            type=change_type,
            description=description,
            diff=diff,
            timestamp=datetime.utcnow(),
        ))
        self.updated_at = datetime.utcnow()


class ArtifactService:
    def __init__(self):
        self.storage_key = "artifacts"

    async def save(self, artifact: Artifact) -> Artifact:
        from app.utils.json_storage import get_storage
        storage = get_storage()
        await storage.write(self.storage_key, artifact.id, artifact.to_dict())
        return artifact

    async def get(self, artifact_id: str) -> Artifact | None:
        from app.utils.json_storage import get_storage
        storage = get_storage()
        data = await storage.read(self.storage_key, artifact_id)
        if data is None:
            return None
        return Artifact(**data)

    async def delete(self, artifact_id: str) -> bool:
        from app.utils.json_storage import get_storage
        storage = get_storage()
        return await storage.delete(self.storage_key, artifact_id)

    async def list_by_session(self, session_id: str) -> list[Artifact]:
        from app.utils.json_storage import get_storage
        storage = get_storage()
        keys = await storage.list_keys(self.storage_key)
        results = []
        for key in keys:
            data = await storage.read(self.storage_key, key)
            if data and data.get("session_id") == session_id:
                results.append(Artifact(**data))
        results.sort(key=lambda a: a.updated_at, reverse=True)
        return results

    async def list_recent(self, limit: int = 20) -> list[Artifact]:
        from app.utils.json_storage import get_storage
        storage = get_storage()
        keys = await storage.list_keys(self.storage_key)
        results = []
        for key in keys:
            data = await storage.read(self.storage_key, key)
            if data:
                results.append(Artifact(**data))
        results.sort(key=lambda a: a.updated_at, reverse=True)
        return results[:limit]

    async def diff_and_update(
        self,
        artifact: Artifact,
        new_content: str,
        change_type: ArtifactChangeType,
        description: str = "",
    ) -> Artifact:
        import difflib
        original = ""
        if artifact.changes:
            last = artifact.changes[-1]
            orig_data = await self._get_file_content_at_change(artifact.path, last)
            if orig_data is not None:
                original = orig_data

        if change_type == ArtifactChangeType.DELETE:
            diff = "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    [],
                    fromfile=f"a/{artifact.path}",
                    tofile=f"b/{artifact.path}",
                    lineterm="",
                )
            )
        elif original:
            diff = "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile=f"a/{artifact.path}",
                    tofile=f"b/{artifact.path}",
                    lineterm="",
                )
            )
        else:
            diff_lines = [f"+{line}" for line in new_content.splitlines()]
            diff = f"--- /dev/null\n+++ {artifact.path}\n" + "\n".join(diff_lines)

        artifact.add_change(change_type, description, diff)
        artifact.updated_at = datetime.utcnow()
        return await self.save(artifact)

    async def _get_file_content_at_change(self, path: str, change: ArtifactChange) -> str | None:
        try:
            from pathlib import Path
            p = Path(path)
            if p.exists():
                return p.read_text(encoding="utf-8")
        except Exception:
            pass
        return None
