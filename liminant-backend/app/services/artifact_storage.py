import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any
import shutil


class ArtifactStorage:
    def __init__(self, data_dir: Path):
        self.artifacts_dir = data_dir / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, dict] = {}
        self._load_index()

    def _load_index(self) -> None:
        idx_path = self.artifacts_dir / "_index.json"
        if idx_path.exists():
            self._index = json.loads(idx_path.read_text())

    def _save_index(self) -> None:
        idx_path = self.artifacts_dir / "_index.json"
        idx_path.write_text(json.dumps(self._index, indent=2, default=str))

    def _content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    async def save(
        self,
        session_id: str,
        path: str,
        content: str,
        artifact_type: str = "file",
        summary: str = "",
    ) -> dict[str, Any]:
        rel_path = str(Path(path).as_posix()).lstrip("/")
        content_hash = self._content_hash(content)
        artifact_id = f"art_{session_id}_{content_hash}"

        artifact_dir = self.artifacts_dir / session_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        file_path = artifact_dir / f"{content_hash}.bin"
        file_path.write_text(content, encoding="utf-8")

        metadata = {
            "id": artifact_id,
            "session_id": session_id,
            "path": path,
            "rel_path": rel_path,
            "type": artifact_type,
            "summary": summary or path,
            "content_hash": content_hash,
            "size_bytes": len(content.encode()),
            "created_at": datetime.utcnow().isoformat(),
            "versions": [],
        }

        if artifact_id in self._index:
            old = self._index[artifact_id]
            metadata["versions"] = old.get("versions", [])
            metadata["versions"].append({
                "content_hash": old["content_hash"],
                "path": old["path"],
                "created_at": old["created_at"],
            })

        self._index[artifact_id] = metadata
        self._save_index()

        return metadata

    async def load(self, artifact_id: str) -> tuple[str, dict] | None:
        if artifact_id not in self._index:
            return None
        meta = self._index[artifact_id]
        file_path = self.artifacts_dir / meta["session_id"] / f"{meta['content_hash']}.bin"
        if not file_path.exists():
            return None
        return file_path.read_text(encoding="utf-8"), meta

    async def load_by_path(self, session_id: str, path: str) -> tuple[str, dict] | None:
        rel_path = str(Path(path).as_posix()).lstrip("/")
        for meta in self._index.values():
            if meta["session_id"] == session_id and meta["rel_path"] == rel_path:
                file_path = self.artifacts_dir / meta["session_id"] / f"{meta['content_hash']}.bin"
                if file_path.exists():
                    return file_path.read_text(encoding="utf-8"), meta
        return None

    async def list_session(self, session_id: str) -> list[dict]:
        return [
            {k: v for k, v in meta.items() if k != "versions"}
            for meta in self._index.values()
            if meta["session_id"] == session_id
        ]

    async def delete_session(self, session_id: str) -> None:
        artifact_dir = self.artifacts_dir / session_id
        if artifact_dir.exists():
            shutil.rmtree(artifact_dir)
        to_remove = [aid for aid, meta in self._index.items() if meta["session_id"] == session_id]
        for aid in to_remove:
            del self._index[aid]
        self._save_index()

    async def diff_versions(self, artifact_id: str) -> list[dict]:
        if artifact_id not in self._index:
            return []
        return self._index[artifact_id].get("versions", [])
