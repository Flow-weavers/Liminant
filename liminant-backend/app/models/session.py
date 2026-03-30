from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class SessionState(BaseModel):
    phase: str = "planning"
    current_step: int = 1
    total_steps: int = 1


class SessionContext(BaseModel):
    working_directory: str = "/workspace/default"
    language: str = "en-US"
    preferences: dict = Field(default_factory=lambda: {
        "detail_level": "medium",
        "output_format": "markdown",
    })


class SessionConstraints(BaseModel):
    active: bool = True
    rules: list[str] = Field(default_factory=list)
    knowledge_refs: list[str] = Field(default_factory=list)


class Session(BaseModel):
    id: str = Field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:12]}")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    state: SessionState = Field(default_factory=SessionState)
    context: SessionContext = Field(default_factory=SessionContext)
    messages: list[dict] = Field(default_factory=list)
    artifacts: list[dict] = Field(default_factory=list)
    constraints: SessionConstraints = Field(default_factory=SessionConstraints)

    def to_dict(self) -> dict:
        data = self.model_dump(mode="json")
        data["updated_at"] = self.updated_at.isoformat()
        data["created_at"] = self.created_at.isoformat()
        return data


class SessionCreate(BaseModel):
    working_directory: Optional[str] = None
    language: Optional[str] = None
