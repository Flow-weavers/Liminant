from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class KnowledgeType(str, Enum):
    RULE = "rule"
    PATTERN = "pattern"
    PREFERENCE = "preference"
    CONTEXT = "context"


class KnowledgeTriggers(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    session_types: list[str] = Field(default_factory=list)
    context_patterns: list[str] = Field(default_factory=list)


class KnowledgeMetadata(BaseModel):
    tags: list[str] = Field(default_factory=list)
    source: str = "user_defined"
    confidence: float = 0.95
    usage_count: int = 0
    pending_review: bool = False


class KnowledgeContent(BaseModel):
    title: str = ""
    body: str = ""
    examples: list[dict] = Field(default_factory=list)


class KnowledgeEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"kb_{uuid.uuid4().hex[:12]}")
    type: KnowledgeType = KnowledgeType.RULE
    content: KnowledgeContent = Field(default_factory=KnowledgeContent)
    metadata: KnowledgeMetadata = Field(default_factory=KnowledgeMetadata)
    triggers: KnowledgeTriggers = Field(default_factory=KnowledgeTriggers)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        data = self.model_dump(mode="json")
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data


class KnowledgeCreate(BaseModel):
    type: KnowledgeType = KnowledgeType.RULE
    title: str = ""
    body: str = ""
    tags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
