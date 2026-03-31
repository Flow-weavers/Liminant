from pathlib import Path
from app.services.artifact_storage import ArtifactStorage
from app.config import settings

_storage: ArtifactStorage | None = None

def get_artifact_storage() -> ArtifactStorage:
    global _storage
    if _storage is None:
        _storage = ArtifactStorage(settings.data_dir)
    return _storage
