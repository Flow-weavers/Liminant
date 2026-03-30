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


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: f"art_{uuid.uuid4().hex[:12]}")
    type: str = "file"
    path: str = ""
    summary: str = ""
    changes: list[ArtifactChange] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
